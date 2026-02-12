# MCP Server for Autodesk ShotGrid REST API

This project provides an MCP (Model Context Protocol) server, implemented using [FastMCP](https://github.com/modelcontextprotocol/fastmcp), that enables Large Language Model (LLM) agents to interact programmatically with Autodesk ShotGrid via its REST API. It exposes a set of tools for querying and managing ShotGrid entities such as projects, assets, tasks, users, notes, and more. The server supports `transport="stdio"` mode for integration with LLM-based workflows.

## Features

- Connects to Autodesk ShotGrid using OAuth2 authentication.
- Exposes ShotGrid REST API operations as MCP tools using FastMCP.
- Query projects, users, assets, tasks, notes, versions, bookings, and more.
- Retrieve detailed information about entities.
- Designed for integration with LLM-based workflows.
- Modular codebase: `main.py` provides the MCP server and tool definitions, while `shotgrid_rest.py` implements the ShotGrid API wrapper.

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

All tools are asynchronous and exposed via FastMCP. They return structured Python objects (List or Dict) which are automatically serialized by the MCP framework. Arguments in parentheses are required unless marked optional.

- `get_all_projects()`: List all projects.
- `get_all_users()`: List all users.
- `get_all_projects_field_contains(value: str, field: str = "name")`: List projects where a field contains a value.
- `get_sequences(project_id: int (optional), project_name: str (optional), code: str (optional), updated_in_last_n_days: int (optional), updated_date_from: [YYYY,MM,DD] (optional), updated_date_to: [YYYY,MM,DD] (optional))`: List sequences, optionally filtered by project, code, or date.
- `get_shots(project_id: int (optional), project_name: str (optional), sequence_id: int (optional), sequence_code: str (optional), shot_code: str (optional), updated_in_last_n_days: int (optional), updated_date_from: [YYYY,MM,DD] (optional), updated_date_to: [YYYY,MM,DD] (optional))`: List shots, with extensive filters.
- `get_assets(project_id: int (optional), project_name: str (optional), code: str (optional), updated_in_last_n_days: int (optional), updated_date_from: [YYYY,MM,DD] (optional), updated_date_to: [YYYY,MM,DD] (optional))`: List assets, with optional filters.
- `get_tasks(entity_type: str (optional), entity_id: int (optional), project_id: int (optional), project_name: str (optional), user_id: int (optional), task_name: str (optional), updated_in_last_n_days: int (optional), updated_date_from: [YYYY,MM,DD] (optional), updated_date_to: [YYYY,MM,DD] (optional))`: List tasks, with optional filters.
- `get_users_name_or_login_contains(name: str (optional), login: str (optional))`: List users whose name or login contains a substring.
- `get_notes(shot_id: int (optional), asset_id: int (optional), user_id: int (optional), task_id: int (optional), version_id: int (optional), project_id: int (optional), project_name: str (optional), task_name: str (optional), asset_code: str (optional), version_name: str (optional), updated_in_last_n_days: int (optional), updated_date_from: [YYYY,MM,DD] (optional), updated_date_to: [YYYY,MM,DD] (optional))`: List notes with comprehensive filtering options.
- `get_all_replies_with_note_id(note_id: int)`: List replies associated with a note.
- `get_versions(project_id: int (optional), project_name: str (optional), task_id: int (optional), task_name: str (optional), user_id: int (optional), updated_in_last_n_days: int (optional), updated_date_from: [YYYY,MM,DD] (optional), updated_date_to: [YYYY,MM,DD] (optional))`: List versions with optional filters.
- `get_bookings(user_id: int (optional), project_id: int (optional), start_date_from: [YYYY,MM,DD] (optional), start_date_to: [YYYY,MM,DD] (optional), end_date_from: [YYYY,MM,DD] (optional), end_date_to: [YYYY,MM,DD] (optional), vacation: bool (optional))`: List bookings, with optional filters.
- `get_entities_updated_in_last_n_days(entity_type: str, n: int, project_id: int (optional))`: List entities of a type updated in the last n days.
- `get_entity_by_id(entity_type: str, entity_id: int)`: Get details for an entity by type and ID.

## Error Handling

The server includes a robust error handling wrapper that captures ShotGrid API errors and internal exceptions, returning them as structured JSON objects with `error` and `message` fields.

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
