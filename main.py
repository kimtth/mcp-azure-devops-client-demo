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

async def main():
    # The sample demonstarates how to use Azure DevOps Personal Access Token (PAT) for authentication.
    # You can also authenticate using Azure CLI by omitting the ADO_MCP_AUTH_TOKEN environment variable.
    # `npx` can call the MCP package directly without installing it.
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
            tools_list = tools_response.tools
            print(f"Connected. Tools: {len(tools_list)}")
            
            available_tools = [
                {"type": "function", "function": {"name": t.name, "description": t.description, "parameters": t.inputSchema}}
                for t in tools_list
            ]
            
            async def run_prompt(user_prompt):
                messages = [{"role": "user", "content": user_prompt}]
                print(f"\n🤖 Prompt: {user_prompt}\n")
                
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
                        
                        messages.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": result.content,
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
