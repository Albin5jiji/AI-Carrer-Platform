import { useState } from "react";
import type { ReactNode } from "react";
import { LogOut, Menu, Sparkles, X } from "lucide-react";
import { useAuth, roleLabel } from "../../context/AuthContext";
import { navigate, useRoute } from "../../router/router";
import { initials } from "../../utils/format";
import { navForRole } from "./navConfig";
import { NotificationBell } from "./NotificationBell";

export function AppShell({ children }: { children: ReactNode }) {
  const { user, role, logout } = useAuth();
  const { path } = useRoute();
  const [menuOpen, setMenuOpen] = useState(false);
  const items = navForRole(role);
  const activeItem = items.find((item) => path.startsWith(item.path));

  function go(target: string) {
    setMenuOpen(false);
    navigate(target);
  }

  return (
    <div className="app-shell">
      {menuOpen && <div className="sidebar-scrim" onClick={() => setMenuOpen(false)} />}

      <aside className={menuOpen ? "sidebar open" : "sidebar"}>
        <div className="brand">
          <div className="brand-mark">
            <Sparkles size={22} />
          </div>
          <div>
            <p>AI Career</p>
            <span>Career Intelligence Platform</span>
          </div>
          <button className="icon-btn sidebar-close" onClick={() => setMenuOpen(false)} type="button" aria-label="Close menu">
            <X size={18} />
          </button>
        </div>

        <nav className="nav-stack" aria-label="Primary navigation">
          {items.map((item) => {
            const Icon = item.icon;
            const active = path.startsWith(item.path);
            return (
              <button
                className={active ? "nav-item active" : "nav-item"}
                key={item.path}
                onClick={() => go(item.path)}
                type="button"
              >
                <Icon size={18} />
                {item.label}
              </button>
            );
          })}
        </nav>

        <div className="session-card">
          <div className="session-avatar">{initials(user?.full_name ?? "?")}</div>
          <div>
            <p>{user?.full_name}</p>
            <span>{roleLabel(role)}</span>
          </div>
          <button className="icon-btn" onClick={() => go("/notifications")} type="button" aria-label="All notifications">
            <Menu size={16} />
          </button>
        </div>
      </aside>

      <section className="content">
        <header className="topbar">
          <div className="topbar-left">
            <button className="icon-btn menu-btn" onClick={() => setMenuOpen(true)} type="button" aria-label="Open menu">
              <Menu size={20} />
            </button>
            <div>
              <p className="eyebrow">{roleLabel(role)} workspace</p>
              <h1>{activeItem?.label ?? "Career Intelligence"}</h1>
              <p className="session-line">
                {user?.full_name} · {user?.identifier} · {user?.department_or_program}
              </p>
            </div>
          </div>

          <div className="topbar-actions">
            <button className="btn btn-ghost btn-sm" onClick={() => go("/notifications")} type="button">
              Notifications
            </button>
            <NotificationBell />
            <button className="btn btn-outline btn-sm" onClick={() => logout("You have been signed out.")} type="button">
              <LogOut size={15} /> Sign out
            </button>
          </div>
        </header>

        <main className="page-body">{children}</main>
      </section>
    </div>
  );
}
