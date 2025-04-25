from typing import Literal

GENERAL_FIELDS = [
    "name",
    "updated_at",
    "sg_status_list",
    "project",
    "code",
    "user",
    "id",
    "tasks",
    "content",
    "cached_display_name",
]

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
    # note that brackets are literal (eg. ['start_date', 'in_next', [1, 'DAY']])
    "in_next",  # [[int], 'HOUR' | 'DAY' | 'WEEK' | 'MONTH' | 'YEAR']
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
