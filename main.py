import argparse
import json
from mcp.server.fastmcp import FastMCP
from typing import List, Dict

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
    data = json.dumps(data, ensure_ascii=False)
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
    data = json.dumps(data, ensure_ascii=False)
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
    data = json.dumps(data, ensure_ascii=False)
    return data


@mcp.tool()
async def get_all_projects_code_contains(code: str):
    """
    Retrieve all projects from ShotGrid that contain a specific code.

    Args:
        code (str): The code to search for in project codes.

    Returns:
        List[dict]: A list of dictionaries, each representing a project.
            Each dictionary includes at least the following fields:
                - name: The name of the project.
                - code: The project code.
                - updated_at: The timestamp of the last update to the project.
    """
    filters = [["code", "contains", code]]
    fields = ["name", "code", "updated_at"]
    resp = await SG.post_request(
        "/entity/projects/_search", json={"filters": filters, "fields": fields}
    )
    data = resp.get("data", [])
    data = json.dumps(data, ensure_ascii=False)
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
    data = json.dumps(data, ensure_ascii=False)
    return data


@mcp.tool()
async def get_shots(
    project_name: str = None,
    shot_code: str = None,
):
    """
    Retrieve shots from ShotGrid, filtered by project name and/or shot code substring.

    Args:
        project_name (str, optional): The name of the project to filter shots.
        shot_code (str, optional): The substring to search for in shot codes.

    Returns:
        str: JSON-encoded list of shot dictionaries, each with fields:
            - code
            - sg_status_list
            - sg_sequence
            - updated_at
    """
    filters = []
    if project_name:
        filters.append(["project.Project.name", "is", project_name])
    if shot_code:
        filters.append(["code", "contains", shot_code])
    fields = ["code", "sg_status_list", "sg_sequence", "updated_at"]
    if filters:
        resp = await SG.post_request(
            "/entity/shots/_search", json={"filters": filters, "fields": fields}
        )
        data = resp.get("data", [])
    else:
        params = {"fields": ",".join(fields)}
        resp = await SG.get_request("/entity/shots", params=params)
        data = resp.get("data", [])
    data = json.dumps(data, ensure_ascii=False)
    return data


@mcp.tool()
async def get_assets(
    project_name: str = None,
    code: str = None,
):
    """
    Retrieve assets from ShotGrid, filtered by project name and/or code substring.

    Args:
        project_name (str, optional): The name of the project to filter assets.
        code (str, optional): The substring to search for in asset codes.

    Returns:
        str: JSON-encoded list of asset dictionaries, each with fields:
            - name
            - code
            - sg_status_list
            - updated_at
            - sg_asset_type
            - project
    """
    filters = []
    if project_name:
        filters.append(["project.Project.name", "is", project_name])
    if code:
        filters.append(["code", "contains", code])
    # Combine fields from both original functions
    fields = [
        "name",
        "code",
        "sg_status_list",
        "updated_at",
        "sg_asset_type",
        "project",
    ]

    resp = await SG.post_request(
        "/entity/assets/_search", json={"filters": filters, "fields": fields}
    )
    data = resp.get("data", [])

    data = json.dumps(data, ensure_ascii=False)
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
    data = json.dumps(data, ensure_ascii=False)
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
    data = json.dumps(data, ensure_ascii=False)
    return data


@mcp.tool()
async def get_tasks(
    project_id: int = None,
    user_id: int = None,
):
    """
    Retrieve tasks from ShotGrid, filtered by project and/or assigned user.

    Args:
        project_id (int, optional): The unique ID of the project to filter tasks.
        user_id (int, optional): The unique ID of the user to filter assigned tasks.

    Returns:
        str: JSON-encoded list of task dictionaries, each with fields:
            - content
            - sg_status_list
            - id
            - updated_at
            - project
            - task_assignees
    """
    filters = []
    if project_id is not None:
        filters.append(["project.Project.id", "is", project_id])
    if user_id is not None:
        filters.append(["task_assignees", "is", {"type": "HumanUser", "id": user_id}])
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
    data = json.dumps(data, ensure_ascii=False)
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
    data = json.dumps(data, ensure_ascii=False)
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
    data = json.dumps(data, ensure_ascii=False)
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
    data = json.dumps(data, ensure_ascii=False)
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
    data = json.dumps(data, ensure_ascii=False)
    return data


