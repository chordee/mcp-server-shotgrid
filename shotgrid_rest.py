import httpx
import logging
from typing import Dict, Any, Optional, Literal, List, Union
from httpx_auth import OAuth2ClientCredentials
from dataclasses import dataclass
from shotgrid_options import (
    ARRAY_HEADER,
    HASH_HEADER,
    FILTER_RELS,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


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
        self._client: Optional[httpx.AsyncClient] = None
        self._schema_cache: Dict[str, List[str]] = {}

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create the shared httpx.AsyncClient instance with no proxies."""
        if self._client is None or self._client.is_closed:
            # Set a more generous timeout
            timeout = httpx.Timeout(60.0, connect=10.0)
            # Use proxy=None and trust_env=False to bypass system proxies completely
            # since moonshine.shotgunstudio.com is internal.
            self._client = httpx.AsyncClient(
                timeout=timeout, 
                proxy=None, 
                trust_env=False
            )
        return self._client

    async def close(self):
        """Close the underlying httpx client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def set_host(self, host: str, version: str = "1.1") -> None:
        """Set the ShotGrid host URL and API version."""
        self.host = host.rstrip("/")
        self.api_host = f"{self.host}/api/v{version}"

    def access_token(self, client_id: str, client_secret: str) -> None:
        """
        Obtain and set the OAuth2 access token for authenticating with the ShotGrid API.
        """
        self.client_id = client_id
        self.client_secret = client_secret
        logger.info("Token accessing...")
        self.auth = OAuth2ClientCredentials(
            f"{self.host}/api/v1.1/auth/access_token",
            client_id=self.client_id,
            client_secret=self.client_secret,
        )
        # Use proper logging syntax
        logger.info("Auth state initialized: %s", getattr(self.auth, "state", "unknown"))

    async def post_request(
        self,
        path: str,
        context_type: Literal["array", "hash", "json"] = "array",
        json: Optional[Dict[str, Any]] = None,
    ):
        """
        Send an asynchronous POST request using the shared client.
        context_type: "array" / "hash" for ShotGrid search endpoints; "json" for entity create.
        """
        url = f"{self.api_host}{path}"
        if context_type == "array":
            content_type = ARRAY_HEADER["Content-Type"]
        elif context_type == "hash":
            content_type = HASH_HEADER["Content-Type"]
        else:
            content_type = "application/json"
        headers = {"Content-Type": content_type}
        client = self._get_client()
        resp = await client.post(url, json=json, headers=headers, auth=self.auth)
        resp.raise_for_status()
        return resp.json()

    async def get_request(self, path: str, params: Optional[Dict[str, Any]] = None):
        """
        Send an asynchronous GET request using the shared client.
        """
        url = f"{self.api_host}{path}"
        client = self._get_client()
        resp = await client.get(url, params=params, auth=self.auth)
        resp.raise_for_status()
        return resp.json()

    async def put_request(self, path: str, json: Optional[Dict[str, Any]] = None):
        """Send an asynchronous PUT request using the shared client."""
        url = f"{self.api_host}{path}"
        headers = {"Content-Type": "application/json"}
        client = self._get_client()
        resp = await client.put(url, json=json, headers=headers, auth=self.auth)
        resp.raise_for_status()
        return resp.json()

    async def delete_request(self, path: str):
        """Send an asynchronous DELETE request using the shared client."""
        url = f"{self.api_host}{path}"
        client = self._get_client()
        resp = await client.delete(url, auth=self.auth)
        resp.raise_for_status()
        return resp.status_code

    async def fetch_entity_fields(self, entity_type: str) -> List[str]:
        """
        Fetch and cache field names for a given ShotGrid entity type.
        """
        if entity_type in self._schema_cache:
            return self._schema_cache[entity_type]

        client = self._get_client()
        resp = await client.get(
            f"{self.api_host}/schema/{entity_type}/fields", auth=self.auth
        )
        resp.raise_for_status()
        fields = list(resp.json().get("data", {}).keys())
        
        if fields:
            self._schema_cache[entity_type] = fields
        return fields


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
