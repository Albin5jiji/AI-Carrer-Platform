from datetime import datetime

from pydantic import BaseModel

from ..models import NotificationType


class NotificationOut(BaseModel):
    id: int
    title: str
    message: str
    type: NotificationType
    entity_type: str | None = None
    entity_id: int | None = None
    is_read: bool
    created_at: datetime


class NotificationListOut(BaseModel):
    unread_count: int
    items: list[NotificationOut]


__all__ = ["NotificationOut", "NotificationListOut"]