@mcp.tool()
async def get_users_name_contains(name: str):
    """Get detailed information about users whose names contain a specific substring on ShotGrid.
    Args:
        name: The substring to search for in user names.
    Returns:
        A list of dictionaries, each containing the user's details, including login, name, and other relevant fields.
    """
    filters = [["name", "contains", name]]
    fields = ["login", "name"]
    response = await SG.post_request(
        "/entity/HumanUsers/_search", json={"filters": filters, "fields": fields}
    )
    data = response.get("data", [])
    if data:
        data = [remove_exclude_fields(d) for d in data]
    data = json.dumps(data, ensure_ascii=False)
    return data


@mcp.tool()
async def get_users_login_contains(login: str):
    """Get detailed information about users whose logins contain a specific substring on ShotGrid.
    Args:
        login: The substring to search for in user logins.
    Returns:
        A list of dictionaries, each containing the user's details, including login, name, and other relevant fields.
    """
    filters = [["login", "contains", login]]
    fields = ["login", "name"]
    response = await SG.post_request(
        "/entity/HumanUsers/_search", json={"filters": filters, "fields": fields}
    )
    data = response.get("data", [])
    if data:
        data = [remove_exclude_fields(d) for d in data]
    data = json.dumps(data, ensure_ascii=False)
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
    data = json.dumps(data, ensure_ascii=False)
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
    data = json.dumps(data, ensure_ascii=False)
    return data


@mcp.tool()
async def get_versions(
    project_id: int = None,
    task_id: int = None,
    updated_in_last_n_days: int = None,
):
    """
    Retrieve versions from ShotGrid, filtered by project, task, and/or updated in last n days.

    Args:
        project_id (int, optional): The ID of the project to filter versions.
        task_id (int, optional): The ID of the task to filter versions.
        updated_in_last_n_days (int, optional): Only include versions updated in the last n days.

    Returns:
        str: JSON-encoded list of version dictionaries, each with fields:
            - user
            - updated_at
            - code
            - sg_path_to_movie
            - sg_path_to_frames
            - description
            - sg_status_list
    """
    filters = []
    if project_id is not None:
        filters.append(["project.Project.id", "is", project_id])
    if task_id is not None:
        filters.append(["sg_task.Task.id", "is", task_id])
    if updated_in_last_n_days is not None:
        filters.append(["updated_at", "in_last", [updated_in_last_n_days, "DAY"]])
    fields = [
        "user",
        "updated_at",
        "code",
        "sg_path_to_movie",
        "sg_path_to_frames",
        "description",
        "sg_status_list",
    ]
    if filters:
        resp = await SG.post_request(
            "/entity/versions/_search", json={"filters": filters, "fields": fields}
        )
        data = resp.get("data", [])
    else:
        params = {"fields": ",".join(fields)}
        resp = await SG.get_request("/entity/versions", params=params)
        data = resp.get("data", [])
    data = json.dumps(data, ensure_ascii=False)
    return data


