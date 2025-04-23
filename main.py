import argparse
import httpx
import asyncio
from mcp.server.fastmcp import FastMCP
from typing import List, Dict, Any, Optional

from shotgrid_rest import (
    ShotGridRest,
    EXCLUDE_KEYS
)

SG = ShotGridRest()

# Initialize FastMCP server
mcp = FastMCP("mcp-server-shotgrid-rest")


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
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SG.api_host}/entity/projects?fields=name,code,updated_at", auth=SG.auth
        )
        data = response.json().get("data", [])
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
    async with httpx.AsyncClient() as client:
        reop = await client.get(
            f"{SG.api_host}/entity/HumanUsers?fields=login,name", auth=SG.auth
        )
        data = reop.json().get("data", [])
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
    filters = {"filters": [["name", "contains", name]]}
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
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SG.api_host}/entity/sequences?filter[project.Project.name]={project_name}&fields=name,code,sg_status_list,project,updated_at",
            auth=SG.auth,
        )
        data = response.json().get("data", [])
        for d in data:
            d.pop("links", None)
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
                - name: The name of the shot.
                - code: The shot code.
                - sg_status_list: The status of the shot.
                - sg_sequence: The sequence to which the shot belongs.
                - updated_at: The timestamp of the last update to the shot.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SG.api_host}/entity/shots?filter[project.Project.name]={project_name}&fields=name,code,sg_status_list,sg_sequence,updated_at",
            auth=SG.auth,
        )
        data = response.json().get("data", [])
        for d in data:
            d.pop("links", None)
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
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SG.api_host}/entity/assets?filter[project.Project.name]={project_name}&fields=name,code,sg_status_list,updated_at,sg_asset_type",
            auth=SG.auth,
        )
        data = response.json().get("data", [])
        for d in data:
            d.pop("links", None)
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
    filters = {"filters": [["code", "contains", code]]}
    fields = ["name", "code", "updated_at", "project"]
    resp = await SG.post_request(
        "/entity/assets/_search", json={"filters": filters, "fields": fields}
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
    filters = {
        "filters": [["task_assignees", "is", {"type": "HumanUser", "id": user_id}]]
    }
    fields = ["content", "sg_status_list", "id", "updated_at", "project"]
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
    filters = {
        "filters": [
            ["task_assignees", "is", {"type": "HumanUser", "id": user_id}],
            ["project.Project.name", "is", project_name],
        ]
    }
    fields = ["content", "sg_status_list", "id", "updated_at", "project", "updated_at"]
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
    filters = {"filters": [["entity", "is", {"type": "Shot", "id": shot_id}]]}
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
    filters = {"filters": [["entity", "is", {"type": "Asset", "id": asset_id}]]}
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
    async with httpx.AsyncClient() as client:
        fileds_response = await client.get(
            f"{SG.api_host}/schema/projects/fields", auth=SG.auth
        )

        fields = ",".join(fileds_response.json()["data"].keys())
        response = await client.get(
            f"{SG.api_host}/entity/projects?filter[name]={name}&fields={fields}",
            auth=SG.auth,
        )
        data = response.json().get("data", [])
        if data:
            data = [remove_exclude_fields(d) for d in data]
        return data


@mcp.tool()
async def get_project_by_id(project_id: int):
    """Get detailed information about a project by its ID on ShotGrid.

    Args:
        project_id: The ID of the project to retrieve.

    Returns:
        A dictionary containing the project's details, including name, status, type,
        and other relevant fields as specified in the documentation.
    """
    async with httpx.AsyncClient() as client:
        fileds_response = await client.get(
            f"{SG.api_host}/schema/projects/fields", auth=SG.auth
        )

        fields = ",".join(fileds_response.json()["data"].keys())
        response = await client.get(
            f"{SG.api_host}/entity/projects?filter[id]={project_id}&fields={fields}",
            auth=SG.auth,
        )
        data = response.json().get("data", [])
        if data:
            data = [remove_exclude_fields(d) for d in data]
        return data


@mcp.tool()
async def get_shot_by_id(shot_id: int):
    """Get detailed information about a shot by its ID on ShotGrid.

    Args:
        shot_id: The ID of the shot to retrieve.

    Returns:
        A dictionary containing the shot's details, including name, status, type,
        and other relevant fields as specified in the documentation.
    """
    async with httpx.AsyncClient() as client:
        fileds_response = await client.get(
            f"{SG.api_host}/schema/shots/fields", auth=SG.auth
        )

        fields = ",".join(fileds_response.json()["data"].keys())
        response = await client.get(
            f"{SG.api_host}/entity/shots?filter[id]={shot_id}&fields={fields}",
            auth=SG.auth,
        )
        data = response.json().get("data", [])
        if data:
            data = [remove_exclude_fields(d) for d in data]
        return data


@mcp.tool()
async def get_sequence_by_id(sequence_id: int):
    """Get detailed information about a sequence by its ID on ShotGrid.

    Args:
        sequence_id: The ID of the sequence to retrieve.

    Returns:
        A dictionary containing the sequence's details, including name, status, type,
        and other relevant fields as specified in the documentation.
    """
    async with httpx.AsyncClient() as client:
        fileds_response = await client.get(
            f"{SG.api_host}/schema/sequences/fields", auth=SG.auth
        )

        fields = ",".join(fileds_response.json()["data"].keys())
        response = await client.get(
            f"{SG.api_host}/entity/sequences?filter[id]={sequence_id}&fields={fields}",
            auth=SG.auth,
        )
        data = response.json().get("data", [])
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
    async with httpx.AsyncClient() as client:
        fileds_response = await client.get(
            f"{SG.api_host}/schema/assets/fields", auth=SG.auth
        )

        fields = ",".join(
            [
                field
                for field in fileds_response.json()["data"].keys()
                if not field.startswith("step")
            ]
        )
        response = await client.get(
            f"{SG.api_host}/entity/assets?filter[id]={asset_id}&fields={fields}",
            auth=SG.auth,
        )
        data = response.json().get("data", [])
        if data:
            data = [remove_exclude_fields(d) for d in data]
        return data


@mcp.tool()
async def get_task_by_id(task_id: int):
    """Get detailed information about a task by its ID on ShotGrid.

    Args:
        task_id: The ID of the task to retrieve.

    Returns:
        A dictionary containing the task's details, including name, status, type,
        and other relevant fields as specified in the documentation.
    """
    async with httpx.AsyncClient() as client:
        fileds_response = await client.get(
            f"{SG.api_host}/schema/tasks/fields", auth=SG.auth
        )

        fields = ",".join(fileds_response.json()["data"].keys())
        response = await client.get(
            f"{SG.api_host}/entity/tasks?filter[id]={task_id}&fields={fields}",
            auth=SG.auth,
        )
        data = response.json().get("data", [])
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
    async with httpx.AsyncClient() as client:
        fileds_response = await client.get(
            f"{SG.api_host}/schema/HumanUsers/fields", auth=SG.auth
        )

        fields = ",".join(fileds_response.json()["data"].keys())
        response = await client.get(
            f"{SG.api_host}/entity/HumanUsers?filter[id]={user_id}&fields={fields}",
            auth=SG.auth,
        )
        data = response.json().get("data", [])
        return data


@mcp.tool()
async def get_user_by_login(login: str):
    """Get detailed information about a user by their login on ShotGrid.
    Args:
        login: The login of the user to retrieve.
    Returns:
        A dictionary containing the user's details, including login, name, and other relevant fields.
    """
    async with httpx.AsyncClient() as client:
        fileds_response = await client.get(
            f"{SG.api_host}/schema/HumanUsers/fields", auth=SG.auth
        )
        fields = ",".join(fileds_response.json()["data"].keys())
        response = await client.get(
            f"{SG.api_host}/entity/HumanUsers?filter[login]={login}&fields={fields}",
            auth=SG.auth,
        )
        data = response.json().get("data", [])
        return data


@mcp.tool()
async def get_note_by_id(note_id: int):
    """Get detailed information about a note by its ID on ShotGrid.
    Args:
        note_id: The ID of the note to retrieve.
    Returns:
        A dictionary containing the note's details, including content, author, and other relevant fields.
    """
    async with httpx.AsyncClient() as client:
        fileds_response = await client.get(
            f"{SG.api_host}/schema/notes/fields", auth=SG.auth
        )
        fields = ",".join(fileds_response.json()["data"].keys())
        response = await client.get(
            f"{SG.api_host}/entity/notes?filter[id]={note_id}&fields={fields}",
            auth=SG.auth,
        )
        data = response.json().get("data", [])
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
    async with httpx.AsyncClient() as client:

        response = await client.get(
            f"{SG.api_host}/entity/versions?filter[id]={version_id}&fields=notes",
            auth=SG.auth,
        )
        data = response.json().get("data", [])
        if data:
            data = data[0].get("relationships", {}).get("notes", {}).get("data", [])
        return data


@mcp.tool()
async def get_reply_by_id(reply_id: int):
    """Get detailed information about a reply by its ID on ShotGrid.
    Args:
        reply_id: The ID of the reply to retrieve.
    Returns:
        A dictionary containing the reply's details, including content, author, and other relevant fields.
    """
    async with httpx.AsyncClient() as client:
        fileds_response = await client.get(
            f"{SG.api_host}/schema/replies/fields", auth=SG.auth
        )
        fields = ",".join(fileds_response.json()["data"].keys())
        response = await client.get(
            f"{SG.api_host}/entity/replies?filter[id]={reply_id}&fields={fields}",
            auth=SG.auth,
        )
        data = response.json().get("data", [])
        if data:
            data = [remove_exclude_fields(d) for d in data]
        return data


@mcp.tool()
async def get_all_replies_with_note_id(note_id: int):
    """Get all replies associated with a specific note ID on ShotGrid.
    Args:
        note_id: The ID of the note for which to retrieve replies.
    Returns:
        A list of dictionaries, each containing reply details such as content, author, and other relevant fields.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SG.api_host}/entity/notes?filter[id]={note_id}&fields=replies",
            auth=SG.auth,
        )
        data = response.json().get("data", [])
        if data:
            data = data[0].get("relationships", {}).get("replies", {}).get("data", [])
        return data


@mcp.tool()
async def get_version_by_id(version_id: int):
    """Get detailed information about a version by its ID on ShotGrid.

    Args:
        version_id: The ID of the version to retrieve.

    Returns:
        A dictionary containing the version's details, including name, status, type,
        and other relevant fields as specified in the documentation.
    """
    async with httpx.AsyncClient() as client:
        fileds_response = await client.get(
            f"{SG.api_host}/schema/versions/fields", auth=SG.auth
        )

        fields = ",".join(fileds_response.json()["data"].keys())
        response = await client.get(
            f"{SG.api_host}/entity/versions?filter[id]={version_id}&fields={fields}",
            auth=SG.auth,
        )
        data = response.json().get("data", [])
        if data:
            data = [remove_exclude_fields(d) for d in data]
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
    async with httpx.AsyncClient() as client:

        response = await client.get(
            f"{SG.api_host}/entity/versions?filter[sg_task.Task.id]={task_id}&fields=user,updated_at,code,sg_path_to_movie,sg_path_to_frames,description,sg_status_list",
            auth=SG.auth,
        )
        data = response.json().get("data", [])
        if data:
            data = data[0].get("relationships", {}).get("versions", {}).get("data", [])
        return data


def remove_exclude_fields(data: Dict) -> Dict:
    for exclude_key in EXCLUDE_KEYS:
        if exclude_key in data["attributes"].keys():
            del data["attributes"][exclude_key]
    for field in data["attributes"].keys():
        if field.startswith("step_"):
            del data["attributes"][field]
    return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("-host", "--host", type=str, help="host address")
    parser.add_argument("-ci", "--client-id", type=str, help="client-id")
    parser.add_argument("-cs", "--client-secret", type=str, help="client-secret")
    args = parser.parse_args()
    SG.set_host(args.host)
    SG.access_token(client_id=args.client_id, client_secret=args.client_secret)
    mcp.run(transport="stdio")

