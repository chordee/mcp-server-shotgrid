# MCP Server for Autodesk ShotGrid REST API

This project provides an MCP (Model Context Protocol) server, implemented using [FastMCP](https://github.com/modelcontextprotocol/fastmcp), that enables Large Language Model (LLM) agents to interact programmatically with Autodesk ShotGrid via its REST API. It exposes a set of tools for querying and managing ShotGrid entities such as projects, assets, and tasks. The server runs with `transport="stdio"` for integration with LLM-based workflows.

## Features

- Connects to Autodesk ShotGrid using OAuth2 authentication.
- Exposes ShotGrid REST API operations as MCP tools using FastMCP.
- Query projects, assets, and tasks.
- Retrieve detailed information about entities.
- Designed for integration with LLM-based workflows.

## Requirements

- Python 3.11
- [httpx](https://www.python-httpx.org/)
- [httpx-auth](https://pypi.org/project/httpx-auth/)
- [mcp.server.fastmcp](https://github.com/modelcontextprotocol/fastmcp)

## Usage

1. **Set up ShotGrid credentials**:
   - Obtain your ShotGrid host URL, client ID, and client secret.

2. **Run the server**:
   ```bash
   uv run --directory {REPO_DIR} main.py --host <SHOTGRID_HOST> --client-id <CLIENT_ID> --client-secret <CLIENT_SECRET>
   ```
   The server will start using FastMCP and communicate via `transport="stdio"`.

3. **Integrate with your LLM agent**:
   - The server exposes tools via MCP for LLMs to call.

## Available Tools

All tools are asynchronous and exposed via FastMCP.

**Available Tools:**

- `get_all_projects() -> List[dict]`  
  Retrieve all projects. Returns a list of dicts with at least `name`, `code`, and `id`.

- `get_all_users() -> List[dict]`  
  Retrieve all users. Returns a list of dicts with at least the `login` field.

- `get_all_sequences_in_project(project_name: str) -> List[dict]`  
  Retrieve all sequences within a specified project from ShotGrid. Returns a list of dicts with at least the sequence's `name`, `code`, `sg_status_list`, and associated `project`.

- `get_all_shots_in_project(project_name: str) -> List[dict]`  
  Retrieve all shots within a specified project from ShotGrid. Returns a list of dicts with at least the shot's `name`, `code`, `sg_status_list`, and associated `sg_sequence`.

- `get_all_assets_in_project(project_name: str) -> List[dict]`  
  List all assets in a project. Returns dicts with `name`, `code`, `sg_status_list`, `updated_at`, and `sg_asset_type`.

- `get_all_tasks_assigned_to_user(user_id: int) -> List[dict]`  
  List all tasks assigned to a user. Returns dicts with `content`, `sg_status_list`, `id`, `updated_at`, and `project`.

- `get_project_by_name(name: str) -> List[dict]`  
  Get details for a project by name. Returns a list of dicts with all available fields.

- `get_project_by_id(project_id: int) -> List[dict]`  
  Get details for a project by ID. Returns a list of dicts with all available fields.

- `get_asset_by_id(asset_id: int) -> List[dict]`  
  Get detailed info for an asset by ID. Returns a list of dicts with all available fields.

- `get_user_by_id(user_id: int) -> List[dict]`  
  Get detailed info for a user by ID. Returns a list of dicts with all available fields.

- `get_user_by_login(login: str) -> List[dict]`  
  Get detailed info for a user by login. Returns a list of dicts with all available fields.

- `get_shot_by_id(shot_id: int) -> List[dict]`  
  Get detailed info for a shot by ID. Returns a list of dicts with all available fields.

- `get_sequence_by_id(sequence_id: int) -> List[dict]`  
  Get detailed info for a sequence by ID. Returns a list of dicts with all available fields.

- `get_task_by_id(task_id: int) -> List[dict]`  
  Get detailed info for a task by ID. Returns a list of dicts with all available fields.

- `get_tasks_with_asset_id(asset_id: int) -> List[dict]`  
  List all tasks for a given asset ID.

- `get_note_by_id(note_id: int) -> List[dict]`  
  Get detailed information about a note by its ID on ShotGrid. Returns a list of dicts with all available fields.

- `get_version_by_id(version_id: int) -> List[dict]`  
  Get detailed information about a version by its ID on ShotGrid. Returns a list of dicts with all available fields.

- `get_all_versions_with_task(task_id: int) -> List[dict]`  
  Retrieve all version entities in ShotGrid that are linked to a specific task. Returns a list of dicts with fields such as `user`, `updated_at`, `code`, `sg_path_to_movie`, `sg_path_to_frames`, and `description`.

## Example

```bash
uv run --directory {REPO_DIR} main.py --host https://your-shotgrid-url --client-id your_client_id --client-secret your_client_secret
```

## Notes

- Ensure your ShotGrid account has API access enabled.
- The server uses OAuth2 for authentication.
- The server is implemented using FastMCP and runs with `transport="stdio"` by default.
- Command-line arguments:  
  - `--host` (ShotGrid host URL)  
  - `--client-id` (OAuth2 client ID)  
  - `--client-secret` (OAuth2 client secret)
- Extend or customize the tools in `main.py` as needed for your workflow.

## License

MIT License
