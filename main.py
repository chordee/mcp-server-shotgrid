import argparse
from mcp.server.fastmcp import FastMCP
from typing import List, Dict, Any

from shotgrid_rest import ShotGridRest
from shotgrid_options import GENERAL_FIELDS, EXCLUDE_KEYS, ALL_ENTITY_TYPES

SG = ShotGridRest()

# Initialize FastMCP server
mcp = FastMCP("mcp-server-shotgrid")


def remove_exclude_fields(data: Dict) -> Dict:
    for exclude_key in EXCLUDE_KEYS:
        if exclude_key in data["attributes"].keys():
            del data["attributes"][exclude_key]
    for field in list(data["attributes"].keys()):
        if field.startswith("step_"):
            del data["attributes"][field]
    return data


@mcp.tool()
async def get_all_projects():
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
    fields = [
        "name",
        "code",
        "id",
        "updated_at",
    ]
    params = {"fields": ",".join(fields)}
    response = await SG.get_request("/entity/projects", params=params)
    data = response.get("data", [])
    return data


@mcp.tool()
async def get_all_users():
    """
    Retrieve all users from ShotGrid.

    Returns:
        List[dict]: A list of dictionaries, each representing a user.
            Each dictionary includes at least the following fields:
                - login: The user's login name.
                - name: The user's full name.
            Additional user-related fields may also be included depending on ShotGrid configuration.
    """
    fields = ["login", "name"]
    params = {"fields": ",".join(fields)}
    response = await SG.get_request("/entity/HumanUsers", params=params)
    data = response.get("data", [])
    return data


@mcp.tool()
async def get_all_projects_name_contains(name: str):
    """
    Retrieve all projects from ShotGrid that contain a specific name.

    Args:
        name (str): The name to search for in project names.

    Returns:
        List[dict]: A list of dictionaries, each representing a project.
            Each dictionary includes at least the following fields:
                - name: The name of the project.
                - code: The project code.
                - updated_at: The timestamp of the last update to the project.
    """
    filters = [["name", "contains", name]]
    fields = ["name", "code", "updated_at"]
    resp = await SG.post_request(
        "/entity/projects/_search", json={"filters": filters, "fields": fields}
    )
    data = resp.get("data", [])
    return data


@mcp.tool()
async def get_all_sequences_in_project(project_name: str):
    """
    Retrieve all sequences within a specified project from ShotGrid.

    Args:
        project_name (str): The name of the project for which to retrieve sequences.

    Returns:
        List[dict]: A list of dictionaries, each containing details for a sequence,
            including at least the sequence's name, code, status, and associated project.
    """
    fields = ["name", "code", "sg_status_list", "project", "updated_at"]
    params = {"fields": ",".join(fields), "filter[project.Project.name]": project_name}
    response = await SG.get_request("/entity/sequences", params=params)
    data = response.get("data", [])
    return data


@mcp.tool()
async def get_all_shots_in_project(project_name: str):
    """
    Retrieve all shots within a specified project from ShotGrid.

    Args:
        project_name (str): The name of the project for which to retrieve shots.

    Returns:
        List[dict]: A list of dictionaries, each representing a shot in the project.
            Each dictionary includes at least the following fields:
                - code: The shot code.
                - sg_status_list: The status of the shot.
                - sg_sequence: The sequence to which the shot belongs.
                - updated_at: The timestamp of the last update to the shot.
    """
    fields = ["code", "sg_status_list", "sg_sequence", "updated_at"]
    params = {
        "fields": ",".join(fields),
        "filter[project.Project.name]": project_name,
    }
    response = await SG.get_request("/entity/shots", params=params)
    data = response.get("data", [])
    return data


