import argparse
import os
import httpx
from mcp.server.fastmcp import FastMCP
from typing import List, Dict, Optional, Any, Union

from shotgrid_rest import ShotGridRest
from shotgrid_options import GENERAL_FIELDS, EXCLUDE_KEYS, ALL_ENTITY_TYPES
from booking_tools import register_booking_tools
from note_tools import register_note_tools

SG = ShotGridRest()

# Initialize FastMCP server
mcp = FastMCP("mcp-server-shotgrid")


def remove_exclude_fields(data: Dict) -> Dict:
    """
    Remove excluded and pipeline-specific fields from the entity attributes.
    """
    attributes = data.get("attributes", {})
    if not attributes:
        return data
        
    # Remove explicitly excluded keys
    for exclude_key in EXCLUDE_KEYS:
        attributes.pop(exclude_key, None)
        
    # Remove step-specific fields (e.g., step_123)
    keys_to_remove = [k for k in attributes.keys() if k.startswith("step_")]
    for k in keys_to_remove:
        attributes.pop(k, None)
        
    return data


async def handle_request_errors(coro):
    """
    Wrapper to handle ShotGrid API errors gracefully.
    """
    try:
        return await coro
    except httpx.HTTPStatusError as e:
        return {"error": f"ShotGrid API Error: {e.response.status_code}", "message": e.response.text}
    except Exception as e:
        return {"error": "Internal Server Error", "message": str(e)}


@mcp.tool()
async def get_all_projects() -> Union[List[Dict], Dict]:
    """
    Retrieve all projects from ShotGrid.

    Returns:
        List[dict]: A list of dictionaries, each representing a project.
            Each dictionary includes at least the following fields:
                - name: The name of the project.
                - code: The project code.
                - id: The unique identifier of the project.
                - updated_at: The timestamp of the last update to the project.
    """
    fields = ["name", "code", "id", "updated_at"]
    params = {"fields": ",".join(fields)}
    
    async def _call():
        response = await SG.get_request("/entity/projects", params=params)
        return response.get("data", [])
        
    return await handle_request_errors(_call())


@mcp.tool()
async def get_all_users() -> Union[List[Dict], Dict]:
    """
    Retrieve all users from ShotGrid.

    Returns:
        List[dict]: A list of dictionaries, each representing a user.
            Each dictionary includes at least the following fields:
                - login: The user's login name.
                - name: The user's full name.
    """
    fields = ["login", "name"]
    params = {"fields": ",".join(fields)}
    
    async def _call():
        response = await SG.get_request("/entity/HumanUsers", params=params)
        return response.get("data", [])
        
    return await handle_request_errors(_call())


@mcp.tool()
async def get_all_projects_field_contains(
    value: str,
    field: str = "name",
) -> Union[List[Dict], Dict]:
    """
    Retrieve all projects from ShotGrid that contain a specific value in the name or code field.

    Args:
        value (str): The value to search for in the specified field.
        field (str, optional): The field to search in ("name" or "code"). Defaults to "name".

    Returns:
        List[dict]: A list of project dictionaries, each with fields:
            - name
            - code
            - updated_at
    """
    if field not in {"name", "code"}:
        return {"error": "Field must be 'name' or 'code'."}
        
    filters = [[field, "contains", value]]
    fields = ["name", "code", "updated_at"]
    
    async def _call():
        resp = await SG.post_request(
            "/entity/projects/_search", json={"filters": filters, "fields": fields}
        )
        return resp.get("data", [])
        
    return await handle_request_errors(_call())


@mcp.tool()
async def get_sequences(
    project_id: Optional[int] = None,
    project_name: Optional[str] = None,
    code: Optional[str] = None,
    updated_in_last_n_days: Optional[int] = None,
    updated_date_from: Optional[List[int]] = None,
    updated_date_to: Optional[List[int]] = None,
) -> Union[List[Dict], Dict]:
    """
    Retrieve all sequences from ShotGrid, filtered by project, code substring, or update date.

    Args:
        project_id (int, optional): The ID of the project to filter sequences.
        project_name (str, optional): Filter sequences where the project name contains this value.
        code (str, optional): The substring to search for in sequence codes.
        updated_in_last_n_days (int, optional): Only include sequences updated in the last n days.
        updated_date_from (List[int], optional): Only include sequences updated after this date [YYYY, MM, DD].
        updated_date_to (List[int], optional): Only include sequences updated before this date [YYYY, MM, DD].

    Returns:
        List[dict]: A list of dictionaries, each containing details for a sequence.
    """
    filters = []
    if project_id is not None:
        filters.append(["project.Project.id", "is", project_id])
    if project_name:
        filters.append(["project.Project.name", "contains", project_name])
    if code:
        filters.append(["code", "contains", code])
    if updated_in_last_n_days is not None:
        filters.append(["updated_at", "in_last", [updated_in_last_n_days, "DAY"]])
    if updated_date_from:
        filters.append(
            [
                "updated_at",
                "greater_than",
                f"{updated_date_from[0]:04}-{updated_date_from[1]:02}-{updated_date_from[2]:02}",
            ]
        )
    if updated_date_to:
        filters.append(
            [
                "updated_at",
                "less_than",
                f"{updated_date_to[0]:04}-{updated_date_to[1]:02}-{updated_date_to[2]:02}",
            ]
        )
    fields = ["name", "code", "sg_status_list", "project", "updated_at"]
    
    async def _call():
        resp = await SG.post_request(
            "/entity/sequences/_search", json={"filters": filters, "fields": fields}
        )
        return resp.get("data", [])
        
    return await handle_request_errors(_call())


