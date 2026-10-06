import { useState } from "react";
import { notificationApi } from "../api/studentApi";
import { EmptyState, ErrorState, LoadingState, StatusBadge } from "../components/ui/primitives";
import { SectionCard } from "../components/ui/blocks";
import { useAction, useAsync } from "../hooks/useAsync";
import { formatDateTime } from "../utils/format";

export function NotificationsPage() {
  const [key, setKey] = useState("0"); const feed = useAsync(() => notificationApi.list(), key); const action = useAction(); const refresh = () => setKey(String(Date.now()));
  const one = async (id: number) => { const ok = await action.run(() => notificationApi.markRead(id)); if (ok) refresh(); };
  const all = async () => { const ok = await action.run(() => notificationApi.markAllRead()); if (ok) refresh(); };
  if (feed.loading) return <LoadingState label="Loading notifications…" />; if (feed.error) return <ErrorState message={feed.error} onRetry={feed.reload} />;
  return <SectionCard actions={<><button className="btn btn-outline btn-sm" onClick={refresh} type="button">Refresh</button><button className="btn btn-primary btn-sm" disabled={action.pending} onClick={() => void all()} type="button">Mark all read</button></>} eyebrow="Notifications" title={`${feed.data?.unread_count ?? 0} unread`}>
    {feed.data?.items.length === 0 && <EmptyState title="No notifications yet" />}
    <div className="notification-list">{feed.data?.items.map((item) => <button className={item.is_read ? "notification-row" : "notification-row unread"} key={item.id} onClick={() => void one(item.id)} type="button"><div><strong>{item.title}</strong><p>{item.message}</p><span>{formatDateTime(item.created_at)}</span></div><StatusBadge value={item.type} /></button>)}</div>
    {action.error && <p className="form-error">{action.error}</p>}
  </SectionCard>;
}