@mcp.tool()
async def get_all_shots_code_contains(shot_code: str):
    """
    Retrieve all shots within a specified project from ShotGrid.
    Args:
        shot_code (str): The name of the shot for which to retrieve shots.
    Returns:
        List[dict]: A list of dictionaries, each representing a shot in the project.
            Each dictionary includes at least the following fields:
                - code: The shot code.
                - sg_status_list: The status of the shot.
                - sg_sequence: The sequence to which the shot belongs.
                - updated_at: The timestamp of the last update to the shot.
    """
    filters = [["code", "contains", shot_code]]
    fields = ["code", "sg_status_list", "sg_sequence", "updated_at"]
    response = await SG.post_request(
        "/entity/shots", json={"filters": filters, "fields": fields}
    )
    data = response.get("data", [])
    return data


@mcp.tool()
async def get_all_assets_in_project(project_name: str):
    """
    Retrieve all assets within a specified project on ShotGrid.

    Args:
        project_name (str): The name of the project to search for assets.

    Returns:
        List[dict]: A list of dictionaries, each containing details for an asset,
            including at least the asset's name, code, status, last update time, and asset type.
    """
    fields = ["name", "code", "sg_status_list", "updated_at", "sg_asset_type"]
    params = {
        "fields": ",".join(fields),
        "filter[project.Project.name]": project_name,
    }
    response = await SG.get_request("/entity/assets", params=params)
    data = response.get("data", [])
    return data


@mcp.tool()
async def get_all_assets_code_contains(code: str):
    """
    Retrieve all assets from ShotGrid whose code(name) contains a specific substring.

    Args:
        code (str): The substring to search for within asset codes.

    Returns:
        List[dict]: A list of dictionaries, each representing an asset.
            Each dictionary includes at least the following fields:
                - name: The name of the asset.
                - code: The asset code(name).
                - updated_at: The timestamp of the last update to the asset.
                - project: The project to which the asset belongs.
    """
    filters = [["code", "contains", code]]
    fields = ["name", "code", "updated_at", "project"]
    resp = await SG.post_request(
        "/entity/assets/_search", json={"filters": filters, "fields": fields}
    )
    data = resp.get("data", [])
    return data


@mcp.tool()
async def get_all_tasks_in_project(project_id: int):
    """
    Retrieve all tasks within a specified project in ShotGrid.

    Args:
        project_id (int): The unique ID of the project for which to retrieve tasks.

    Returns:
        List[dict]: A list of dictionaries, each containing details for a task,
            including at least the task's name (content), status, ID, last update time, and project.
    """
    filters = [["project.Project.id", "is", project_id]]
    fields = [
        "content",
        "sg_status_list",
        "id",
        "updated_at",
        "project",
        "task_assignees",
    ]
    resp = await SG.post_request(
        "/entity/tasks/_search", json={"filters": filters, "fields": fields}
    )
    data = resp.get("data", [])
    return data


@mcp.tool()
async def get_all_tasks_assigned_to_user(user_id: int):
    """
    Retrieve all tasks assigned to a specific user in ShotGrid.

    Args:
        user_id (int): The unique ID of the user whose tasks should be retrieved.

    Returns:
        List[dict]: A list of dictionaries, each containing details for a task,
            including at least the task's name (content), status, ID, last update time, and project.
    """
    filters = [["task_assignees", "is", {"type": "HumanUser", "id": user_id}]]
    fields = [
        "content",
        "sg_status_list",
        "id",
        "updated_at",
        "project",
        "task_assignees",
    ]
    resp = await SG.post_request(
        "/entity/tasks/_search", json={"filters": filters, "fields": fields}
    )
    data = resp.get("data", [])
    return data


@mcp.tool()
async def get_all_tasks_assigned_to_user_in_project_name(
    user_id: int, project_name: str
):
    """
    Retrieve all tasks assigned to a specific user in a specific project in ShotGrid.
    Args:
        user_id (int): The unique ID of the user whose tasks should be retrieved.
        project_name (str): The name of the project whose tasks should be retrieved.
    Returns:
        List[dict]: A list of dictionaries, each containing details for a task,
            including at least the task's name (content), status, ID, last update time, and project.
    """
    filters = [
        ["task_assignees", "is", {"type": "HumanUser", "id": user_id}],
        ["project.Project.name", "is", project_name],
    ]

    fields = [
        "content",
        "sg_status_list",
        "id",
        "updated_at",
        "project",
        "task_assignees",
    ]
    resp = await SG.post_request(
        "/entity/tasks/_search", json={"filters": filters, "fields": fields}
    )
    data = resp.get("data", [])
    return data


