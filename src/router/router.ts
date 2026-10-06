import { useCallback, useEffect, useState } from "react";

/**
 * Tiny hash based router: no extra dependency, works with the existing sidebar
 * anchor links, and is easy to read. Routes look like `#/student/profile`.
 */
export function readHashPath(): string {
  const raw = window.location.hash.replace(/^#/, "");
  if (!raw || raw === "/") return "/";
  return raw.startsWith("/") ? raw : `/${raw}`;
}

export function navigate(path: string): void {
  const next = path.startsWith("/") ? path : `/${path}`;
  if (readHashPath() === next) {
    window.dispatchEvent(new CustomEvent("career:route"));
    return;
  }
  window.location.hash = `#${next}`;
}

export function useRoute(): { path: string; navigate: typeof navigate } {
  const [path, setPath] = useState(readHashPath);

  useEffect(() => {
    function sync() {
      setPath(readHashPath());
    }
    window.addEventListener("hashchange", sync);
    window.addEventListener("career:route", sync);
    return () => {
      window.removeEventListener("hashchange", sync);
      window.removeEventListener("career:route", sync);
    };
  }, []);

  const go = useCallback((next: string) => navigate(next), []);
  return { path, navigate: go };
}
