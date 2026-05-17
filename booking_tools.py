import httpx
from typing import List, Dict, Optional, Union, Literal

BOOKING_STATUS = Literal["cfrm", "pndng"]

from shotgrid_rest import ShotGridRest


async def _handle_errors(coro):
    try:
        return await coro
    except httpx.HTTPStatusError as e:
        return {"error": f"ShotGrid API Error: {e.response.status_code}", "message": e.response.text}
    except Exception as e:
        return {"error": "Internal Server Error", "message": str(e)}


def register_booking_tools(mcp, sg: ShotGridRest):

    @mcp.tool()
    async def get_bookings(
        user_id: Optional[int] = None,
        project_id: Optional[int] = None,
        start_date_from: Optional[List[int]] = None,
        start_date_to: Optional[List[int]] = None,
        end_date_from: Optional[List[int]] = None,
        end_date_to: Optional[List[int]] = None,
        vacation: Optional[bool] = None,
    ) -> Union[List[Dict], Dict]:
        """Retrieve bookings in ShotGrid with various filters."""
        filters = []
        if vacation is not None:
            filters.append(["vacation", "is", vacation])
        if user_id is not None:
            filters.append(["user.HumanUser.id", "is", user_id])
        if project_id is not None:
            filters.append(["project.Project.id", "is", project_id])
        if start_date_from:
            filters.append(["start_date", "greater_than", f"{start_date_from[0]:04}-{start_date_from[1]:02}-{start_date_from[2]:02}"])
        if start_date_to:
            filters.append(["start_date", "less_than", f"{start_date_to[0]:04}-{start_date_to[1]:02}-{start_date_to[2]:02}"])
        if end_date_from:
            filters.append(["end_date", "greater_than", f"{end_date_from[0]:04}-{end_date_from[1]:02}-{end_date_from[2]:02}"])
        if end_date_to:
            filters.append(["end_date", "less_than", f"{end_date_to[0]:04}-{end_date_to[1]:02}-{end_date_to[2]:02}"])
        fields = ["user", "updated_at", "project", "vacation", "sg_status_list", "percent_allocation", "start_date", "end_date", "note"]

        async def _call():
            resp = await sg.post_request("/entity/bookings/_search", json={"filters": filters, "fields": fields})
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
        data: Dict = {
            "user": {"type": "HumanUser", "id": user_id},
            "project": {"type": "Project", "id": project_id},
            "start_date": f"{start_date[0]:04}-{start_date[1]:02}-{start_date[2]:02}",
            "end_date": f"{end_date[0]:04}-{end_date[1]:02}-{end_date[2]:02}",
            "vacation": vacation,
        }
        if note is not None:
            data["note"] = note
        if percent_allocation is not None:
            data["percent_allocation"] = percent_allocation
        if sg_status_list is not None:
            data["sg_status_list"] = sg_status_list

        async def _call():
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
        data: Dict = {}
        if start_date is not None:
            data["start_date"] = f"{start_date[0]:04}-{start_date[1]:02}-{start_date[2]:02}"
        if end_date is not None:
            data["end_date"] = f"{end_date[0]:04}-{end_date[1]:02}-{end_date[2]:02}"
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

        async def _call():
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