@mcp.tool()
async def get_all_vacation_bookings(
    start_date_from: List[int] = None,
    start_date_to: List[int] = None,
    end_date_from: List[int] = None,
    end_date_to: List[int] = None,
):
    """
    Retrieve all vacation bookings in ShotGrid, with optional date filters.

    Args:
        start_date_from (List[int], optional): Only include bookings starting after this date [YYYY, MM, DD].
        start_date_to (List[int], optional): Only include bookings starting before this date [YYYY, MM, DD].
        end_date_from (List[int], optional): Only include bookings ending after this date [YYYY, MM, DD].
        end_date_to (List[int], optional): Only include bookings ending before this date [YYYY, MM, DD].

    Returns:
        str: A JSON-encoded list of dictionaries, each representing a vacation booking.
            Each dictionary contains fields such as:
                - user: The user who created the booking.
                - updated_at: The timestamp of the last update to the booking.
                - sg_status_list: The status of the booking.
                - start_date: The start date of the booking.
                - end_date: The end date of the booking.
    """
    filters = [
        ["vacation", "is", True],
    ]
    if start_date_from:
        filters.append(
            [
                "start_date",
                "greater_than",
                f"{start_date_from[0]:04}-{start_date_from[1]:02}-{start_date_from[2]:02}",
            ]
        )
    if start_date_to:
        filters.append(
            [
                "start_date",
                "less_than",
                f"{start_date_to[0]:04}-{start_date_to[1]:02}-{start_date_to[2]:02}",
            ]
        )
    if end_date_from:
        filters.append(
            [
                "end_date",
                "greater_than",
                f"{end_date_from[0]:04}-{end_date_from[1]:02}-{end_date_from[2]:02}",
            ]
        )
    if end_date_to:
        filters.append(
            [
                "end_date",
                "less_than",
                f"{end_date_to[0]:04}-{end_date_to[1]:02}-{end_date_to[2]:02}",
            ]
        )
    fields = [
        "user",
        "updated_at",
        "sg_status_list",
        "start_date",
        "end_date",
    ]
    resp = await SG.post_request(
        "/entity/bookings/_search", json={"filters": filters, "fields": fields}
    )
    data = resp.get("data", [])
    data = json.dumps(data, ensure_ascii=False)
    return data


@mcp.tool()
async def get_all_bookings_in_date_range(
    start_date_from: List[int] = None,
    start_date_to: List[int] = None,
    end_date_from: List[int] = None,
    end_date_to: List[int] = None,
):
    """
    Retrieve all bookings in ShotGrid, with optional date filters.

    Args:
        start_date_from (List[int], optional): Only include bookings starting after this date [YYYY, MM, DD].
        start_date_to (List[int], optional): Only include bookings starting before this date [YYYY, MM, DD].
        end_date_from (List[int], optional): Only include bookings ending after this date [YYYY, MM, DD].
        end_date_to (List[int], optional): Only include bookings ending before this date [YYYY, MM, DD].

    Returns:
        str: A JSON-encoded list of dictionaries, each representing a booking.
            Each dictionary contains fields such as:
                - user: The user who created the booking.
                - updated_at: The timestamp of the last update to the booking.
                - sg_status_list: The status of the booking.
                - start_date: The start date of the booking.
                - end_date: The end date of the booking.
                - project: The project associated with the booking.
    """
    filters = []
    if start_date_from:
        filters.append(
            [
                "start_date",
                "greater_than",
                f"{start_date_from[0]:04}-{start_date_from[1]:02}-{start_date_from[2]:02}",
            ]
        )
    if start_date_to:
        filters.append(
            [
                "start_date",
                "less_than",
                f"{start_date_to[0]:04}-{start_date_to[1]:02}-{start_date_to[2]:02}",
            ]
        )
    if end_date_from:
        filters.append(
            [
                "end_date",
                "greater_than",
                f"{end_date_from[0]:04}-{end_date_from[1]:02}-{end_date_from[2]:02}",
            ]
        )
    if end_date_to:
        filters.append(
            [
                "end_date",
                "less_than",
                f"{end_date_to[0]:04}-{end_date_to[1]:02}-{end_date_to[2]:02}",
            ]
        )
    if (
        not start_date_from
        and not start_date_to
        and not end_date_from
        and not end_date_to
    ):
        return [
            {
                "error": "No date filters provided. Please provide at least one date filter."
            }
        ]
    fields = [
        "user",
        "updated_at",
        "sg_status_list",
        "start_date",
        "end_date",
        "project",
    ]
    resp = await SG.post_request(
        "/entity/bookings/_search", json={"filters": filters, "fields": fields}
    )
    data = resp.get("data", [])
    data = json.dumps(data, ensure_ascii=False)
    return data


