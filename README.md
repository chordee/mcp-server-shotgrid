# MCP Server for Autodesk ShotGrid REST API

This project provides an MCP (Model Context Protocol) server, implemented using [FastMCP](https://github.com/modelcontextprotocol/fastmcp), that enables Large Language Model (LLM) agents to interact programmatically with Autodesk ShotGrid via its REST API. It exposes a set of tools for querying and managing ShotGrid entities such as projects, assets, and tasks. The server supports both HTTP and `transport="stdio"` modes for integration with LLM-based workflows.

## Features

- Connects to Autodesk ShotGrid using OAuth2 authentication.
- Exposes ShotGrid REST API operations as MCP tools using FastMCP.
- Query projects, assets, and tasks.
- Retrieve detailed information about entities.
- Designed for integration with LLM-based workflows.
- Modular codebase: `main.py` provides the MCP server and tool definitions, while `shotgrid_rest.py` implements the ShotGrid API wrapper.
- Includes `test_main.py` for automated testing.

## Requirements

- Python 3.11
- [httpx](https://www.python-httpx.org/)
- [httpx-auth](https://pypi.org/project/httpx-auth/)
- [mcp.server.fastmcp](https://github.com/modelcontextprotocol/fastmcp)

## Usage

1. **Set up ShotGrid credentials**:
   - Obtain your ShotGrid host URL, client ID, and client secret.

2. **Run the server** (replace placeholders with your actual values):

   ```bash
   uv run --directory {REPO_DIR} main.py -host https://your-shotgrid-url -ci your_client_id -cs your_client_secret
   ```

   All three arguments are required. Both short (`-host`, `-ci`, `-cs`) and long (`--host`, `--client-id`, `--client-secret`) forms are supported.

   The server uses FastMCP and communicates via `transport="stdio"` only.

3. **Integrate with your LLM agent**:
   - The server exposes tools via MCP for LLMs to call.

## Available Tools

All tools are asynchronous and exposed via FastMCP.

**Available Tools:**  
Arguments in parentheses are required.

- `get_all_projects()`
- `get_all_users()`
- `get_all_projects_name_contains(name: str)`
- `get_all_sequences_in_project(project_name: str)`
- `get_all_shots_in_project(project_name: str)`
- `get_all_assets_in_project(project_name: str)`
- `get_all_assets_code_contains(code: str)`
- `get_all_tasks_in_project(project_id: int)`
- `get_all_tasks_assigned_to_user(user_id: int)`
- `get_all_tasks_assigned_to_user_in_project_name(user_id: int, project_name: str)`
- `get_all_tasks_with_shot(shot_id: int)`
- `get_all_tasks_with_asset(asset_id: int)`
- `get_project_by_name(name: str)`
- `get_asset_by_id(asset_id: int)`
- `get_user_by_id(user_id: int)`
- `get_user_by_login(login: str)`
- `get_all_notes_with_version(version_id: int)`
- `get_all_replies_with_note_id(note_id: int)`
- `get_all_versions_with_task(task_id: int)`
- `get_all_versions_in_project(project_id: int)`
- `get_all_versions_in_project_updated_in_last_n_days(project_id: int, n: int)`
- `get_entities_updated_in_last_n_days(entity_type: str, n: int)`
- `get_entities_updated_in_last_n_days_with_project(entity_type: str, project_id: int, n: int)`
- `get_entity_by_id(entity_type: str, entity_id: int)`

Some tools dynamically fetch entity fields and exclude certain keys for cleaner output. See `main.py` for full argument and return details.

## Example

```bash
uv run --directory {REPO_DIR} main.py --host https://your-shotgrid-url --client-id your_client_id --client-secret your_client_secret
```

## Notes

- Ensure your ShotGrid account has API access enabled.
- The server uses OAuth2 for authentication.
- The server is implemented using FastMCP and runs with `transport="stdio"` only.
- Command-line arguments:  
  - `-host` or `--host` (ShotGrid host URL)  
  - `-ci` or `--client-id` (OAuth2 client ID)  
  - `-cs` or `--client-secret` (OAuth2 client secret)
- Some tools use dynamic field fetching and exclude certain keys (see `remove_exclude_fields` in `main.py`).
- Extend or customize the tools in `main.py` as needed for your workflow.
- The ShotGrid REST API logic is implemented in `shotgrid_rest.py`.

## License

MIT License
