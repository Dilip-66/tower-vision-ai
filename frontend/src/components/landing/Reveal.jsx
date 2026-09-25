import { useEffect, useRef, useState } from "react";
import { cn } from "../../lib/utils";

/**
 * Scroll-triggered reveal used across the landing page.
 * Adds data-visible once the element enters the viewport.
 */
export function Reveal({ as: Tag = "div", delay = 0, className, children, ...props }) {
  const ref = useRef(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;

    if (typeof IntersectionObserver === "undefined") {
      setVisible(true);
      return;
    }

    // Safety net: never leave content permanently hidden.
    const fallback = setTimeout(() => setVisible(true), 1500);

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setVisible(true);
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.15, rootMargin: "0px 0px -60px 0px" }
    );

    observer.observe(node);

    return () => {
      clearTimeout(fallback);
      observer.disconnect();
    };
  }, []);

  return (
    <Tag
      ref={ref}
      data-visible={visible}
      style={{ transitionDelay: `${delay}ms` }}
      className={cn("lp-reveal", className)}
      {...props}
    >
      {children}
    </Tag>
  );
}
