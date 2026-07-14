from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from .. import schemas, services
from .parser import summarize


def _as_text(value: Any) -> str | None:
    """Convert LLM-produced values into database-safe text.

    Groq may return a single CRM text field as a list, for example:
    ["Dr. Vikram Shah was positive about the product"].
    The database schema expects a string, so lists are joined cleanly.
    """
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or None
    if isinstance(value, (list, tuple, set)):
        parts = [_as_text(item) for item in value]
        cleaned_parts = [part for part in parts if part]
        return "; ".join(cleaned_parts) or None
    if isinstance(value, dict):
        parts = []
        for key, item in value.items():
            item_text = _as_text(item)
            if item_text:
                parts.append(f"{key}: {item_text}")
        return "; ".join(parts) or None
    return str(value).strip() or None


def _normalize_sentiment(value: Any) -> str:
    text = (_as_text(value) or "Neutral").lower()
    if "positive" in text:
        return "Positive"
    if "negative" in text:
        return "Negative"
    return "Neutral"


def _normalize_interaction_fields(args: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(args)
    for field in (
        "interaction_type",
        "attendees",
        "topics_discussed",
        "materials_shared",
        "samples_distributed",
        "outcomes",
        "follow_up_actions",
        "ai_summary",
    ):
        if field in normalized:
            normalized[field] = _as_text(normalized[field])
    if "sentiment" in normalized:
        normalized["sentiment"] = _normalize_sentiment(normalized["sentiment"])
    return normalized


def serialize(item):
    return {
        "id": item.id,
        "hcp_id": item.hcp_id,
        "hcp_name": item.hcp.name,
        "interaction_type": item.interaction_type,
        "interaction_date": item.interaction_date.isoformat(),
        "interaction_time": item.interaction_time.isoformat() if item.interaction_time else None,
        "attendees": item.attendees,
        "topics_discussed": item.topics_discussed,
        "materials_shared": item.materials_shared,
        "samples_distributed": item.samples_distributed,
        "sentiment": item.sentiment,
        "outcomes": item.outcomes,
        "follow_up_actions": item.follow_up_actions,
        "ai_summary": item.ai_summary,
    }


def resolve_hcp(db: Session, args: dict[str, Any]):
    if args.get("hcp_id"):
        return services.get_hcp(db, int(args["hcp_id"]))
    if args.get("hcp_name"):
        return services.find_hcp_by_name(db, str(args["hcp_name"]))
    return None


def log_interaction(db: Session, args: dict[str, Any]):
    args = _normalize_interaction_fields(args)
    hcp = resolve_hcp(db, args)
    if not hcp:
        raise ValueError("Please provide a valid HCP name, for example Dr. Vikram Shah.")

    topics = args.get("topics_discussed")
    if not topics:
        raise ValueError("Please provide the topics discussed.")

    summary_data = {**args, "hcp_name": hcp.name}
    payload = schemas.InteractionCreate(
        hcp_id=hcp.id,
        interaction_type=args.get("interaction_type") or "Meeting",
        interaction_date=args.get("interaction_date") or date.today().isoformat(),
        interaction_time=args.get("interaction_time"),
        attendees=args.get("attendees"),
        topics_discussed=topics,
        materials_shared=args.get("materials_shared"),
        samples_distributed=args.get("samples_distributed"),
        sentiment=_normalize_sentiment(args.get("sentiment")),
        outcomes=args.get("outcomes"),
        follow_up_actions=args.get("follow_up_actions"),
        ai_summary=_as_text(summarize(summary_data)),
        source="chat",
    )
    return serialize(services.create_interaction(db, payload))


def edit_interaction(db: Session, args: dict[str, Any]):
    interaction_id = args.get("interaction_id")
    if not interaction_id:
        raise ValueError("Please provide the interaction ID to edit.")

    interaction = services.get_interaction(db, int(interaction_id))
    if not interaction:
        raise ValueError(f"Interaction {interaction_id} was not found.")

    raw_changes = args.get("changes") if isinstance(args.get("changes"), dict) else {}
    changes = {
        key: value
        for key, value in raw_changes.items()
        if key in schemas.InteractionUpdate.model_fields and value is not None
    }
    changes = _normalize_interaction_fields(changes)

    if not changes:
        raise ValueError("Please specify at least one field to change.")

    payload = schemas.InteractionUpdate(**changes)
    return serialize(services.update_interaction(db, interaction, payload))


def search_interaction_history(db: Session, args: dict[str, Any]):
    hcp = resolve_hcp(db, args)
    if not hcp:
        raise ValueError("Please provide a valid HCP name.")
    return [serialize(item) for item in services.list_interactions(db, hcp.id, 10)]


def schedule_follow_up(db: Session, args: dict[str, Any]):
    interaction = None
    hcp = resolve_hcp(db, args)

    if args.get("interaction_id"):
        interaction = services.get_interaction(db, int(args["interaction_id"]))
        if not interaction:
            raise ValueError("Interaction not found.")
        hcp = interaction.hcp

    if not hcp:
        raise ValueError("Please provide an HCP name or interaction ID.")
    if not args.get("due_date"):
        raise ValueError("Please provide a due date in YYYY-MM-DD format.")

    task = _as_text(args.get("task"))
    if not task:
        raise ValueError("Please describe the follow-up task.")

    follow_up = services.create_follow_up(
        db,
        schemas.FollowUpCreate(
            hcp_id=hcp.id,
            interaction_id=interaction.id if interaction else None,
            due_date=args["due_date"],
            task=task,
        ),
    )
    return {
        "id": follow_up.id,
        "hcp_name": hcp.name,
        "interaction_id": follow_up.interaction_id,
        "due_date": follow_up.due_date.isoformat(),
        "task": follow_up.task,
        "status": follow_up.status,
    }


def recommend_next_best_action(db: Session, args: dict[str, Any]):
    hcp = resolve_hcp(db, args)
    if not hcp:
        raise ValueError("Please provide a valid HCP name.")

    history = services.list_interactions(db, hcp.id, 5)
    if not history:
        recommendation = "Arrange an introductory meeting and capture the HCP priorities."
        reason = "No previous interaction history is available."
        interaction_id = None
    else:
        latest = history[0]
        interaction_id = latest.id
        if latest.follow_up_actions:
            recommendation = latest.follow_up_actions
            reason = "This was recorded as the follow-up action in the latest interaction."
        elif latest.sentiment.lower() == "positive":
            recommendation = "Share the agreed approved material and schedule a focused follow-up."
            reason = "The latest sentiment was positive."
        elif latest.sentiment.lower() == "negative":
            recommendation = "Address the concern with approved evidence and involve a medical colleague when appropriate."
            reason = "The latest sentiment was negative."
        else:
            recommendation = "Send a concise recap and ask for a suitable follow-up time."
            reason = "The latest interaction was neutral without a specific action."

    return {
        "hcp_name": hcp.name,
        "recommendation": recommendation,
        "reason": reason,
        "based_on_interaction_id": interaction_id,
    }


TOOL_REGISTRY = {
    "log_interaction": log_interaction,
    "edit_interaction": edit_interaction,
    "search_interaction_history": search_interaction_history,
    "schedule_follow_up": schedule_follow_up,
    "recommend_next_best_action": recommend_next_best_action,
}