@mcp.tool()
async def get_shots(
    project_id: Optional[int] = None,
    project_name: Optional[str] = None,
    sequence_id: Optional[int] = None,
    sequence_code: Optional[str] = None,
    shot_code: Optional[str] = None,
    updated_in_last_n_days: Optional[int] = None,
    updated_date_from: Optional[List[int]] = None,
    updated_date_to: Optional[List[int]] = None,
) -> Union[List[Dict], Dict]:
    """
    Retrieve shots from ShotGrid with various filters.

    Args:
        project_id (int, optional): The ID of the project to filter shots.
        project_name (str, optional): Filter shots where the project name contains this value.
        sequence_id (int, optional): The ID of the sequence to filter shots.
        sequence_code (str, optional): Filter shots where the sequence code contains this value.
        shot_code (str, optional): The substring to search for in shot codes.
        updated_in_last_n_days (int, optional): Only include shots updated in the last n days.
        updated_date_from (List[int], optional): Only include shots updated after this date [YYYY, MM, DD].
        updated_date_to (List[int], optional): Only include shots updated before this date [YYYY, MM, DD].

    Returns:
        List[dict]: A list of shot dictionaries.
    """
    filters = []
    if project_id is not None:
        filters.append(["project.Project.id", "is", project_id])
    if project_name:
        filters.append(["project.Project.name", "contains", project_name])
    if sequence_id is not None:
        filters.append(["sg_sequence.Sequence.id", "is", sequence_id])
    if sequence_code:
        filters.append(["sg_sequence.Sequence.code", "contains", sequence_code])
    if shot_code:
        filters.append(["code", "contains", shot_code])
    if updated_in_last_n_days is not None:
        filters.append(["updated_at", "in_last", [updated_in_last_n_days, "DAY"]])
    if updated_date_from:
        filters.append(
            [
                "updated_at",
                "greater_than",
                f"{updated_date_from[0]:04}-{updated_date_from[1]:02}-{updated_date_from[2]:02}",
            ]
        )
    if updated_date_to:
        filters.append(
            [
                "updated_at",
                "less_than",
                f"{updated_date_to[0]:04}-{updated_date_to[1]:02}-{updated_date_to[2]:02}",
            ]
        )
    fields = ["code", "sg_status_list", "sg_sequence", "updated_at", "project"]

    async def _call():
        resp = await SG.post_request(
            "/entity/shots/_search", json={"filters": filters, "fields": fields}
        )
        return resp.get("data", [])
        
    return await handle_request_errors(_call())


@mcp.tool()
async def get_assets(
    project_id: Optional[int] = None,
    project_name: Optional[str] = None,
    code: Optional[str] = None,
    updated_in_last_n_days: Optional[int] = None,
    updated_date_from: Optional[List[int]] = None,
    updated_date_to: Optional[List[int]] = None,
) -> Union[List[Dict], Dict]:
    """
    Retrieve assets from ShotGrid with various filters.

    Args:
        project_id (int, optional): Only include assets for this project ID.
        project_name (str, optional): Filter assets where the project name contains this value.
        code (str, optional): The substring to search for in asset codes.
        updated_in_last_n_days (int, optional): Only include assets updated in the last n days.
        updated_date_from (List[int], optional): Only include assets updated after this date [YYYY, MM, DD].
        updated_date_to (List[int], optional): Only include assets updated before this date [YYYY, MM, DD].

    Returns:
        List[dict]: A list of asset dictionaries.
    """
    filters = []
    if project_id is not None:
        filters.append(["project.Project.id", "is", project_id])
    if project_name:
        filters.append(["project.Project.name", "contains", project_name])
    if code:
        filters.append(["code", "contains", code])
    if updated_in_last_n_days is not None:
        filters.append(["updated_at", "in_last", [updated_in_last_n_days, "DAY"]])
    if updated_date_from:
        filters.append(
            [
                "updated_at",
                "greater_than",
                f"{updated_date_from[0]:04}-{updated_date_from[1]:02}-{updated_date_from[2]:02}",
            ]
        )
    if updated_date_to:
        filters.append(
            [
                "updated_at",
                "less_than",
                f"{updated_date_to[0]:04}-{updated_date_to[1]:02}-{updated_date_to[2]:02}",
            ]
        )
    fields = ["name", "code", "sg_status_list", "updated_at", "sg_asset_type", "project"]

    async def _call():
        resp = await SG.post_request(
            "/entity/assets/_search", json={"filters": filters, "fields": fields}
        )
        return resp.get("data", [])
        
    return await handle_request_errors(_call())


