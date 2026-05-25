from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, model_validator

from config import EMPTY_OPERATORS

FieldName = Literal[
    "number",
    "short_description",
    "assignment_group",
    "caller",
    "assigned_to",
    "state",
    "active",
    "created",
]

Operator = Literal[
    "is",
    "contains",
    "on_or_after",
    "on_or_before",
    "is_empty",
    "is_not_empty",
]


class SearchCondition(BaseModel):
    join: Optional[Literal["and", "or"]] = None
    field: FieldName
    operator: Operator
    value: str = ""

    @model_validator(mode="after")
    def validate_value_for_operator(self) -> "SearchCondition":
        if self.operator in EMPTY_OPERATORS:
            self.value = ""
            return self
        if not self.value.strip():
            raise ValueError("value is required for this operator")
        return self


class ConditionGroup(BaseModel):
    conditions: List[SearchCondition] = Field(..., min_length=1)


class SearchRequest(BaseModel):
    groups: List[ConditionGroup] = Field(..., min_length=1)


class ExportRequest(BaseModel):
    incidents: List[Dict[str, Any]] = Field(..., min_length=1)
