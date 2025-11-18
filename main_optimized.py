import os
import asyncio
from dotenv import load_dotenv
from openai import AzureOpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import json

load_dotenv()

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_MODEL = os.getenv("AZURE_OPENAI_MODEL")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_DEVOPS_ORG = os.getenv("AZURE_DEVOPS_ORG")
ADO_MCP_AUTH_TOKEN = os.getenv("AZURE_DEVOPS_PAT")

project_name = "your-project-name"
team_name = "your-team-name"
work_item_id = 12345
repo_name = "your-repo-name"
custom_prompt = f"List all the repositories in {project_name} project"

openai_client = AzureOpenAI(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_version="2025-04-01-preview",
    api_key=AZURE_OPENAI_API_KEY,
)

# Tool categories for progressive disclosure
TOOL_CATEGORIES = {
    "work_item": ["wit_get_work_item", "wit_create_work_item", "wit_update_work_items_batch", 
                  "wit_my_work_items", "wit_add_artifact_link", "wit_work_items_link"],
    "project": ["project_list", "team_list", "work_get_team_capacity", "work_get_iteration_capacities",
                "work_list_team_iterations", "work_update_team_capacity"],
    "repository": ["repo_list", "repo_get_by_name", "repo_create_branch", 
                   "repo_create_pull_request_thread"],
    "pull_request": ["repo_list_pull_requests", "repo_get_pull_request"],
    "pipeline": ["pipelines_list", "pipelines_run_pipeline"],
    "wiki": ["wiki_list", "wiki_list_pages", "wiki_create_or_update_page"],
    "search": ["search_code", "search_wiki"],
}

def get_tool_summary():
    """Lightweight summary of available tool categories."""
    return {
        "work_item": "Create, read, update work items, add links and comments",
        "project": "List projects, teams, manage iterations and capacity",
        "repository": "Access repositories, create branches",
        "pull_request": "List and manage pull requests, add comments",
        "pipeline": "List and run pipelines",
        "wiki": "Access and update wiki pages",
        "search": "Search code and wiki content",
    }

def search_tools_by_intent(tools_list, user_prompt):
    """
    Smart tool filtering based on user intent.
    Returns only relevant tools instead of all 77.
    """
    prompt_lower = user_prompt.lower()
    relevant_categories = set()
    
    # Intent detection keywords
    intent_map = {
        "work_item": ["work item", "task", "bug", "user story", "backlog", "assign", "comment", "triage"],
        "project": ["project", "team", "iteration", "capacity", "sprint"],
        "repository": ["repo", "repository", "branch", "code"],
        "pull_request": ["pull request", "pr", "review", "merge"],
        "pipeline": ["pipeline", "build", "deploy", "run"],
        "wiki": ["wiki", "documentation", "page"],
        "search": ["search", "find"],
    }
    
    # Detect relevant categories
    for category, keywords in intent_map.items():
        if any(keyword in prompt_lower for keyword in keywords):
            relevant_categories.add(category)
    
    # If no specific category detected, use a minimal default set
    if not relevant_categories:
        relevant_categories = {"project", "work_item"}  # Safe defaults
    
    # Filter tools by relevant categories
    relevant_tool_names = set()
    for category in relevant_categories:
        if category in TOOL_CATEGORIES:
            relevant_tool_names.update(TOOL_CATEGORIES[category])
    
    # Return only relevant tools
    filtered_tools = [t for t in tools_list if t.name in relevant_tool_names]
    
    print(f"📊 Token Optimization: Using {len(filtered_tools)} tools (filtered from {len(tools_list)})")
    print(f"   Categories: {', '.join(relevant_categories)}")
    
    return filtered_tools

