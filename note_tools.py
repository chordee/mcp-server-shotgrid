import logging
import httpx
from datetime import date
from typing import List, Dict, Optional, Union

from shotgrid_rest import ShotGridRest

logger = logging.getLogger(__name__)


NOTE_FIELDS = [
    "user", "cached_display_name", "subject", "content", "sg_status_list",
    "tasks", "addressings_to", "addressings_cc", "note_links", "attachments",
    "client_note", "created_at", "updated_at",
]

REPLY_FIELDS = [
    "content", "user", "entity", "created_at", "updated_at",
    "attachments", "sg_status_list",
]

ATTACHMENT_FIELDS = [
    "this_file", "image", "display_name", "filename", "file_size",
    "content_type", "attachment_links", "tag_list",
    "created_at", "updated_at",
]


def _to_iso_date(parts: List[int], field_name: str) -> str:
    if not isinstance(parts, list) or len(parts) != 3:
        raise ValueError(f"{field_name} must be [YYYY, MM, DD].")
    try:
        return date(int(parts[0]), int(parts[1]), int(parts[2])).isoformat()
    except (TypeError, ValueError) as e:
        raise ValueError(f"{field_name} must be a valid [YYYY, MM, DD] date.") from e


def _refs(entity_type: str, ids: Optional[List[int]]) -> List[Dict]:
    return [{"type": entity_type, "id": int(i)} for i in (ids or [])]


async def _handle_errors(coro):
    try:
        return await coro
    except ValueError as e:
        logger.info("Note tool validation error: %s", e)
        return {"error": "Invalid input", "message": str(e)}
    except httpx.HTTPStatusError as e:
        logger.warning("ShotGrid API error: status=%s", e.response.status_code)
        return {
            "error": f"ShotGrid API Error: {e.response.status_code}",
            "message": "Request to ShotGrid failed.",
        }
    except Exception:
        logger.exception("Unhandled note tool error")
        return {"error": "Internal Server Error", "message": "Unexpected server error."}