@mcp.tool()
async def get_all_tasks_with_shot(shot_id: int):
    """
    Retrieve all tasks associated with a specific shot in ShotGrid.
    Args:
        shot_id (int): The unique ID of the shot whose tasks should be retrieved.
    Returns:
        List[dict]: A list of dictionaries, each containing details for a task,
            including at least the task's name (content), status, ID, last update time, project,
            task assignees, cached display name, and step.
    """
    filters = [["entity", "is", {"type": "Shot", "id": shot_id}]]
    fields = [
        "content",
        "sg_status_list",
        "id",
        "updated_at",
        "project",
        "task_assignees",
        "cached_display_name",
        "step",
    ]
    resp = await SG.post_request(
        "/entity/tasks/_search", json={"filters": filters, "fields": fields}
    )
    data = resp.get("data", [])
    return data


@mcp.tool()
async def get_all_tasks_with_asset(asset_id: int):
    """
    Retrieve all tasks associated with a specific asset in ShotGrid.
    Args:
        asset_id (int): The unique ID of the asset whose tasks should be retrieved.
    Returns:
        List[dict]: A list of dictionaries, each containing details for a task,
            including at least the task's name (content), status, ID, last update time, project,
            task assignees, cached display name, and step.
    """
    filters = [["entity", "is", {"type": "Asset", "id": asset_id}]]
    fields = [
        "content",
        "sg_status_list",
        "id",
        "updated_at",
        "project",
        "task_assignees",
        "cached_display_name",
        "step",
    ]
    resp = await SG.post_request(
        "/entity/tasks/_search", json={"filters": filters, "fields": fields}
    )
    data = resp.get("data", [])
    return data


@mcp.tool()
async def get_project_by_name(name: str):
    """Retrieve project details on ShotGrid based on name.

    Args:
        name: Project name

    Returns:
        A dictionary containing the project's details, including name, status, type,
        and other relevant fields as specified in the documentation.
    """
    fields = await SG.fetch_entity_fields("projects")
    params = {
        "fields": ",".join(fields),
        "filter[name]": name,
    }
    response = await SG.get_request("/entity/projects", params=params)
    data = response.get("data", [])
    if data:
        data = [remove_exclude_fields(d) for d in data]
    return data


@mcp.tool()
async def get_asset_by_id(asset_id: int):
    """Get detailed information about an asset by its ID on ShotGrid.

    Args:
        asset_id: The ID of the asset to retrieve.

    Returns:
        A dictionary containing the asset's details, including name, status, type,
        and other relevant fields as specified in the documentation.
    """
    fields = await SG.fetch_entity_fields("assets")
    params = {
        "fields": ",".join(
            [field for field in fields if not field.startswith("step_")]
        ),
        "filter[id]": asset_id,
    }
    response = await SG.get_request("/entity/assets", params=params)
    data = response.get("data", [])
    if data:
        data = [remove_exclude_fields(d) for d in data]
    return data


@mcp.tool()
async def get_user_by_id(user_id: int):
    """Get detailed information about a user by their ID on ShotGrid.

    Args:
        user_id: The ID of the user to retrieve.

    Returns:
        A dictionary containing the user's details, including login, name, and other relevant fields.
    """
    fields = await SG.fetch_entity_fields("HumanUsers")
    params = {"fields": ",".join(fields), "filter[id]": user_id}
    response = await SG.get_request("/entity/HumanUsers", params=params)
    data = response.get("data", [])
    if data:
        data = [remove_exclude_fields(d) for d in data]
    return data