@mcp.tool()
async def get_all_bookings(
    user_id: int = None,
    project_id: int = None,
    start_date_from: List[int] = None,
    start_date_to: List[int] = None,
    end_date_from: List[int] = None,
    end_date_to: List[int] = None,
):
    """
    Retrieve all bookings in ShotGrid, filtered by user, project, and/or date.

    Args:
        user_id (int, optional): Only include bookings for this user.
        project_id (int, optional): Only include bookings for this project.
        start_date_from (List[int], optional): Only include bookings starting after this date [YYYY, MM, DD].
        start_date_to (List[int], optional): Only include bookings starting before this date [YYYY, MM, DD].
        end_date_from (List[int], optional): Only include bookings ending after this date [YYYY, MM, DD].
        end_date_to (List[int], optional): Only include bookings ending before this date [YYYY, MM, DD].

    Returns:
        str: JSON-encoded list of booking dictionaries, each with fields like:
            - user
            - updated_at
            - project
            - vacation
            - sg_status_list
            - start_date
            - end_date
    """
    filters = []
    if user_id is not None:
        filters.append(["user.HumanUser.id", "is", user_id])
    if project_id is not None:
        filters.append(["project.Project.id", "is", project_id])
    if start_date_from:
        filters.append(
            [
                "start_date",
                "greater_than",
                f"{start_date_from[0]:04}-{start_date_from[1]:02}-{start_date_from[2]:02}",
            ]
        )
    if start_date_to:
        filters.append(
            [
                "start_date",
                "less_than",
                f"{start_date_to[0]:04}-{start_date_to[1]:02}-{start_date_to[2]:02}",
            ]
        )
    if end_date_from:
        filters.append(
            [
                "end_date",
                "greater_than",
                f"{end_date_from[0]:04}-{end_date_from[1]:02}-{end_date_from[2]:02}",
            ]
        )
    if end_date_to:
        filters.append(
            [
                "end_date",
                "less_than",
                f"{end_date_to[0]:04}-{end_date_to[1]:02}-{end_date_to[2]:02}",
            ]
        )
    fields = [
        "user",
        "updated_at",
        "project",
        "vacation",
        "sg_status_list",
        "start_date",
        "end_date",
    ]
    resp = await SG.post_request(
        "/entity/bookings/_search", json={"filters": filters, "fields": fields}
    )
    data = resp.get("data", [])
    data = json.dumps(data, ensure_ascii=False)
    return data


@mcp.tool()
async def get_entities_updated_in_last_n_days(
    entity_type: str,
    n: int,
    project_id: int = None,
):
    """
    Retrieve entities of a specified type that have been updated within the last n days,
    optionally filtered by project.

    Args:
        entity_type (str): The type of entity to retrieve (e.g., "projects", "shots", "assets").
        n (int): The number of days to look back for recently updated entities.
        project_id (int, optional): The unique ID of the project to filter entities by.

    Returns:
        str: JSON-encoded list of entity dictionaries, each with fields as defined in the ShotGrid schema.
    """
    filters = [["updated_at", "in_last", [n, "DAY"]]]
    if project_id is not None:
        filters.append(["project", "is", {"type": "Project", "id": project_id}])
    fields = GENERAL_FIELDS
    resp = await SG.post_request(
        f"/entity/{entity_type}/_search", json={"filters": filters, "fields": fields}
    )
    data = resp.get("data", [])
    data = json.dumps(data, ensure_ascii=False)
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
    data = json.dumps(data, ensure_ascii=False)
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