def register_note_tools(mcp, sg: ShotGridRest):

    @mcp.tool()
    async def get_notes(
        shot_id: Optional[int] = None,
        asset_id: Optional[int] = None,
        user_id: Optional[int] = None,
        task_id: Optional[int] = None,
        version_id: Optional[int] = None,
        project_id: Optional[int] = None,
        project_name: Optional[str] = None,
        task_name: Optional[str] = None,
        asset_code: Optional[str] = None,
        version_name: Optional[str] = None,
        updated_in_last_n_days: Optional[int] = None,
        updated_date_from: Optional[List[int]] = None,
        updated_date_to: Optional[List[int]] = None,
        limit: Optional[int] = None,
        page: Optional[int] = None,
    ) -> Union[List[Dict], Dict]:
        """Retrieve notes from ShotGrid with optional filters.

        Args:
            shot_id: Filter notes linked to this Shot.
            asset_id: Filter notes linked to this Asset.
            user_id: Filter notes addressed to this HumanUser.
            task_id: Filter notes attached to this Task.
            version_id: Filter notes linked to this Version.
            project_id: Filter by Project id.
            project_name: Substring match on project name.
            task_name: Substring match on related task content.
            asset_code: Substring match on the linked asset code.
            version_name: Substring match on the linked version code.
            updated_in_last_n_days: Restrict to notes updated in the last N
                days. Must be a positive integer.
            updated_date_from: [YYYY, MM, DD] lower bound on updated_at (strict).
            updated_date_to: [YYYY, MM, DD] upper bound on updated_at (strict).
            limit: Page size. Omit for ShotGrid's default page; supply to
                paginate large projects whose note count exceeds the default.
            page: 1-based page number. Defaults to 1 when `limit` is given;
                must not be supplied without `limit`.
        """
        async def _call():
            filters: List = []
            if shot_id:
                filters.append(["note_links", "is", {"type": "Shot", "id": shot_id}])
            if asset_id:
                filters.append(["note_links", "is", {"type": "Asset", "id": asset_id}])
            if user_id:
                filters.append(["addressings_to", "is", {"type": "HumanUser", "id": user_id}])
            if task_id:
                filters.append(["tasks", "is", {"type": "Task", "id": task_id}])
            if version_id:
                filters.append(["note_links", "is", {"type": "Version", "id": version_id}])
            if project_id:
                filters.append(["project.Project.id", "is", project_id])
            if project_name:
                filters.append(["project.Project.name", "contains", project_name])
            if task_name:
                filters.append(["tasks.Task.content", "contains", task_name])
            if asset_code:
                filters.append(["note_links.Asset.code", "contains", asset_code])
            if version_name:
                filters.append(["note_links.Version.code", "contains", version_name])
            if updated_in_last_n_days is not None:
                if updated_in_last_n_days <= 0:
                    raise ValueError("updated_in_last_n_days must be a positive integer.")
                filters.append(["updated_at", "in_last", [updated_in_last_n_days, "DAY"]])
            if updated_date_from is not None:
                filters.append(["updated_at", "greater_than",
                                _to_iso_date(updated_date_from, "updated_date_from")])
            if updated_date_to is not None:
                filters.append(["updated_at", "less_than",
                                _to_iso_date(updated_date_to, "updated_date_to")])

            payload: Dict = {"filters": filters, "fields": NOTE_FIELDS}
            if limit is not None:
                if limit <= 0:
                    raise ValueError("limit must be positive.")
                if page is not None and page <= 0:
                    raise ValueError("page must be >= 1.")
                payload["page"] = {"size": limit, "number": page if page is not None else 1}
            elif page is not None:
                raise ValueError("page requires limit.")

            resp = await sg.post_request("/entity/notes/_search", json=payload)
            return resp.get("data", [])

        return await _handle_errors(_call())

    @mcp.tool()
    async def create_note(
        content: str,
        project_id: int,
        subject: Optional[str] = None,
        link_shot_ids: Optional[List[int]] = None,
        link_asset_ids: Optional[List[int]] = None,
        link_task_ids: Optional[List[int]] = None,
        link_version_ids: Optional[List[int]] = None,
        task_ids: Optional[List[int]] = None,
        addressing_to_user_ids: Optional[List[int]] = None,
        addressing_cc_user_ids: Optional[List[int]] = None,
        user_id: Optional[int] = None,
        sg_status_list: Optional[str] = None,
    ) -> Union[Dict, Dict]:
        """Create a new Note in ShotGrid.

        Args:
            content: Body text of the note (required).
            project_id: Project the note belongs to (required).
            subject: Optional subject line.
            link_shot_ids / link_asset_ids / link_task_ids / link_version_ids:
                Entity ids to attach via the `note_links` multi-entity field.
            task_ids: Tasks attached to the note (separate from note_links).
            addressing_to_user_ids: HumanUser ids in the To list.
            addressing_cc_user_ids: HumanUser ids in the CC list.
            user_id: Author HumanUser id. Defaults to the API user when omitted.
            sg_status_list: Status code. Common values: "opn" (open),
                "ip" (in progress), "clsd" (closed). Site may define others.
        """
        async def _call():
            data: Dict = {
                "content": content,
                "project": {"type": "Project", "id": project_id},
            }
            if subject is not None:
                data["subject"] = subject

            note_links = (
                _refs("Shot", link_shot_ids)
                + _refs("Asset", link_asset_ids)
                + _refs("Task", link_task_ids)
                + _refs("Version", link_version_ids)
            )
            if note_links:
                data["note_links"] = note_links

            if task_ids:
                data["tasks"] = _refs("Task", task_ids)
            if addressing_to_user_ids:
                data["addressings_to"] = _refs("HumanUser", addressing_to_user_ids)
            if addressing_cc_user_ids:
                data["addressings_cc"] = _refs("HumanUser", addressing_cc_user_ids)
            if user_id is not None:
                data["user"] = {"type": "HumanUser", "id": user_id}
            if sg_status_list is not None:
                data["sg_status_list"] = sg_status_list

            resp = await sg.post_request("/entity/notes", context_type="json", json=data)
            return resp.get("data", resp)

        return await _handle_errors(_call())

    @mcp.tool()
    async def update_note(
        note_id: int,
        content: Optional[str] = None,
        subject: Optional[str] = None,
        sg_status_list: Optional[str] = None,
        link_shot_ids: Optional[List[int]] = None,
        link_asset_ids: Optional[List[int]] = None,
        link_task_ids: Optional[List[int]] = None,
        link_version_ids: Optional[List[int]] = None,
        task_ids: Optional[List[int]] = None,
        addressing_to_user_ids: Optional[List[int]] = None,
        addressing_cc_user_ids: Optional[List[int]] = None,
    ) -> Union[Dict, Dict]:
        """Update an existing Note. `project` and `user` cannot be changed via update;
        delete and recreate if those need to change.

        Multi-entity list parameters REPLACE the existing value when provided
        (ShotGrid multi-entity PUT semantics) — pass an empty list to clear.

        Important: the four `link_*` parameters all map to the single
        `note_links` field. Supplying any one of them rebuilds `note_links`
        from scratch using only the supplied entity types, which clears any
        other types already on the note. To preserve existing links of a type
        you are not modifying, fetch the note first and pass that type's ids
        back in. `task_ids` (which writes `tasks`) and the `addressing_*`
        parameters are independent of `note_links` and of each other.

        At least one editable field must be supplied.
        """
        async def _call():
            data: Dict = {}
            if content is not None:
                data["content"] = content
            if subject is not None:
                data["subject"] = subject
            if sg_status_list is not None:
                data["sg_status_list"] = sg_status_list

            if any(x is not None for x in (link_shot_ids, link_asset_ids,
                                            link_task_ids, link_version_ids)):
                data["note_links"] = (
                    _refs("Shot", link_shot_ids)
                    + _refs("Asset", link_asset_ids)
                    + _refs("Task", link_task_ids)
                    + _refs("Version", link_version_ids)
                )
            if task_ids is not None:
                data["tasks"] = _refs("Task", task_ids)
            if addressing_to_user_ids is not None:
                data["addressings_to"] = _refs("HumanUser", addressing_to_user_ids)
            if addressing_cc_user_ids is not None:
                data["addressings_cc"] = _refs("HumanUser", addressing_cc_user_ids)

            if not data:
                return {"error": "No fields to update",
                        "message": "Provide at least one editable field."}

            resp = await sg.put_request(f"/entity/notes/{note_id}", json=data)
            return resp.get("data", resp)

        return await _handle_errors(_call())

    @mcp.tool()
    async def delete_note(note_id: int) -> Dict:
        """Delete a Note from ShotGrid by its ID."""
        async def _call():
            status = await sg.delete_request(f"/entity/notes/{note_id}")
            return {"success": True, "status_code": status}

        return await _handle_errors(_call())

    @mcp.tool()
    async def get_replies(
        note_id: int,
        limit: Optional[int] = None,
        page: Optional[int] = None,
    ) -> Union[List[Dict], Dict]:
        """List replies under a Note, returning full reply fields
        (content, user, entity, timestamps, attachments).

        Args:
            note_id: Parent Note id (required).
            limit: Page size. Omit for ShotGrid's default page; supply to
                paginate notes whose reply count exceeds the default.
            page: 1-based page number. Defaults to 1 when `limit` is given;
                must not be supplied without `limit`.
        """
        async def _call():
            payload: Dict = {
                "filters": [["entity", "is", {"type": "Note", "id": note_id}]],
                "fields": REPLY_FIELDS,
            }
            if limit is not None:
                if limit <= 0:
                    raise ValueError("limit must be positive.")
                if page is not None and page <= 0:
                    raise ValueError("page must be >= 1.")
                payload["page"] = {"size": limit, "number": page if page is not None else 1}
            elif page is not None:
                raise ValueError("page requires limit.")

            resp = await sg.post_request("/entity/replies/_search", json=payload)
            return resp.get("data", [])

        return await _handle_errors(_call())

    @mcp.tool()
    async def create_reply(
        content: str,
        note_id: int,
        user_id: Optional[int] = None,
    ) -> Union[Dict, Dict]:
        """Post a Reply under the given Note.

        Args:
            content: Reply body (required).
            note_id: Parent Note id (required).
            user_id: Author HumanUser id. Defaults to the API user when omitted.
        """
        async def _call():
            data: Dict = {
                "content": content,
                "entity": {"type": "Note", "id": note_id},
            }
            if user_id is not None:
                data["user"] = {"type": "HumanUser", "id": user_id}
            resp = await sg.post_request("/entity/replies", context_type="json", json=data)
            return resp.get("data", resp)

        return await _handle_errors(_call())

    @mcp.tool()
    async def update_reply(reply_id: int, content: str) -> Union[Dict, Dict]:
        """Update an existing Reply's content."""
        async def _call():
            resp = await sg.put_request(
                f"/entity/replies/{reply_id}", json={"content": content},
            )
            return resp.get("data", resp)

        return await _handle_errors(_call())

    @mcp.tool()
    async def delete_reply(reply_id: int) -> Dict:
        """Delete a Reply from ShotGrid by its ID."""
        async def _call():
            status = await sg.delete_request(f"/entity/replies/{reply_id}")
            return {"success": True, "status_code": status}

        return await _handle_errors(_call())

    @mcp.tool()
    async def get_note_attachments(note_id: int) -> Union[List[Dict], Dict]:
        """List attachment references on a Note. Returns lightweight
        [{id, type, name}] entries — call `get_attachment_info(attachment_id)`
        for download URL, filename, content type, and thumbnail."""
        async def _call():
            resp = await sg.get_request(
                f"/entity/notes/{note_id}", params={"fields": "attachments"},
            )
            data = resp.get("data", {})
            atts = (
                data.get("relationships", {})
                    .get("attachments", {})
                    .get("data", [])
            )
            return atts

        return await _handle_errors(_call())

    @mcp.tool()
    async def get_attachment_info(attachment_id: int) -> Union[Dict, Dict]:
        """Fetch full metadata for a single Attachment: download URL
        (`this_file`), thumbnail (`image`), display name, content type,
        size, and back-references."""
        async def _call():
            resp = await sg.get_request(
                f"/entity/attachments/{attachment_id}",
                params={"fields": ",".join(ATTACHMENT_FIELDS)},
            )
            return resp.get("data", resp)

        return await _handle_errors(_call())
