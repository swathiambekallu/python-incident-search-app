from pathlib import Path

STATIC_DIR = Path(__file__).parent / "static"

INCIDENT_FIELDS = (
    "number,short_description,state,priority,sys_id,active,sys_created_on,"
    "assignment_group,caller_id,assigned_to"
)

STATE_LABELS = {
    "new": "1",
    "in progress": "2",
    "on hold": "3",
    "resolved": "6",
    "closed": "7",
    "canceled": "8",
    "cancelled": "8",
}

FIELD_QUERY_MAP = {
    "number": "number",
    "short_description": "short_description",
    "assignment_group": "assignment_group.name",
    "caller": "caller_id.name",
    "assigned_to": "assigned_to.name",
    "state": "state",
    "active": "active",
    "created": "sys_created_on",
}

INCIDENT_OUTPUT_FIELDS = [
    ("number", "number"),
    ("short_description", "short_description"),
    ("state", "state"),
    ("priority", "priority"),
    ("active", "active"),
    ("sys_created_on", "sys_created_on"),
    ("assignment_group", "assignment_group"),
    ("caller", "caller_id"),
    ("assigned_to", "assigned_to"),
    ("sys_id", "sys_id"),
]

EXPORT_COLUMNS = [
    ("number", "Number"),
    ("short_description", "Short Description"),
    ("state", "State"),
    ("priority", "Priority"),
    ("active", "Active"),
    ("assignment_group", "Assignment Group"),
    ("caller", "Caller"),
    ("assigned_to", "Assigned To"),
    ("sys_created_on", "Created"),
    ("sys_id", "Sys ID"),
]

EMPTY_OPERATORS = {"is_empty", "is_not_empty"}
