from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List

from fastapi.responses import StreamingResponse
from openpyxl import Workbook

from config import EXPORT_COLUMNS


def build_incidents_workbook(incidents: List[Dict[str, Any]]) -> BytesIO:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Incidents"
    worksheet.append([header for _, header in EXPORT_COLUMNS])

    for incident in incidents:
        worksheet.append([incident.get(field, "") or "" for field, _ in EXPORT_COLUMNS])

    for column in worksheet.columns:
        max_length = max(len(str(cell.value or "")) for cell in column)
        worksheet.column_dimensions[column[0].column_letter].width = min(max_length + 2, 50)

    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer


def build_export_response(incidents: List[Dict[str, Any]]) -> StreamingResponse:
    buffer = build_incidents_workbook(incidents)
    filename = f"incidents_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )
