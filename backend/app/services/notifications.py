"""In-app notification helper.

Notifications always target a single account (the same `accounts` table used by
authentication), so a user can only ever read their own notifications.
"""

from sqlalchemy.orm import Session

from ..models import Account, Notification, NotificationType, UserRole


def notify(
    db: Session,
    *,
    account_id: int | None,
    title: str,
    message: str,
    type_: NotificationType = NotificationType.general,
    entity_type: str | None = None,
    entity_id: int | None = None,
) -> Notification | None:
    """Create one notification. Returns None when there is no recipient."""

    if account_id is None:
        return None
    entry = Notification(
        account_id=account_id,
        title=title,
        message=message,
        type=type_,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    db.add(entry)
    return entry


def notify_many(db: Session, account_ids: list[int], **kwargs) -> int:
    """Fan a notification out to several accounts. Returns the number created."""

    created = 0
    for account_id in dict.fromkeys(account_ids):
        if notify(db, account_id=account_id, **kwargs) is not None:
            created += 1
    return created


def notify_role(db: Session, role: UserRole, **kwargs) -> int:
    """Notify every account holding a role (used for drive announcements)."""

    account_ids = [account.id for account in db.query(Account).filter(Account.role == role).all()]
    return notify_many(db, account_ids, **kwargs)
