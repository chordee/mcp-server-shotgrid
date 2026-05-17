import logging
import httpx
from datetime import date
from typing import List, Dict, Optional, Union, Literal

from shotgrid_rest import ShotGridRest

BOOKING_STATUS = Literal["cfrm", "pndng"]

logger = logging.getLogger(__name__)


def _to_iso_date(parts: List[int], field_name: str) -> str:
    if not isinstance(parts, list) or len(parts) != 3:
        raise ValueError(f"{field_name} must be [YYYY, MM, DD].")
    try:
        return date(int(parts[0]), int(parts[1]), int(parts[2])).isoformat()
    except (TypeError, ValueError) as e:
        raise ValueError(f"{field_name} must be a valid [YYYY, MM, DD] date.") from e


async def _handle_errors(coro):
    try:
        return await coro
    except ValueError as e:
        logger.info("Booking validation error: %s", e)
        return {"error": "Invalid input", "message": str(e)}
    except httpx.HTTPStatusError as e:
        logger.warning("ShotGrid API error: status=%s", e.response.status_code)
        return {"error": f"ShotGrid API Error: {e.response.status_code}", "message": "Request to ShotGrid failed."}
    except Exception:
        logger.exception("Unhandled booking tool error")
        return {"error": "Internal Server Error", "message": "Unexpected server error."}


