from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from config import STATIC_DIR
from export_utils import build_export_response
from models import ExportRequest, SearchRequest
from query_builder import build_groups_from_legacy_params, build_query_from_groups
from servicenow_client import search_incidents

load_dotenv(Path(__file__).resolve().parent / ".env")

app = FastAPI(title="ServiceNow Incidents", version="1.0.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def root() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/search")
async def search_incidents_post(request: SearchRequest):
    sysparm_query = build_query_from_groups(request.groups)
    incidents = search_incidents(sysparm_query)
    return {
        "groups": [
            {"conditions": [condition.model_dump() for condition in group.conditions]}
            for group in request.groups
        ],
        "sysparm_query": sysparm_query,
        "count": len(incidents),
        "incidents": incidents,
    }


@app.get("/search")
async def search_incidents_get(
    q: Optional[str] = Query(None, description="Incident number or short description"),
    assignment_group: Optional[str] = Query(None, description="Assignment group name"),
    caller: Optional[str] = Query(None, description="Caller name"),
    assigned_to: Optional[str] = Query(None, description="Assigned to user name"),
    state: Optional[str] = Query(None, description="Incident state"),
    active: Optional[str] = Query(None, description="Active flag"),
    created_from: Optional[str] = Query(None, description="Created on or after (YYYY-MM-DD)"),
    created_to: Optional[str] = Query(None, description="Created on or before (YYYY-MM-DD)"),
):
    filters = {
        "q": q,
        "assignment_group": assignment_group,
        "caller": caller,
        "assigned_to": assigned_to,
        "state": state,
        "active": active,
        "created_from": created_from,
        "created_to": created_to,
    }
    groups = build_groups_from_legacy_params(
        q=q,
        assignment_group=assignment_group,
        caller=caller,
        assigned_to=assigned_to,
        state=state,
        active=active,
        created_from=created_from,
        created_to=created_to,
    )
    sysparm_query = build_query_from_groups(groups)
    incidents = search_incidents(sysparm_query)
    return {
        "filters": {key: value for key, value in filters.items() if value is not None},
        "sysparm_query": sysparm_query,
        "count": len(incidents),
        "incidents": incidents,
    }


@app.post("/export")
async def export_incidents(request: ExportRequest):
    return build_export_response(request.incidents)
