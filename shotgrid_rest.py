import httpx
from typing import Dict, Any, Optional, Literal, List, Union
from httpx_auth import OAuth2ClientCredentials
from dataclasses import dataclass


class ShotGridRest:
    def __init__(self):
        """
        Initialize a new ShotGridRest instance with default (None) connection and authentication attributes.
        """
        self.host = None
        self.auth = None
        self.client_id = None
        self.client_secret = None
        self.api_host = None

    def set_host(self, host: str, version: str = "1.1") -> None:
        """
        Set the ShotGrid API host and version.

        Args:
            host (str): The base URL of the ShotGrid server (e.g., "https://your-shotgrid-site.com").
            version (str, optional): The API version to use. Defaults to "1.1".

        Sets:
            self.host: The base host URL.
            self.api_host: The full API endpoint including version.
        """
        self.host = host
        self.api_host = f"{self.host}/api/v{version}"

    def access_token(self, client_id: str, client_secret: str) -> None:
        """
        Obtain and set the OAuth2 access token for authenticating with the ShotGrid API.

        Args:
            client_id (str): The client ID for the ShotGrid API application.
            client_secret (str): The client secret for the ShotGrid API application.

        Sets:
            self.auth: The OAuth2 authentication object used for API requests.
            self.client_id: Stores the provided client ID.
            self.client_secret: Stores the provided client secret.

        Prints:
            The state of the authentication process for debugging purposes.
        """
        self.client_id = client_id
        self.client_secret = client_secret
        print("Token accessing...")
        self.auth = OAuth2ClientCredentials(
            f"{self.host}/api/v1.1/auth/access_token",
            client_id=self.client_id,
            client_secret=self.client_secret,
        )
        print("Result:", self.auth.state)

    async def post_request(
        self,
        path: str,
        context_type: Literal["array", "hash"] = "array",
        json: Optional[Dict[str, Any]] = None,
    ):
        """
        Send an asynchronous POST request to the ShotGrid API with OAuth2 authentication.

        Args:
            path (str): The API endpoint path to append to the base API host URL.
            json (Optional[Dict[str, Any]]): The JSON payload to include in the POST request body.

        Returns:
            dict: The JSON-decoded response from the ShotGrid API.
        """
        url = f"{self.api_host}{path}"
        headers = {
            "Content-Type": (
                "application/vnd+shotgun.api3_array+json"
                if context_type == "array"
                else "application/vnd+shotgun.api3_hash+json"
            )
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=json, headers=headers, auth=self.auth)
            resp.raise_for_status()
            return resp.json()

    async def _fetch_entity_fields(self, entity_type):
        """
        Fetch all field names for a given ShotGrid entity type.

        Args:
            entity_type (str): The type of entity (e.g., "projects", "shots", "assets").

        Returns:
            KeysView: A view of the field names (keys) for the specified entity type.
        """
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.api_host}/schema/{entity_type}/fields", auth=self.auth
            )
            data = resp.json().get("data", [])
            return data.keys()


ARRAY_HEADER = {"Content-Type": "application/vnd+shotgun.api3_array+json"}
HASH_HEADER = {"Content-Type": "application/vnd+shotgun.api3_hash+json"}

EXCLUDE_KEYS = (
    "sg_know_how",
    "tracking_settings",
    "filmstrip_image",
    "sg_uploaded_movie_mp4",
    "sg_uploaded_movie",
    "sg_uploaded_movie_webm",
    "sg_uploaded_movie_transcoding_status",
    "bookings",
)

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
    "replies",
    "attachments",
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

FILTER_RELS = Literal[
    "is",  # [field_value] | None,
    "is_not",  # [field_value] | None
    "less_than",  # [field_value] | None
    "greater_than",  # [field_value] | None
    "contains",  # [field_value] | None
    "not_contains",  # [field_value] | None
    "starts_with",  # [string]
    "ends_with",  # [string]
    "between",  # [[field_value] | None, [field_value] | None]
    "not_between",  # [[field_value] | None, [field_value] | None]
    "in_last",  # [[int], 'HOUR' | 'DAY' | 'WEEK' | 'MONTH' | 'YEAR']
    # note that brackets are literal (eg. ['start_date', 'in_last', [1, 'DAY']])
    "in_next",  # [[int], 'HOUR' | 'DAY' | 'WEEK' | 'MONTH' | 'YEAR']
    # note that brackets are literal (eg. ['start_date', 'in_next', [1, 'DAY']])
    "in",  # [[field_value] | None, ...] # Array of field values
    "type_is",  # [string] | None # Flow Production Tracking entity type
    "type_is_not",  # [string] | None # Flow Production Tracking entity type
    "in_calendar_day",  # [int] # Offset (e.g. 0 = today, 1 = tomorrow, -1 = yesterday)
    "in_calendar_week",  # [int] # Offset (e.g. 0 = this week, 1 = next week, -1 = last week)
    "in_calendar_month",  # [int] # Offset (e.g. 0 = this month, 1 = next month, -1 = last month)
    "name_contains",  # [string]
    "name_not_contains",  # [string]
    "name_starts_with",  # [string]
    "name_ends_with",  # [string]
]


@dataclass
class Filter:
    """
    Represents a single filter condition for ShotGrid API queries.

    Attributes:
        field (str): The name of the field to filter on.
        relation (str): The comparison operator or relation (e.g., 'is', 'contains', 'greater_than').
        value (str): The value to compare the field against.

    Methods:
        to_list(): Returns the filter as a list [field, relation, value], suitable for API requests.
        __repr__(): Returns a string representation for debugging.
        __str__(): Returns a human-readable string representation.
    """

    field: str
    relation: FILTER_RELS
    value: Any

    def to_list(self):
        return [self.field, self.relation, self.value]

    def __repr__(self):
        return (
            f"Filter(field={self.field}, relation={self.relation}, value={self.value})"
        )

    def __str__(self):
        return f"Filter: {self.field} {self.relation} {self.value}"


@dataclass
class Filters:
    """
    Represents a collection of filter conditions for ShotGrid API queries,
    optionally combined with a logical operator.

    Attributes:
        conditions (List[Filter]): A list of Filter objects representing individual filter conditions.
        logical_operator (Optional[str]): The logical operator to combine conditions (e.g., 'and', 'or').

    Methods:
        to_dict(): Converts the Filters object to a dictionary suitable for API requests.
        __repr__(): Returns a string representation for debugging.
        __str__(): Returns a human-readable string representation.
    """

    conditions: List[Union[Filter, "Filters"]]
    logical_operator: Optional[str]

    def to_dict(self):
        """
        Convert the Filters object to a dictionary suitable for ShotGrid API requests.
        Handles nested Filters objects by recursively calling to_dict.

        Returns:
            dict: Dictionary representation of the Filters object.
        """
        result = dict()
        if self.logical_operator:
            result["logical_operator"] = self.logical_operator
        result["conditions"] = [
            f.to_dict() if isinstance(f, Filters) else f.to_list()
            for f in self.conditions
        ]
        return result

    def __repr__(self):
        return f"Filters(conditions={self.conditions}, logical_operator={self.logical_operator})"

    def __str__(self):
        conditions_str = ", ".join([str(f) for f in self.conditions])
        return f"Filters(conditions=[{conditions_str}], logical_operator={self.logical_operator})"
