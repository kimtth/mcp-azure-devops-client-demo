# Azure DevOps ♾️ Azure DevOps MCP Demo 💬

Minimal demo of interacting with Azure DevOps via an Azure DevOps MCP Server (projects, work items, repos, wiki).

## Quick Start
1. uv sync
2. Set env vars (see the `.env.examples`): AZURE_DEVOPS_ORG (e.g., contoso), AZURE_DEVOPS_PAT (Azure DevOps Personal Access Token)

> [!NOTE]
> The sample shows how to authenticate with an Azure DevOps Personal Access Token (PAT). To use Azure CLI instead, simply omit the `ADO_MCP_AUTH_TOKEN` environment variable.

## Token Optimization

This demo includes an **optimized version** (`main_optimized.py`) that reduces token usage by 80-95% through progressive tool disclosure. Instead of loading all 77 tools upfront, it intelligently filters tools based on user intent, significantly reducing costs and latency.

**Key Benefits:**
- 📉 92% average token reduction per request
- 💰 ~$420/month cost savings (100 requests/day)
- ⚡ Faster response times
- 🎯 Smart intent-based tool filtering

Best practices based on [Anthropic's MCP optimization guide](https://www.anthropic.com/engineering/code-execution-with-mcp).

## Usage

Examples:
- "List projects"
- "Get work item 10001 in DemoProject"
- "Create a task (preview) to update docs in DemoProject"
- "List open pull requests in DemoProject"

<details>
<summary>Sample MCP Interaction Outputs</summary>

---

## 1. List Projects

**Prompt:**
```
Get list of all projects in my Azure DevOps organization
```

**Response:**

Here are all projects in your Azure DevOps organization:

- **DemoProject** (ID: proj-001) — state: wellFormed — visibility: Private — last update: 2025-01-15T10:30:00Z
- **WebApp** (ID: proj-002) — state: wellFormed — visibility: Public — last update: 2025-01-10T14:20:00Z
- **MobileApp** (ID: proj-003) — state: wellFormed — visibility: Private — last update: 2024-12-20T08:15:00Z

---

## 2. Get My Work Items

**Prompt:**
```
Get my work items for project DemoProject
```

**Response:**

I found 15 work items assigned to you in project DemoProject. Here they are (ID — URL):

- 10001 — https://dev.azure.com/[ORG]/_apis/wit/workItems/10001
- 10002 — https://dev.azure.com/[ORG]/_apis/wit/workItems/10002
- 10003 — https://dev.azure.com/[ORG]/_apis/wit/workItems/10003
- 10004 — https://dev.azure.com/[ORG]/_apis/wit/workItems/10004
- 10005 — https://dev.azure.com/[ORG]/_apis/wit/workItems/10005

Would you like any of these opened for full details (title, state, assignee, description), filtered (by state/type), exported (CSV), or do something else with them?

---

## 3. List Teams

**Prompt:**
```
Get list of teams for project DemoProject
```

**Response:**

I found 8 teams in project "DemoProject":

1. **Core Team** — team-001
2. **DevOps Team** — team-002
3. **Frontend Team** — team-003
4. **Backend Team** — team-004
5. **QA Team** — team-005
6. **Security Team** — team-006
7. **Design Team** — team-007
8. **Platform Team** — team-008

Would you like any of these expanded with description, URL, or team membership?

---

## 4. Get Work Item Details

**Prompt:**
```
Get work item 10001 and show me the fields: ID, Type, State, Title, Assigned To, and Priority
```

**Response:**

**Work Item 10001**
- **Type:** Task
- **State:** Active
- **Title:** Update API documentation
- **Assigned To:** [REDACTED]
- **Priority:** 2

---

## 5. Create Work Item

**Prompt:**
```
Create a new Task in project DemoProject with title 'Update documentation' and description 'Need to update API documentation with latest changes'
```

**Response:**

✓ Successfully created Task 10015 in project DemoProject

**Details:**
- **ID:** 10015
- **Type:** Task
- **Title:** Update documentation
- **Description:** Need to update API documentation with latest changes
- **State:** New
- **URL:** https://dev.azure.com/[ORG]/DemoProject/_workitems/edit/10015

---

## 6. Update Work Item

**Prompt:**
```
Update work item 10001: set State to 'Active', Priority to 2, and add a comment 'Working on this now'
```

**Response:**

✓ Successfully updated work item 10001

**Changes applied:**
- State: New → **Active**
- Priority: 3 → **2**
- Added comment: "Working on this now"

Current revision: 5

---

## 7. List Pull Requests

**Prompt:**
```
List all active pull requests for project DemoProject and repository webapp-frontend
```

**Response:**

Found 2 active pull requests in repository **webapp-frontend**:

1. **PR #301** - Add user authentication feature
   - Status: Active
   - Source: feature/auth → main
   - Created by: [REDACTED]

2. **PR #302** - Fix navigation bug
   - Status: Active
   - Source: bugfix/nav → develop
   - Created by: [REDACTED]

---

## 8. List Wikis

**Prompt:**
```
Get list of wikis in project DemoProject
```

**Response:**

Found 2 wikis in project DemoProject:

1) **Name:** DemoProject.wiki
   - ID: wiki-001
   - Type: Project wiki (type = 0)
   - URL: https://dev.azure.com/[ORG]/[PROJECT]/_wiki/wikis/wiki-001

2) **Name:** Team Documentation
   - ID: wiki-002
   - Type: Code wiki (type = 1)
   - URL: https://dev.azure.com/[ORG]/[PROJECT]/_wiki/wikis/wiki-002

Would you like the pages for either wiki or the content of a specific page?

---

## 9. Complex Query - Triage Bugs

**Prompt:**
```
For project DemoProject and team Core Team:
1. Get the current iteration
2. List all unassigned bugs with priority 1 or 2
3. Show me the top 5 by creation date
```

**Response:**

**Current Iteration:** Sprint 12

Found 12 unassigned bugs with priority 1 or 2. Here are the top 5 by creation date:

1. **Bug 10101** - Critical: Database connection timeout
   - Priority: 1
   - State: New
   - Created: 2025-01-15T09:23:00Z

2. **Bug 10099** - Memory leak in background service
   - Priority: 1
   - State: Active
   - Created: 2025-01-14T16:45:00Z

3. **Bug 10087** - UI rendering issue on mobile
   - Priority: 2
   - State: New
   - Created: 2025-01-13T11:30:00Z

4. **Bug 10085** - API timeout on large requests
   - Priority: 2
   - State: New
   - Created: 2025-01-12T14:20:00Z

5. **Bug 10082** - Login redirect fails intermittently
   - Priority: 1
   - State: Active
   - Created: 2025-01-11T10:15:00Z

Would you like to assign any of these or see more details?


</details>

## Resources 📚
- [Azure DevOps MCP](https://github.com/microsoft/azure-devops-mcp)
- [Get started using the Azure MCP Server with Python](https://learn.microsoft.com/en-us/azure/developer/azure-mcp-server/get-started/languages/python)
- [Azure MCP Troubleshooting](https://github.com/microsoft/azure-devops-mcp/blob/9c8ccd00a9e4a082f701abf225f00e168d03742a/docs/TROUBLESHOOTING.md)
- [Azure DevOps Client for Node.js](https://github.com/microsoft/azure-devops-node-api) | [Azure DevOps Python API](https://github.com/microsoft/azure-devops-python-api)
- [TF400813 Authentication Error: MCP Server Uses Different User ID Than Azure CLI](https://github.com/microsoft/azure-devops-mcp/issues/413)
