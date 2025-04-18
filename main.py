import argparse
import httpx
import asyncio
import json
from mcp.server.fastmcp import FastMCP
from typing import List, Dict, Any, Optional, Literal
from httpx_auth import OAuth2ClientCredentials


class ShotGridRest:
    def __init__(self):
        self.host = None
        self.auth = None

    def set_host(self, host: str, version: str = "1.1") -> None:
        self.host = host
        self.api_host = f"{self.host}/api/v{version}"

    def access_token(self, client_id: str, client_secret: str) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        print("Token accessing...")
        self.auth = OAuth2ClientCredentials(
            f"{self.host}/api/v1.1/auth/access_token",
            client_id=self.client_id,
            client_secret=self.client_secret,
        )
        print("Result:", self.auth.state)

    async def _post_request(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
    ):
        url = f"{self.api_host}{path}"
        headers = {"Content-Type": "application/vnd+shotgun.api3_array+json"}
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=json, headers=headers, auth=self.auth)
            # resp.raise_for_status()
            print(resp.json())
            return resp.json()

    async def _fetch_entity_fields(self, entity_type):
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{SG.api_host}/schema/{entity_type}/fields", auth=SG.auth
            )
            data = resp.json().get("data", [])
            return data.keys()


SG = ShotGridRest()

ARRAY_HEADER = {"Content-Type": "application/vnd+shotgun.api3_array+json"}
HASH_HEADER = {"Content-Type": "application/vnd+shotgun.api3_hash+json"}

EXCLUDE_KEYS = ("sg_know_how", "tracking_settings")

ALL_ENTITY_TYPES = Literal[
    "projects",
    "assets",
    "versions",
    "tasks",
    "sequences",
    "shots",
    "HumanUsers",
    "notes",
    "steps",
    "steps",
]

EXPLAIN_FIELDS = {
    "sg_res_width": "Resolution Width",
    "sg_res_height": "Resolution Height",
    "description": "Description",
    "start_date": "Start Date",
    "end_date": "End Date",
    "sg_render_engine": "Render Engine",
    "updated_at": "Last Updated Time",
    "created_at": "Created Time",
    "code": "Code Name (Alternaitve Name)",
    "name": "Name",
    "type": "Entity Type",
    "id": "ID",
    "sg_fps": "FPS",
    "sg_project_root": "Project Root",
    "tank_name": "Folder Name",
    "sg_status": "Status",
    "landing_page_url": "Address on Shotgrid",
    "sg_pmb_id": "PMB ID",
    "archived": "Is Archived",
    "sg_zulip_stream": "Zulip Stream",
    "sg_unit": "Unit",
    "sg_scale": "Scale",
    "cached_display_name": "Display Name",
    "sg_type": "Description Type",
    "sg_status_list": "Status",
    "sg_asset_type": "Asset Type",
}

EXPLAIN_RELS = {"shots": "Shot", "tasks": "Tasks"}


# Initialize FastMCP server
mcp = FastMCP("mcp-server-shotgrid-rest")


@mcp.tool()
async def get_all_projects():
    """Get the name, code and ID of all projects on ShotGrid."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SG.api_host}/entity/projects?fields=name,code", auth=SG.auth
        )
        data = response.json().get("data", [])
        # data = sort_list_data(data)
        return data


@mcp.tool()
async def get_all_assets_in_project(project_name: str):
    """Get the name, status and ID of every asset within the project of the given name.

    Args:
        project_name: Project name
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SG.api_host}/entity/assets?fileter[project.Project.name]={project_name}&fields=name,code,sg_status_list,updated_at,sg_asset_type",
            auth=SG.auth,
        )
        data = response.json().get("data", [])
        for d in data:
            d.pop("links", None)
        # data = sort_list_data(data)
        return data


@mcp.tool()
async def get_project_by_name(name: str):
    """Retrieve project details on ShotGrid based on name.

    Args:
        name: Project name
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
        return data


@mcp.tool()
async def list_asset_tasks_with_assignees(asset_id: int) -> str:
    """
    List all tasks for a specified asset, including assigned human users.
    """
    try:
        params = {
            "filters": [["id", "is", asset_id]],
            "fields": ["id", "content", "task_assignees"],
        }
        tasks = await SG._post_request("/entity/assets/_search", json=params)
        if not tasks:
            return f"No tasks found for asset {asset_id}."
        lines = []
        for t in tasks:
            tid = t.get("id")
            tname = t.get("attributes", {}).get("content", "(no name)")
            assignees = t.get("attributes", {}).get("task_assignees", [])
            if not assignees:
                lines.append(f"Task {tid}: {tname} | Assigned to: (none)")
            else:
                for user in assignees:
                    uname = user.get("attributes", {}).get("name", "(no name)")
                    uid = user.get("id")
                    lines.append(
                        f"Task {tid}: {tname} | Assigned to: {uname} (id: {uid})"
                    )
        return "\n".join(lines)
    except Exception as e:
        return f"Error listing tasks with assignees: {e}"


def post_method_searh_entity_with_array_format_body(
    entity_type: ALL_ENTITY_TYPES, body: Dict[str, Any]
):
    with httpx.Client(headers=ARRAY_HEADER) as client:
        response = client.post(
            f"{SG.api_host}/entity/{entity_type}/_search", json=body, auth=SG.auth
        )
        data = response.json()["data"]
        return data


def post_method_searh_entity_with_hash_format_body(
    entity_type: ALL_ENTITY_TYPES, body: Dict[str, Any]
):
    with httpx.Client(headers=HASH_HEADER) as client:
        response = client.post(
            f"{SG.api_host}/entity/{entity_type}/_search", json=body, auth=SG.auth
        )
        data = response.json()["data"]
        return data


def remove_exclude_fields(data: Dict) -> Dict:
    for exclude_key in EXCLUDE_KEYS:
        if exclude_key in data["attributes"].keys():
            del data["attributes"][exclude_key]
    return data


def sort_data(data: Dict) -> str:
    result_string_list = list()
    for key in data.keys():
        if key in EXPLAIN_FIELDS:
            result_string_list.append(f"{EXPLAIN_FIELDS[key]}: {data[key]}")
    return "\n".join(result_string_list)


def sort_data_to_dict(data: Dict) -> Dict:
    result_string_dict = dict()
    for key in data.keys():
        if key in EXPLAIN_FIELDS:
            result_string_dict[EXPLAIN_FIELDS[key]] = data[key]
    return result_string_dict


def sort_list_data(data: List):
    result_string_list = list()
    for idx, element in enumerate(data):
        result_string_list.append(f"{str(idx+1)}.\n" + sort_data(element))
    return "\n".join(result_string_list)


def sort_relationships(relationships: Dict):
    result_string_list = list()
    for rel in EXPLAIN_RELS:
        result_string_list.append(f"{EXPLAIN_RELS[rel]}: {relationships[rel]}")
    return result_string_list


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("-host", "--host", type=str, help="host address")
    parser.add_argument("-ci", "--client-id", type=str, help="client-id")
    parser.add_argument("-cs", "--client-secret", type=str, help="client-secret")
    args = parser.parse_args()
    SG.set_host(args.host)
    SG.access_token(client_id=args.client_id, client_secret=args.client_secret)
    mcp.run(transport="stdio")
    # res = asyncio.run(get_asset_by_id(1405))
    # print(res, type(res))