async def main():
    auth_mode = "envvar" if ADO_MCP_AUTH_TOKEN else "azcli"
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@azure-devops/mcp@latest", AZURE_DEVOPS_ORG, "--authentication", auth_mode],
        env={"ADO_MCP_AUTH_TOKEN": ADO_MCP_AUTH_TOKEN} if auth_mode == "envvar" else {},
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            tools_response = await session.list_tools()
            all_tools = tools_response.tools
            print(f"Connected. Total tools available: {len(all_tools)}")
            print(f"Tool categories: {', '.join(get_tool_summary().keys())}\n")
            
            async def run_prompt(user_prompt):
                """
                Optimized prompt execution with progressive tool disclosure.
                Only loads tools relevant to the current prompt.
                """
                messages = [{"role": "user", "content": user_prompt}]
                print(f"\n🤖 Prompt: {user_prompt}\n")
                
                # OPTIMIZATION: Filter tools based on user intent
                relevant_tools = search_tools_by_intent(all_tools, user_prompt)
                
                available_tools = [
                    {
                        "type": "function", 
                        "function": {
                            "name": t.name, 
                            "description": t.description, 
                            "parameters": t.inputSchema
                        }
                    }
                    for t in relevant_tools
                ]
                
                # Calculate token savings
                total_tools_count = len(all_tools)
                used_tools_count = len(relevant_tools)
                reduction_pct = ((total_tools_count - used_tools_count) / total_tools_count) * 100
                print(f"   Token reduction: ~{reduction_pct:.1f}% (from tool definitions)\n")
                
                response = openai_client.chat.completions.create(
                    model=AZURE_OPENAI_MODEL,
                    messages=messages,
                    tools=available_tools
                )
                
                response_message = response.choices[0].message
                messages.append(response_message)
                
                if response_message.tool_calls:
                    print(f"🔧 Tool calls made: {len(response_message.tool_calls)}\n")
                    
                    for tool_call in response_message.tool_calls:
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments)
                        
                        print(f"  → Calling: {function_name}")
                        print(f"    Arguments: {json.dumps(function_args, indent=2)}")
                        
                        result = await session.call_tool(function_name, function_args)
                        
                        # OPTIMIZATION: Limit content length in messages to reduce context
                        content_str = str(result.content)
                        if len(content_str) > 10000:  # Truncate large responses
                            print(f"    ⚠️  Large response ({len(content_str)} chars), truncating for context...")
                            content_str = content_str[:10000] + "\n... [truncated for token efficiency]"
                        
                        messages.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": content_str,
                        })
                        print("    ✓ Tool executed successfully\n")
                
                final_response = openai_client.chat.completions.create(
                    model=AZURE_OPENAI_MODEL,
                    messages=messages,
                    tools=available_tools
                )
                
                final_answer = final_response.choices[0].message.content
                print("\n" + "=" * 70)
                print("📝 Response:")
                print("=" * 70)
                print(final_answer)
                print("=" * 70 + "\n")
                
                return final_answer
            
            # Example 1: List Azure DevOps Projects
            await run_prompt("Get list of all projects in my Azure DevOps organization")
            
            # Example 2: Get My Work Items
            await run_prompt(f"Get my work items for project {project_name}")
            
            # Example 3: List Teams in a Project
            await run_prompt(f"Get list of teams for project {project_name}")
            
            # Example 4: Work with Work Items
            await run_prompt(
                f"Get work item {work_item_id} and show me the fields: ID, Type, State, Title, "
                f"Assigned To, and Priority. Also get all comments and summarize them."
            )
            
            # Example 5: Get Backlog Items
            await run_prompt(
                f"Get backlogs for {project_name} project and {team_name} team, "
                f"then show me the Stories backlog"
            )
            
            # Example 6: Create a New Work Item
            await run_prompt(
                f"Create a new Task in project {project_name} with title 'Update documentation' "
                f"and description 'Need to update API documentation with latest changes'"
            )
            
            # Example 7: Update Work Item
            await run_prompt(
                f"Update work item {work_item_id}: set State to 'Active', "
                f"Priority to 2, and add a comment 'Working on this now'"
            )
            
            # Example 8: List Pull Requests
            await run_prompt(
                f"List all active pull requests for project {project_name} "
                f"and repository {repo_name}"
            )
            
            # Example 9: Work with Wiki Pages
            await run_prompt(f"Get list of wikis in project {project_name}")
            
            # Example 10: Complex Workflow - Triage Work Items
            await run_prompt(
                f"For project {project_name} and team {team_name}: "
                f"1. Get the current iteration "
                f"2. List all unassigned bugs with priority 1 or 2 "
                f"3. Show me the top 5 by creation date"
            )
            
            # Interactive Prompt
            await run_prompt(custom_prompt)

if __name__ == "__main__":
    asyncio.run(main())
