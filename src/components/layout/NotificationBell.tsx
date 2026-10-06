import { useState } from "react";
import { Bell, CheckCheck } from "lucide-react";
import { notificationApi } from "../../api/studentApi";
import { useAsync } from "../../hooks/useAsync";
import { formatDateTime } from "../../utils/format";
import { EmptyState } from "../ui/primitives";
import { navigate } from "../../router/router";

export function NotificationBell() {
  const [open, setOpen] = useState(false);
  const [reloadKey, setReloadKey] = useState("0");
  const { data, error, loading, reload } = useAsync(() => notificationApi.list({}), reloadKey);

  async function markAllRead() {
    try {
      await notificationApi.markAllRead();
      setReloadKey(String(Date.now()));
    } catch {
      reload();
    }
  }

  async function markRead(id: number) {
    try {
      await notificationApi.markRead(id);
      setReloadKey(String(Date.now()));
    } catch {
      reload();
    }
  }

  const unread = data?.unread_count ?? 0;

  return (
    <div className="notification-wrap">
      <button
        aria-label={`Notifications${unread ? `, ${unread} unread` : ""}`}
        className="icon-btn notification-btn"
        onClick={() => setOpen((current) => !current)}
        type="button"
      >
        <Bell size={19} />
        {unread > 0 && <span className="notification-count">{unread > 9 ? "9+" : unread}</span>}
      </button>

      {open && (
        <div className="notification-panel">
          <div className="notification-head">
            <strong>Notifications</strong>
            <div><button className="link-btn" onClick={() => navigate("/notifications")} type="button">View all</button><button className="link-btn" onClick={markAllRead} type="button"><CheckCheck size={14} /> Mark all read</button></div>
          </div>

          <div className="notification-list">
            {loading && <p className="muted">Loading notifications…</p>}
            {error && <p className="form-error">{error}</p>}
            {!loading && !error && (data?.items.length ?? 0) === 0 && (
              <EmptyState title="No notifications yet" description="Updates about resumes, applications and drives appear here." />
            )}
            {data?.items.map((item) => (
              <button
                className={item.is_read ? "notification-row" : "notification-row unread"}
                key={item.id}
                onClick={() => void markRead(item.id)}
                type="button"
              >
                <strong>{item.title}</strong>
                <p>{item.message}</p>
                <span>{formatDateTime(item.created_at)}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
