# MCP Server for Autodesk ShotGrid REST API

This project provides an MCP (Model Context Protocol) server that enables Large Language Model (LLM) agents to interact programmatically with Autodesk ShotGrid via its REST API. It exposes a set of tools for querying and managing ShotGrid entities such as projects, assets, and tasks.

## Features

- Connects to Autodesk ShotGrid using OAuth2 authentication.
- Exposes ShotGrid REST API operations as MCP tools.
- Query projects, assets, and tasks.
- Retrieve detailed information about entities.
- Designed for integration with LLM-based workflows.

## Requirements

- Python 3.8+
- [httpx](https://www.python-httpx.org/)
- [httpx-auth](https://pypi.org/project/httpx-auth/)
- [mcp.server.fastmcp](https://github.com/modelcontextprotocol/fastmcp)

Install dependencies:
```bash
pip install -r requirements.txt
```
*(Or install individually as needed.)*

## Usage

1. **Set up ShotGrid credentials**:
   - Obtain your ShotGrid host URL, client ID, and client secret.

2. **Run the server**:
   ```bash
   python main.py --host <SHOTGRID_HOST> --client-id <CLIENT_ID> --client-secret <CLIENT_SECRET>
   ```

3. **Integrate with your LLM agent**:
   - The server exposes tools via MCP for LLMs to call.

## Available Tools

- `get_all_projects`: List all projects (name, code, ID).
- `get_all_assets_in_project(project_name)`: List all assets in a project.
- `get_project_by_name(name)`: Get details for a project by name.
- `get_asset_by_id(asset_id)`: Get detailed info for an asset by ID.
- `list_asset_tasks_with_assignees(asset_id)`: List all tasks for an asset, including assignees.

## Example

```bash
python main.py --host https://your-shotgrid-url --client-id your_client_id --client-secret your_client_secret
```

## Notes

- Ensure your ShotGrid account has API access enabled.
- The server uses OAuth2 for authentication.
- Extend or customize the tools in `main.py` as needed for your workflow.

## License

MIT License
