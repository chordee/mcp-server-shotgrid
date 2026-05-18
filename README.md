# MCP Server for Autodesk ShotGrid REST API

This project provides an MCP (Model Context Protocol) server, implemented using [FastMCP](https://github.com/modelcontextprotocol/fastmcp), that enables Large Language Model (LLM) agents to interact programmatically with Autodesk ShotGrid via its REST API. It exposes a set of tools for querying and managing ShotGrid entities such as projects, assets, tasks, users, notes, and more. The server supports `transport="stdio"` mode for integration with LLM-based workflows.

## Features

- Connects to Autodesk ShotGrid using OAuth2 authentication.
- Exposes ShotGrid REST API operations as MCP tools using FastMCP.
- Query projects, users, assets, tasks, notes, versions, bookings, and more.
- Retrieve detailed information about entities.
- Designed for integration with LLM-based workflows.
- Modular codebase: `main.py` provides the MCP server and core tool definitions; `booking_tools.py` handles all Booking CRUD operations; `note_tools.py` handles Note / Reply CRUD plus attachment reads; `shotgrid_rest.py` implements the ShotGrid API wrapper.

## Requirements

- Python 3.11
- [httpx](https://www.python-httpx.org/)
- [httpx-auth](https://pypi.org/project/httpx-auth/)
- [mcp.server.fastmcp](https://github.com/modelcontextprotocol/fastmcp)

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/chordee/mcp-server-shotgrid.git
   ```

2. **Install [uv](https://docs.astral.sh/uv/)** if you don't have it. `uv` manages Python 3.11 and the dependencies declared in `pyproject.toml` automatically; no manual `venv` step is needed.

3. **Configure credentials.** Use environment variables (recommended) or CLI arguments. See [Usage](#usage).

4. **Register the server with your MCP client.** Example for Claude Code (`~/.claude.json` or a project-local `.mcp.json`):

   ```json
   {
     "mcpServers": {
       "shotgrid": {
         "command": "uv",
         "args": ["run", "--directory", "D:\\path\\to\\mcp-server-shotgrid", "main.py"],
         "env": {
           "SHOTGRID_HOST": "https://your-shotgrid-url",
           "SHOTGRID_CLIENT_ID": "your_client_id",
           "SHOTGRID_CLIENT_SECRET": "your_client_secret"
         }
       }
     }
   }
   ```

## Usage

Credentials can come from either **environment variables (recommended)** or CLI arguments. Environment variables take precedence; if both are missing for any of the three values, the server exits with an error.

### Option A — Environment variables (recommended)

| Variable | Description |
|---|---|
| `SHOTGRID_HOST` | ShotGrid host URL, e.g. `https://your-shotgrid-url` |
| `SHOTGRID_CLIENT_ID` | OAuth2 client ID |
| `SHOTGRID_CLIENT_SECRET` | OAuth2 client secret |

**Windows (PowerShell):**

```powershell
$env:SHOTGRID_HOST = "https://your-shotgrid-url"
$env:SHOTGRID_CLIENT_ID = "your_client_id"
$env:SHOTGRID_CLIENT_SECRET = "your_client_secret"
uv run --directory C:\path\to\mcp-server-shotgrid main.py
```

**macOS / Linux (bash / zsh):**

```bash
export SHOTGRID_HOST="https://your-shotgrid-url"
export SHOTGRID_CLIENT_ID="your_client_id"
export SHOTGRID_CLIENT_SECRET="your_client_secret"
uv run --directory /path/to/mcp-server-shotgrid main.py
```

### Option B — CLI arguments

```bash
uv run --directory {REPO_DIR} main.py --host https://your-shotgrid-url --client-id your_client_id --client-secret your_client_secret
```

Both short (`-host`, `-ci`, `-cs`) and long (`--host`, `--client-id`, `--client-secret`) forms are supported.

### Security note

Prefer environment variables over CLI arguments. Arguments passed on the command line are visible in process listings (`ps`, Task Manager), shell history, and many supervisor/IDE configuration files. Environment variables can reduce accidental exposure, but they are still secrets — store them in protected config files (for example, `.mcp.json` / `~/.claude.json`), use strict file permissions, and never commit secrets to version control.

The server uses FastMCP and communicates via `transport="stdio"` only. Tools exposed by MCP are available for LLM agents to call.

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
- `get_notes(shot_id: int (optional), asset_id: int (optional), user_id: int (optional), task_id: int (optional), version_id: int (optional), project_id: int (optional), project_name: str (optional), task_name: str (optional), asset_code: str (optional), version_name: str (optional), updated_in_last_n_days: int (optional), updated_date_from: [YYYY,MM,DD] (optional), updated_date_to: [YYYY,MM,DD] (optional), limit: int (optional), page: int (optional))`: List notes with comprehensive filtering options. Supports pagination via `limit` / `page` so large projects aren't silently truncated to ShotGrid's default page.
- `create_note(content: str, project_id: int, subject: str (optional), link_shot_ids: [int] (optional), link_asset_ids: [int] (optional), link_task_ids: [int] (optional), link_version_ids: [int] (optional), task_ids: [int] (optional), addressing_to_user_ids: [int] (optional), addressing_cc_user_ids: [int] (optional), user_id: int (optional), sg_status_list: str (optional))`: Create a new Note. `note_links` is built from the four `link_*` lists. `user_id` defaults to the API user when omitted.
- `update_note(note_id: int, content: str (optional), subject: str (optional), sg_status_list: str (optional), link_shot_ids: [int] (optional), link_asset_ids: [int] (optional), link_task_ids: [int] (optional), link_version_ids: [int] (optional), task_ids: [int] (optional), addressing_to_user_ids: [int] (optional), addressing_cc_user_ids: [int] (optional))`: Update an existing Note. Multi-entity list parameters REPLACE existing values when supplied (pass `[]` to clear). `project` and `user` cannot be changed via update.
- `delete_note(note_id: int)`: Delete a Note by ID.
- `get_replies(note_id: int, limit: int (optional), page: int (optional))`: List replies under a Note, returning full reply fields (`content`, `user`, `entity`, timestamps, `attachments`). Supports pagination via `limit` / `page`. Replaces the previous `get_all_replies_with_note_id`, which only returned ids.
- `create_reply(content: str, note_id: int, user_id: int (optional))`: Post a Reply under a Note. `user_id` defaults to the API user.
- `update_reply(reply_id: int, content: str)`: Update a Reply's content.
- `delete_reply(reply_id: int)`: Delete a Reply by ID.
- `get_note_attachments(note_id: int)`: List attachment references on a Note (lightweight `[{id, type, name}]`).
- `get_attachment_info(attachment_id: int)`: Fetch full Attachment metadata (`this_file` URL, `image` thumbnail, display name, content type, size).
- `get_versions(project_id: int (optional), project_name: str (optional), task_id: int (optional), task_name: str (optional), user_id: int (optional), updated_in_last_n_days: int (optional), updated_date_from: [YYYY,MM,DD] (optional), updated_date_to: [YYYY,MM,DD] (optional))`: List versions with optional filters.
- `get_bookings(user_ids: [int] (optional), project_ids: [int] (optional), range_from: [YYYY,MM,DD] (optional), range_to: [YYYY,MM,DD] (optional), vacation: bool (optional), exclude_vacation: bool (optional), sg_status_list: "cfrm"|"pndng" (optional), sort_field: "start_date"|"end_date"|"updated_at" (default "start_date"), sort_order: "asc"|"desc" (default "asc"), limit: int (optional), page: int (optional))`: List bookings whose date interval overlaps `[range_from, range_to]`. Supports multi-user and multi-project queries via the `in` relation. **Breaking change in v0.2.0**: `user_id`/`project_id` replaced by list-valued `user_ids`/`project_ids`; the four `start_date_from/to` / `end_date_from/to` parameters were replaced by `range_from`/`range_to` with inclusive overlap semantics.
- `create_booking(user_id: int, project_id: int, start_date: [YYYY,MM,DD], end_date: [YYYY,MM,DD], vacation: bool (optional), note: str (optional), percent_allocation: float (optional), sg_status_list: "cfrm"|"pndng" (optional))`: Create a new booking.
- `update_booking(booking_id: int, start_date: [YYYY,MM,DD] (optional), end_date: [YYYY,MM,DD] (optional), vacation: bool (optional), note: str (optional), percent_allocation: float (optional), sg_status_list: "cfrm"|"pndng" (optional))`: Update an existing booking. Note: `user` and `project` cannot be changed via update — delete and recreate the booking if these need to change.
- `delete_booking(booking_id: int)`: Delete a booking by ID.
- `get_entities_updated_in_last_n_days(entity_type: str, n: int, project_id: int (optional))`: List entities of a type updated in the last n days.
- `get_entity_by_id(entity_type: str, entity_id: int)`: Get details for an entity by type and ID.

## Error Handling

The server includes a robust error handling wrapper that captures ShotGrid API errors and internal exceptions, returning them as structured JSON objects with `error` and `message` fields.

## Notes

- Ensure your ShotGrid account has API access enabled.
- The server uses OAuth2 for authentication.
- The server is implemented using FastMCP and runs with `transport="stdio"` only.
- Credentials can be provided via environment variables (`SHOTGRID_HOST`, `SHOTGRID_CLIENT_ID`, `SHOTGRID_CLIENT_SECRET`) or CLI arguments (`-host` / `--host`, `-ci` / `--client-id`, `-cs` / `--client-secret`). Env vars take precedence.
- Some tools use dynamic field fetching and exclude certain keys (see `remove_exclude_fields` in `main.py`).
- Extend or customize the tools in `main.py` as needed for your workflow.
- The ShotGrid REST API logic is implemented in `shotgrid_rest.py`.

## License

MIT License