def register_booking_tools(mcp, sg: ShotGridRest):

    @mcp.tool()
    async def get_bookings(
        user_ids: Optional[List[int]] = None,
        project_ids: Optional[List[int]] = None,
        range_from: Optional[List[int]] = None,
        range_to: Optional[List[int]] = None,
        vacation: Optional[bool] = None,
        exclude_vacation: bool = False,
        sg_status_list: Optional[BOOKING_STATUS] = None,
        sort_field: Literal["start_date", "end_date", "updated_at"] = "start_date",
        sort_order: Literal["asc", "desc"] = "asc",
        limit: Optional[int] = None,
        page: Optional[int] = None,
    ) -> Union[List[Dict], Dict]:
        """Retrieve bookings whose date interval overlaps [range_from, range_to].

        Args:
            user_ids: Filter to bookings owned by any of these HumanUser IDs.
            project_ids: Filter to bookings on any of these Project IDs.
            range_from: Start of query range as [YYYY, MM, DD] (inclusive).
            range_to: End of query range as [YYYY, MM, DD] (inclusive).
                Overlap semantics: a booking [bs, be] is returned iff
                bs <= range_to AND be >= range_from.
            vacation: Exact match on the vacation flag (True or False).
            exclude_vacation: Shortcut for vacation=False. Ignored when
                `vacation` is also provided.
            sg_status_list: Filter by status ("cfrm" or "pndng").
            sort_field: Field to sort by (default "start_date").
            sort_order: "asc" or "desc" (default "asc").
            limit: Page size. Omit to fetch without pagination.
            page: 1-based page number. Defaults to 1 when `limit` is given.
        """
        fields = ["user", "updated_at", "project", "vacation", "sg_status_list", "percent_allocation", "start_date", "end_date", "note"]
        SENTINEL_PAST = "1900-01-01"
        SENTINEL_FUTURE = "9999-12-31"

        async def _call():
            filters: List = []

            if user_ids:
                filters.append(["user.HumanUser.id", "in", user_ids])
            if project_ids:
                filters.append(["project.Project.id", "in", project_ids])

            if vacation is not None:
                filters.append(["vacation", "is", vacation])
                if exclude_vacation:
                    logger.warning("Both 'vacation' and 'exclude_vacation' given; 'vacation' takes precedence.")
            elif exclude_vacation:
                filters.append(["vacation", "is", False])

            if sg_status_list is not None:
                filters.append(["sg_status_list", "is", sg_status_list])

            range_from_iso = _to_iso_date(range_from, "range_from") if range_from is not None else None
            range_to_iso = _to_iso_date(range_to, "range_to") if range_to is not None else None

            if range_from_iso and range_to_iso and range_from_iso > range_to_iso:
                raise ValueError("range_from must be <= range_to.")

            if range_to_iso is not None:
                filters.append(["start_date", "between", [SENTINEL_PAST, range_to_iso]])
            if range_from_iso is not None:
                filters.append(["end_date", "between", [range_from_iso, SENTINEL_FUTURE]])

            sort_str = sort_field if sort_order == "asc" else f"-{sort_field}"
            payload: Dict = {
                "filters": filters,
                "fields": fields,
                "sort": sort_str,
            }
            if limit is not None:
                if limit <= 0:
                    raise ValueError("limit must be positive.")
                payload["page"] = {"size": limit, "number": page or 1}

            resp = await sg.post_request("/entity/bookings/_search", json=payload)
            return resp.get("data", [])

        return await _handle_errors(_call())

    @mcp.tool()
    async def create_booking(
        user_id: int,
        project_id: int,
        start_date: List[int],
        end_date: List[int],
        vacation: bool = False,
        note: Optional[str] = None,
        percent_allocation: Optional[float] = None,
        sg_status_list: Optional[BOOKING_STATUS] = None,
    ) -> Union[Dict, Dict]:
        """Create a new booking in ShotGrid.

        Args:
            user_id: HumanUser ID.
            project_id: Project ID.
            start_date: Start date as [YYYY, MM, DD].
            end_date: End date as [YYYY, MM, DD].
            vacation: Whether this is a vacation booking (default False).
            note: Optional note string.
            percent_allocation: Work allocation percentage (0-100, default 100).
            sg_status_list: Status, either "cfrm" (Confirmed) or "pndng" (Pending).
        """
        if percent_allocation is not None and not (0 <= percent_allocation <= 100):
            return {"error": "Invalid percent_allocation", "message": "percent_allocation must be between 0 and 100."}

        async def _call():
            data: Dict = {
                "user": {"type": "HumanUser", "id": user_id},
                "project": {"type": "Project", "id": project_id},
                "start_date": _to_iso_date(start_date, "start_date"),
                "end_date": _to_iso_date(end_date, "end_date"),
                "vacation": vacation,
            }
            if note is not None:
                data["note"] = note
            if percent_allocation is not None:
                data["percent_allocation"] = percent_allocation
            if sg_status_list is not None:
                data["sg_status_list"] = sg_status_list
            resp = await sg.post_request("/entity/bookings", context_type="json", json=data)
            return resp.get("data", resp)

        return await _handle_errors(_call())

    @mcp.tool()
    async def update_booking(
        booking_id: int,
        start_date: Optional[List[int]] = None,
        end_date: Optional[List[int]] = None,
        vacation: Optional[bool] = None,
        note: Optional[str] = None,
        percent_allocation: Optional[float] = None,
        sg_status_list: Optional[BOOKING_STATUS] = None,
    ) -> Union[Dict, Dict]:
        """Update an existing booking in ShotGrid.

        Args:
            booking_id: The ID of the booking to update.
            start_date: New start date as [YYYY, MM, DD], or None to leave unchanged.
            end_date: New end date as [YYYY, MM, DD], or None to leave unchanged.
            vacation: New vacation flag, or None to leave unchanged.
            note: New note string, or None to leave unchanged.
            percent_allocation: Work allocation percentage (0-100), or None to leave unchanged.
            sg_status_list: Status "cfrm" (Confirmed) or "pndng" (Pending), or None to leave unchanged.
        """
        if percent_allocation is not None and not (0 <= percent_allocation <= 100):
            return {"error": "Invalid percent_allocation", "message": "percent_allocation must be between 0 and 100."}

        async def _call():
            data: Dict = {}
            if start_date is not None:
                data["start_date"] = _to_iso_date(start_date, "start_date")
            if end_date is not None:
                data["end_date"] = _to_iso_date(end_date, "end_date")
            if vacation is not None:
                data["vacation"] = vacation
            if note is not None:
                data["note"] = note
            if percent_allocation is not None:
                data["percent_allocation"] = percent_allocation
            if sg_status_list is not None:
                data["sg_status_list"] = sg_status_list
            if not data:
                return {"error": "No fields to update", "message": "Provide at least one field to update."}
            resp = await sg.put_request(f"/entity/bookings/{booking_id}", json=data)
            return resp.get("data", resp)

        return await _handle_errors(_call())

    @mcp.tool()
    async def delete_booking(booking_id: int) -> Dict:
        """Delete a booking from ShotGrid by its ID."""
        async def _call():
            status = await sg.delete_request(f"/entity/bookings/{booking_id}")
            return {"success": True, "status_code": status}

        return await _handle_errors(_call())
