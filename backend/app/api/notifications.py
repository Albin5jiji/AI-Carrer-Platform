"""In-app notifications. A user can only read and change their own notifications."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_account
from ..models import Account, Notification, NotificationType
from ..schemas.common import Message
from ..schemas.notification import NotificationListOut, NotificationOut

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=NotificationListOut)
def list_notifications(
    type_filter: NotificationType | None = None,
    unread_only: bool = False,
    limit: int = Query(default=30, ge=1, le=100),
    db: Session = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> NotificationListOut:
    query = db.query(Notification).filter(Notification.account_id == account.id)
    if type_filter is not None:
        query = query.filter(Notification.type == type_filter)
    if unread_only:
        query = query.filter(Notification.is_read.is_(False))

    rows = query.order_by(Notification.id.desc()).limit(limit).all()
    unread = (
        db.query(Notification)
        .filter(Notification.account_id == account.id, Notification.is_read.is_(False))
        .count()
    )
    return NotificationListOut(
        unread_count=unread,
        items=[
            NotificationOut(
                id=row.id,
                title=row.title,
                message=row.message,
                type=row.type,
                entity_type=row.entity_type,
                entity_id=row.entity_id,
                is_read=row.is_read,
                created_at=row.created_at,
            )
            for row in rows
        ],
    )


@router.get("/unread-count")
def unread_count(
    db: Session = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> dict:
    count = (
        db.query(Notification)
        .filter(Notification.account_id == account.id, Notification.is_read.is_(False))
        .count()
    )
    return {"unread_count": count}


@router.post("/{notification_id}/read", response_model=NotificationOut)
def mark_read(
    notification_id: int,
    db: Session = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> NotificationOut:
    row = db.get(Notification, notification_id)
    if row is None or row.account_id != account.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    row.is_read = True
    db.commit()
    db.refresh(row)
    return NotificationOut(
        id=row.id,
        title=row.title,
        message=row.message,
        type=row.type,
        entity_type=row.entity_type,
        entity_id=row.entity_id,
        is_read=row.is_read,
        created_at=row.created_at,
    )


@router.post("/read-all", response_model=Message)
def mark_all_read(
    db: Session = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> Message:
    updated = (
        db.query(Notification)
        .filter(Notification.account_id == account.id, Notification.is_read.is_(False))
        .update({"is_read": True})
    )
    db.commit()
    return Message(message=f"{updated} notification(s) marked as read")