@mcp.tool()
async def get_user_by_login(login: str):
    """Get detailed information about a user by their login on ShotGrid.
    Args:
        login: The login of the user to retrieve.
    Returns:
        A dictionary containing the user's details, including login, name, and other relevant fields.
    """
    fields = await SG.fetch_entity_fields("HumanUsers")
    params = {
        "fields": ",".join(fields),
        "filter[login]": login,
    }
    response = await SG.get_request("/entity/HumanUsers", params=params)
    data = response.get("data", [])
    if data:
        data = [remove_exclude_fields(d) for d in data]
    return data


@mcp.tool()
async def get_all_notes_with_version(version_id: int):
    """
    Retrieve all notes associated with a specific version in ShotGrid.

    Args:
        version_id (int): The ID of the version for which to retrieve associated notes.

    Returns:
        List[dict]: A list of dictionaries, each representing a note associated with the given version.

    """
    params = {
        "fields": "notes",
        "filter[id]": version_id,
    }
    response = await SG.get_request("/entity/versions", params=params)
    data = response.get("data", [])
    if data:
        data = data[0].get("relationships", {}).get("notes", {}).get("data", [])
    return data


@mcp.tool()
async def get_all_replies_with_note_id(note_id: int):
    """Get all replies associated with a specific note ID on ShotGrid.
    Args:
        note_id: The ID of the note for which to retrieve replies.
    Returns:
        A list of dictionaries, each containing reply details such as content, author, and other relevant fields.
    """
    params = {
        "fields": "replies",
        "filter[id]": note_id,
    }
    response = await SG.get_request("/entity/notes", params=params)
    data = response.get("data", [])
    if data:
        data = data[0].get("relationships", {}).get("replies", {}).get("data", [])
    return data


@mcp.tool()
async def get_all_versions_with_task(task_id: int):
    """
    Retrieve all version entities in ShotGrid that are linked to a specific task.

    Args:
        task_id (int): The ID of the task for which to retrieve associated versions.

    Returns:
        List[dict]: A list of dictionaries, each representing a version associated with the given task.
            Each dictionary contains fields such as:
                - user: The user who created the version.
                - updated_at: The timestamp of the last update to the version.
                - code: The version's code or name.
                - sg_path_to_movie: Path to the version's movie file, if available.
                - sg_path_to_frames: Path to the version's frames, if available.
                - description: The description of the version, if provided.
                - sg_status_list: The status of the version (e.g., "wip", "fin", etc.).
    """
    fields = [
        "user",
        "updated_at",
        "code",
        "sg_path_to_movie",
        "sg_path_to_frames",
        "description",
        "sg_status_list",
    ]
    params = {
        "fields": ",".join(fields),
        "filter[sg_task.Task.id]": task_id,
    }
    response = await SG.get_request("/entity/versions", params=params)
    data = response.get("data", [])
    return data


@mcp.tool()
async def get_all_versions_in_project(project_id: int):
    """
    Retrieve all version entities in ShotGrid that are linked to a specific project.

    Args:
        project_id (int): The ID of the project for which to retrieve associated versions.

    Returns:
        List[dict]: A list of dictionaries, each representing a version associated with the given project.
            Each dictionary contains fields such as:
                - user: The user who created the version.
                - updated_at: The timestamp of the last update to the version.
                - code: The version's code or name.
                - sg_path_to_movie: Path to the version's movie file, if available.
                - sg_path_to_frames: Path to the version's frames, if available.
                - description: The description of the version, if provided.
                - sg_status_list: The status of the version (e.g., "wip", "fin", etc.).
    """
    filters = [["project.Project.id", "is", project_id]]
    fields = [
        "user",
        "updated_at",
        "code",
        "sg_path_to_movie",
        "sg_path_to_frames",
        "description",
        "sg_status_list",
    ]
    resp = await SG.post_request(
        "/entity/versions/_search", json={"filters": filters, "fields": fields}
    )
    data = resp.get("data", [])
    return data


