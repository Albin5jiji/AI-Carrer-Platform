"""Audit logging helper. Records who did what, never credentials."""

from sqlalchemy.orm import Session

from ..models import Account, AuditLog

SENSITIVE_KEYS = {"password", "password_hash", "token", "access_token", "secret", "authorization"}


def _sanitize(payload: dict | None) -> dict:
    if not payload:
        return {}
    clean: dict = {}
    for key, value in payload.items():
        if key.lower() in SENSITIVE_KEYS:
            continue
        clean[str(key)] = value if isinstance(value, (int, float, bool, str, type(None))) else str(value)
    return clean


def record_audit(
    db: Session,
    *,
    actor: Account | None,
    action: str,
    entity_type: str,
    entity_id: int | None = None,
    summary: str | None = None,
    meta: dict | None = None,
) -> AuditLog:
    """Add (but do not commit) an audit row for an important action."""

    entry = AuditLog(
        actor_account_id=actor.id if actor else None,
        actor_email=actor.email if actor else None,
        actor_role=actor.role.value if actor else None,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        summary=summary,
        meta=_sanitize(meta),
    )
    db.add(entry)
    return entry