@mcp.tool()
async def get_tasks(
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    project_id: Optional[int] = None,
    project_name: Optional[str] = None,
    user_id: Optional[int] = None,
    task_name: Optional[str] = None,
    updated_in_last_n_days: Optional[int] = None,
    updated_date_from: Optional[List[int]] = None,
    updated_date_to: Optional[List[int]] = None,
) -> Union[List[Dict], Dict]:
    """
    Retrieve tasks from ShotGrid with various filters.

    Args:
        entity_type (str, optional): The type of entity ("Shot" or "Asset").
        entity_id (int, optional): The unique ID of the entity whose tasks should be retrieved.
        project_id (int, optional): The unique ID of the project to filter tasks.
        project_name (str, optional): Filter tasks where the project name contains this value.
        user_id (int, optional): The unique ID of the user to filter assigned tasks.
        task_name (str, optional): Filter tasks where the content contains this value.
        updated_in_last_n_days (int, optional): Only include tasks updated in the last n days.
        updated_date_from (List[int], optional): Only include tasks updated after this date [YYYY, MM, DD].
        updated_date_to (List[int], optional): Only include tasks updated before this date [YYYY, MM, DD].

    Returns:
        List[dict]: A list of task dictionaries.
    """
    filters = []
    if entity_type and entity_id:
        if entity_type not in {"Shot", "Asset"}:
            return {"error": "entity_type must be 'Shot' or 'Asset'."}
        filters.append(["entity", "is", {"type": entity_type, "id": entity_id}])
    if project_id is not None:
        filters.append(["project.Project.id", "is", project_id])
    if project_name:
        filters.append(["project.Project.name", "contains", project_name])
    if task_name:
        filters.append(["content", "contains", task_name])
    if user_id is not None:
        filters.append(["task_assignees", "is", {"type": "HumanUser", "id": user_id}])
    if updated_in_last_n_days is not None:
        filters.append(["updated_at", "in_last", [updated_in_last_n_days, "DAY"]])
    if updated_date_from:
        filters.append(
            [
                "updated_at",
                "greater_than",
                f"{updated_date_from[0]:04}-{updated_date_from[1]:02}-{updated_date_from[2]:02}",
            ]
        )
    if updated_date_to:
        filters.append(
            [
                "updated_at",
                "less_than",
                f"{updated_date_to[0]:04}-{updated_date_to[1]:02}-{updated_date_to[2]:02}",
            ]
        )
    fields = [
        "content", "sg_status_list", "id", "updated_at", "project",
        "task_assignees", "cached_display_name", "step"
    ]
    
    async def _call():
        resp = await SG.post_request(
            "/entity/tasks/_search", json={"filters": filters, "fields": fields}
        )
        return resp.get("data", [])
        
    return await handle_request_errors(_call())


@mcp.tool()
async def get_users_name_or_login_contains(
    name: Optional[str] = None, login: Optional[str] = None
) -> Union[List[Dict], Dict]:
    """
    Get detailed information about users whose names or logins contain a specific substring.

    Args:
        name (str, optional): The substring to search for in user names.
        login (str, optional): The substring to search for in user logins.

    Returns:
        List[dict]: A list of user detail dictionaries.
    """
    filters = []
    if name:
        filters.append(["name", "contains", name])
    if login:
        filters.append(["login", "contains", login])
    if not filters:
        return {"error": "At least one of 'name' or 'login' must be provided."}
        
    fields = ["login", "name"]
    
    async def _call():
        response = await SG.post_request(
            "/entity/HumanUsers/_search", json={"filters": filters, "fields": fields}
        )
        data = response.get("data", [])
        return [remove_exclude_fields(d) for d in data] if data else []
        
    return await handle_request_errors(_call())


