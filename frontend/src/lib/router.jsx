import { useEffect, useState } from "react";

/**
 * Minimal client-side router (no external dependency).
 * Handles pushState navigation and re-renders on popstate.
 */
export function usePathname() {
  const [path, setPath] = useState(() => window.location.pathname);

  useEffect(() => {
    function onPop() {
      setPath(window.location.pathname);
    }

    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  return path;
}

export function navigate(to) {
  if (window.location.pathname === to) return;
  window.history.pushState({}, "", to);
  window.dispatchEvent(new PopStateEvent("popstate"));
  window.scrollTo({ top: 0, behavior: "instant" });
}

export function Link({ to, children, onClick, ...props }) {
  return (
    <a
      href={to}
      onClick={(event) => {
        if (event.metaKey || event.ctrlKey || event.shiftKey) return;
        event.preventDefault();
        onClick?.(event);
        navigate(to);
      }}
      {...props}
    >
      {children}
    </a>
  );
}
