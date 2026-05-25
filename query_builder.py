from typing import List, Optional

from fastapi import HTTPException

from config import FIELD_QUERY_MAP, STATE_LABELS
from models import ConditionGroup, SearchCondition


def normalize_state(state: str) -> str:
    cleaned = state.strip()
    if cleaned.isdigit():
        return cleaned
    return STATE_LABELS.get(cleaned.lower(), cleaned)


def normalize_active(active: str) -> str:
    normalized = active.strip().lower()
    if normalized in {"true", "1", "yes", "active"}:
        return "true"
    if normalized in {"false", "0", "no", "inactive"}:
        return "false"
    raise HTTPException(
        status_code=400,
        detail="active must be true/false, yes/no, or active/inactive",
    )


def normalize_date(date_str: str, *, end_of_day: bool = False) -> str:
    cleaned = date_str.strip()
    if len(cleaned) == 10:
        return f"{cleaned} 23:59:59" if end_of_day else f"{cleaned} 00:00:00"
    return cleaned


def _join_query_parts(parts: List[str], joins: List[str]) -> str:
    query = parts[0]
    for join, part in zip(joins, parts[1:]):
        separator = "^OR" if join == "or" else "^"
        query = f"{query}{separator}{part}"
    return query


def condition_to_query_part(condition: SearchCondition) -> str:
    field = FIELD_QUERY_MAP[condition.field]
    operator = condition.operator

    if operator == "is_empty":
        return f"{field}ISEMPTY"
    if operator == "is_not_empty":
        return f"{field}ISNOTEMPTY"

    value = condition.value.strip()

    if condition.field == "state":
        if operator != "is":
            raise HTTPException(status_code=400, detail="State only supports the 'is' operator")
        return f"{field}={normalize_state(value)}"

    if condition.field == "active":
        if operator != "is":
            raise HTTPException(status_code=400, detail="Active only supports the 'is' operator")
        return f"{field}={normalize_active(value)}"

    if condition.field == "created":
        if operator == "on_or_after":
            return f"{field}>={normalize_date(value)}"
        if operator == "on_or_before":
            return f"{field}<={normalize_date(value, end_of_day=True)}"
        raise HTTPException(
            status_code=400,
            detail="Created date supports 'on_or_after' or 'on_or_before'",
        )

    if operator == "is":
        return f"{field}={value}"
    if operator == "contains":
        return f"{field}LIKE{value}"

    raise HTTPException(
        status_code=400,
        detail=f"Unsupported operator '{operator}' for field '{condition.field}'",
    )


def build_group_query(conditions: List[SearchCondition]) -> str:
    if not conditions:
        raise HTTPException(status_code=400, detail="Each match set needs at least one condition")

    parts = [condition_to_query_part(condition) for condition in conditions]
    joins = [condition.join or "and" for condition in conditions[1:]]
    return _join_query_parts(parts, joins)


def build_query_from_groups(groups: List[ConditionGroup]) -> str:
    if not groups:
        raise HTTPException(status_code=400, detail="At least one match set is required")

    group_queries = [build_group_query(group.conditions) for group in groups]
    if len(group_queries) == 1:
        return group_queries[0]
    return "^NQ".join(group_queries)


def build_groups_from_legacy_params(
    q: Optional[str] = None,
    assignment_group: Optional[str] = None,
    caller: Optional[str] = None,
    assigned_to: Optional[str] = None,
    state: Optional[str] = None,
    active: Optional[str] = None,
    created_from: Optional[str] = None,
    created_to: Optional[str] = None,
) -> List[ConditionGroup]:
    conditions: List[SearchCondition] = []

    if q:
        conditions.extend(
            [
                SearchCondition(field="number", operator="is", value=q.strip()),
                SearchCondition(
                    join="or",
                    field="short_description",
                    operator="contains",
                    value=q.strip(),
                ),
            ]
        )

    optional_filters = [
        (assignment_group, "assignment_group", "contains"),
        (caller, "caller", "contains"),
        (assigned_to, "assigned_to", "contains"),
        (state, "state", "is"),
        (active, "active", "is"),
    ]

    for value, field, operator in optional_filters:
        if value:
            conditions.append(
                SearchCondition(
                    join="and" if conditions else None,
                    field=field,
                    operator=operator,
                    value=value.strip() if field != "state" else value,
                )
            )

    if created_from:
        conditions.append(
            SearchCondition(
                join="and" if conditions else None,
                field="created",
                operator="on_or_after",
                value=created_from,
            )
        )

    if created_to:
        conditions.append(
            SearchCondition(
                join="and" if conditions else None,
                field="created",
                operator="on_or_before",
                value=created_to,
            )
        )

    if not conditions:
        raise HTTPException(
            status_code=400,
            detail=(
                "Provide at least one filter: q, assignment_group, caller, "
                "assigned_to, state, active, created_from, or created_to"
            ),
        )

    return [ConditionGroup(conditions=conditions)]
