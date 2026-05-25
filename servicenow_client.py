import os
from typing import Dict, List, Optional, Tuple

import requests
from fastapi import HTTPException

from config import INCIDENT_FIELDS, INCIDENT_OUTPUT_FIELDS


def get_servicenow_config() -> Tuple[str, str, str]:
    env_vars = {
        "SN_INSTANCE": os.getenv("SN_INSTANCE"),
        "SN_USER": os.getenv("SN_USER"),
        "SN_PASSWORD": os.getenv("SN_PASSWORD"),
    }
    missing = [name for name, value in env_vars.items() if not value]
    if missing:
        raise HTTPException(
            status_code=500,
            detail=f"Missing required environment variables: {', '.join(missing)}",
        )
    return env_vars["SN_INSTANCE"], env_vars["SN_USER"], env_vars["SN_PASSWORD"]


def build_instance_url(instance: str) -> str:
    instance = instance.strip().rstrip("/")
    if instance.startswith(("http://", "https://")):
        return instance
    if ".service-now.com" in instance:
        return f"https://{instance}"
    return f"https://{instance}.service-now.com"


def extract_field(record: dict, field: str) -> Optional[str]:
    value = record.get(field)
    if isinstance(value, dict):
        return value.get("display_value") or value.get("value")
    return value


def format_incident(record: dict) -> Dict[str, Optional[str]]:
    return {
        output_key: extract_field(record, source_key)
        for output_key, source_key in INCIDENT_OUTPUT_FIELDS
    }


def query_servicenow(sysparm_query: str) -> List[dict]:
    instance, user, password = get_servicenow_config()
    url = f"{build_instance_url(instance)}/api/now/table/incident"
    params = {
        "sysparm_query": sysparm_query,
        "sysparm_fields": INCIDENT_FIELDS,
        "sysparm_display_value": "true",
        "sysparm_limit": "50",
    }

    try:
        response = requests.get(
            url,
            params=params,
            auth=(user, password),
            headers={"Accept": "application/json"},
            timeout=30,
        )
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="ServiceNow request timed out")
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=502,
            detail="Unable to connect to ServiceNow. Check SN_INSTANCE and network access.",
        )
    except requests.exceptions.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"ServiceNow request failed: {exc}")

    if response.status_code == 401:
        raise HTTPException(status_code=401, detail="ServiceNow authentication failed")
    if response.status_code == 403:
        raise HTTPException(status_code=403, detail="ServiceNow access denied")
    if not response.ok:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"ServiceNow API error: {response.text}",
        )

    try:
        payload = response.json()
    except ValueError:
        raise HTTPException(status_code=502, detail="Invalid JSON response from ServiceNow")

    return payload.get("result", [])


def search_incidents(sysparm_query: str) -> List[Dict[str, Optional[str]]]:
    return [format_incident(record) for record in query_servicenow(sysparm_query)]