@mcp.tool()
async def get_versions(
    project_id: Optional[int] = None,
    project_name: Optional[str] = None,
    task_id: Optional[int] = None,
    task_name: Optional[str] = None,
    user_id: Optional[int] = None,
    updated_in_last_n_days: Optional[int] = None,
    updated_date_from: Optional[List[int]] = None,
    updated_date_to: Optional[List[int]] = None,
) -> Union[List[Dict], Dict]:
    """
    Retrieve versions from ShotGrid with various filters.

    Args:
        project_id (int, optional): The ID of the project to filter versions.
        project_name (str, optional): Filter versions where the project name contains this value.
        task_id (int, optional): The ID of the task to filter versions.
        task_name (str, optional): Filter versions where the task content contains this value.
        user_id (int, optional): The ID of the user to filter versions.
        updated_in_last_n_days (int, optional): Only include versions updated in the last n days.
        updated_date_from (List[int], optional): Only include versions updated after this date [YYYY, MM, DD].
        updated_date_to (List[int], optional): Only include versions updated before this date [YYYY, MM, DD].

    Returns:
        List[dict]: A list of version dictionaries.
    """
    filters = []
    if project_id is not None:
        filters.append(["project.Project.id", "is", project_id])
    if project_name:
        filters.append(["project.Project.name", "contains", project_name])
    if task_id is not None:
        filters.append(["sg_task.Task.id", "is", task_id])
    if task_name:
        filters.append(["sg_task.Task.content", "contains", task_name])
    if user_id is not None:
        filters.append(["user.HumanUser.id", "is", user_id])
    if updated_in_last_n_days is not None:
        filters.append(["updated_at", "in_last", [updated_in_last_n_days, "DAY"]])
    if updated_date_from:
        filters.append(
            [
                "updated_at",
                "greater_than",
                f"{updated_date_from[0]:04}-{updated_date_from[1]:02}-{updated_date_from[2]:02}",
            ]
        )
    if updated_date_to:
        filters.append(
            [
                "updated_at",
                "less_than",
                f"{updated_date_to[0]:04}-{updated_date_to[1]:02}-{updated_date_to[2]:02}",
            ]
        )
        
    fields = [
        "user", "updated_at", "code", "sg_path_to_movie",
        "sg_path_to_frames", "description", "sg_status_list"
    ]
    
    async def _call():
        resp = await SG.post_request(
            "/entity/versions/_search", json={"filters": filters, "fields": fields}
        )
        return resp.get("data", [])
        
    return await handle_request_errors(_call())


@mcp.tool()
async def get_entities_updated_in_last_n_days(
    entity_type: ALL_ENTITY_TYPES,
    n: int,
    project_id: Optional[int] = None,
) -> Union[List[Dict], Dict]:
    """Retrieve entities of a specified type updated within the last n days."""
    filters = [["updated_at", "in_last", [n, "DAY"]]]
    if project_id is not None and entity_type not in {"projects", "HumanUsers"}:
        filters.append(["project.Project.id", "is", project_id])
        
    fields = GENERAL_FIELDS
    
    async def _call():
        resp = await SG.post_request(
            f"/entity/{entity_type}/_search", json={"filters": filters, "fields": fields}
        )
        return resp.get("data", [])
        
    return await handle_request_errors(_call())


@mcp.tool()
async def get_entity_by_id(entity_type: ALL_ENTITY_TYPES, entity_id: int) -> Union[List[Dict], Dict]:
    """Get detailed information about an entity by its ID."""
    
    async def _call():
        fields = await SG.fetch_entity_fields(entity_type)
        params = {"fields": ",".join(fields), "filter[id]": entity_id}
        response = await SG.get_request(f"/entity/{entity_type}", params=params)
        data = response.get("data", [])
        return [remove_exclude_fields(d) for d in data] if data else []
        
    return await handle_request_errors(_call())


register_booking_tools(mcp, SG)
register_note_tools(mcp, SG)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "MCP Server for ShotGrid. Credentials can be supplied via "
            "environment variables (SHOTGRID_HOST, SHOTGRID_CLIENT_ID, "
            "SHOTGRID_CLIENT_SECRET) or CLI arguments. Env vars take precedence."
        )
    )
    parser.add_argument("-host", "--host", type=str, help="ShotGrid host URL (env: SHOTGRID_HOST)")
    parser.add_argument("-ci", "--client-id", type=str, help="OAuth2 client ID (env: SHOTGRID_CLIENT_ID)")
    parser.add_argument("-cs", "--client-secret", type=str, help="OAuth2 client secret (env: SHOTGRID_CLIENT_SECRET)")
    args = parser.parse_args()

    host = os.environ.get("SHOTGRID_HOST") or args.host
    client_id = os.environ.get("SHOTGRID_CLIENT_ID") or args.client_id
    client_secret = os.environ.get("SHOTGRID_CLIENT_SECRET") or args.client_secret

    missing = [name for name, value in (
        ("host (SHOTGRID_HOST or --host)", host),
        ("client_id (SHOTGRID_CLIENT_ID or --client-id)", client_id),
        ("client_secret (SHOTGRID_CLIENT_SECRET or --client-secret)", client_secret),
    ) if not value]
    if missing:
        parser.error("Missing required credentials: " + ", ".join(missing))

    SG.set_host(host)
    SG.access_token(client_id=client_id, client_secret=client_secret)
    mcp.run(transport="stdio")
