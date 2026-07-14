from datetime import date, datetime, time
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _coerce_text(value: Any) -> str | None:
    """Accept LLM strings, lists, tuples, sets, or dictionaries as text."""
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or None
    if isinstance(value, (list, tuple, set)):
        parts = [_coerce_text(item) for item in value]
        return "; ".join(part for part in parts if part) or None
    if isinstance(value, dict):
        parts = []
        for key, item in value.items():
            text = _coerce_text(item)
            if text:
                parts.append(f"{key}: {text}")
        return "; ".join(parts) or None
    return str(value).strip() or None


class HCPRead(BaseModel):
    id: int
    name: str
    specialty: str | None = None
    institution: str | None = None

    model_config = ConfigDict(from_attributes=True)


class InteractionCreate(BaseModel):
    hcp_id: int
    interaction_type: str = "Meeting"
    interaction_date: date
    interaction_time: time | None = None
    attendees: str | None = None
    topics_discussed: str = Field(min_length=2)
    materials_shared: str | None = None
    samples_distributed: str | None = None
    sentiment: str = "Neutral"
    outcomes: str | None = None
    follow_up_actions: str | None = None
    ai_summary: str | None = None
    source: str = "form"

    @field_validator(
        "interaction_type",
        "attendees",
        "topics_discussed",
        "materials_shared",
        "samples_distributed",
        "sentiment",
        "outcomes",
        "follow_up_actions",
        "ai_summary",
        "source",
        mode="before",
    )
    @classmethod
    def normalize_text_fields(cls, value: Any):
        return _coerce_text(value)

    @field_validator("sentiment")
    @classmethod
    def normalize_sentiment(cls, value: str):
        lowered = value.lower()
        if "positive" in lowered:
            return "Positive"
        if "negative" in lowered:
            return "Negative"
        return "Neutral"


class InteractionUpdate(BaseModel):
    interaction_type: str | None = None
    interaction_date: date | None = None
    interaction_time: time | None = None
    attendees: str | None = None
    topics_discussed: str | None = None
    materials_shared: str | None = None
    samples_distributed: str | None = None
    sentiment: str | None = None
    outcomes: str | None = None
    follow_up_actions: str | None = None
    ai_summary: str | None = None

    @field_validator(
        "interaction_type",
        "attendees",
        "topics_discussed",
        "materials_shared",
        "samples_distributed",
        "sentiment",
        "outcomes",
        "follow_up_actions",
        "ai_summary",
        mode="before",
    )
    @classmethod
    def normalize_text_fields(cls, value: Any):
        return _coerce_text(value)

    @field_validator("sentiment")
    @classmethod
    def normalize_sentiment(cls, value: str | None):
        if value is None:
            return None
        lowered = value.lower()
        if "positive" in lowered:
            return "Positive"
        if "negative" in lowered:
            return "Negative"
        return "Neutral"


class InteractionRead(InteractionCreate):
    id: int
    created_at: datetime
    updated_at: datetime
    hcp: HCPRead

    model_config = ConfigDict(from_attributes=True)


class FollowUpCreate(BaseModel):
    hcp_id: int
    interaction_id: int | None = None
    due_date: date
    task: str = Field(min_length=2)

    @field_validator("task", mode="before")
    @classmethod
    def normalize_task(cls, value: Any):
        return _coerce_text(value)


class FollowUpRead(FollowUpCreate):
    id: int
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatRequest(BaseModel):
    message: str = Field(min_length=2)


class ChatResponse(BaseModel):
    reply: str
    tool_used: str | None = None
    data: dict[str, Any] | list[dict[str, Any]] | None = None
    form_data: dict[str, Any] | None = None
    llm_used: bool = False