@mcp.tool()
async def get_all_versions_in_project_updated_in_last_n_days(
    project_id: int, n: int
) -> List[Dict[str, Any]]:
    """
    Retrieve all versions in a specific project that have been updated within the last n days.

    Args:
        project_id (int): The ID of the project to filter versions by.
        n (int): The number of days to look back for recently updated versions.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, each representing a version associated with the given project.
            Each dictionary contains fields such as user, updated_at, code, sg_path_to_movie,
            sg_path_to_frames, description, and sg_status_list.
    """
    filters = [
        ["updated_at", "in_last", [n, "DAY"]],
        ["project.Project.id", "is", project_id],
    ]
    fields = [
        "user",
        "updated_at",
        "code",
        "sg_path_to_movie",
        "sg_path_to_frames",
        "description",
        "sg_status_list",
    ]
    resp = await SG.post_request(
        "/entity/versions/_search", json={"filters": filters, "fields": fields}
    )
    data = resp.get("data", [])
    return data


@mcp.tool()
async def get_entities_updated_in_last_n_days(
    entity_type: str, n: int
) -> List[Dict[str, Any]]:
    """
    Retrieve entities of a specified type that have been updated within the last n days.

    Args:
        entity_type (str): The type of entity to retrieve (e.g., "projects", "shots", "assets").
        n (int): The number of days to look back for recently updated entities.

    Returns:
        List[Dict[str, Any]]:  A dictionary containing the entity's details, including fields such as name, status, type, id
            and other relevant attributes as defined in the ShotGrid schema for the specified entity type.
    """
    filters = [["updated_at", "in_last", [n, "DAY"]]]
    fields = GENERAL_FIELDS
    resp = await SG.post_request(
        f"/entity/{entity_type}/_search", json={"filters": filters, "fields": fields}
    )
    data = resp.get("data", [])
    return data


@mcp.tool()
async def get_entities_updated_in_last_n_days_with_project(
    entity_type: str, project_id: int, n: int
) -> List[Dict[str, Any]]:
    """
    Retrieve entities of a specified type that have been updated within the last n days and belong to a specific project.

    Args:
        entity_type (str): The type of entity to retrieve (e.g., "projects", "shots", "assets").
        project_id (int): The unique ID of the project to filter entities by.
        n (int): The number of days to look back for recently updated entities.

    Returns:
        List[Dict[str, Any]]: A dictionary containing the entity's details, including fields such as name, status, type, id
            and other relevant attributes as defined in the ShotGrid schema for the specified entity type.
    """
    filters = [
        ["updated_at", "in_last", [n, "DAY"]],
        ["project", "is", {"type": "Project", "id": project_id}],
    ]
    fields = GENERAL_FIELDS
    resp = await SG.post_request(
        f"/entity/{entity_type}/_search", json={"filters": filters, "fields": fields}
    )
    data = resp.get("data", [])
    return data


@mcp.tool()
async def get_entity_by_id(entity_type: ALL_ENTITY_TYPES, entity_id: int):
    """
    Get detailed information about an entity by its ID on ShotGrid.

    Args:
        entity_type (str): The type of entity to retrieve (e.g., "versions", "shots", "assets").
        entity_id (int): The ID of the entity to retrieve.

    Returns:
        dict: A dictionary containing the entity's details, including fields such as name, status, type, id
            and other relevant attributes as defined in the ShotGrid schema for the specified entity type.
    """
    fields = await SG.fetch_entity_fields(entity_type)
    params = {
        "fields": ",".join(fields),
        "filter[id]": entity_id,
    }
    response = await SG.get_request(f"/entity/{entity_type}", params=params)
    data = response.get("data", [])
    if data:
        data = [remove_exclude_fields(d) for d in data]
    return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("-host", "--host", type=str, help="host address", required=True)
    parser.add_argument("-ci", "--client-id", type=str, help="client-id", required=True)
    parser.add_argument(
        "-cs", "--client-secret", type=str, help="client-secret", required=True
    )
    args = parser.parse_args()
    SG.set_host(args.host)
    SG.access_token(client_id=args.client_id, client_secret=args.client_secret)
    mcp.run(transport="stdio")
