// frontend/src/v3/components/ui/hooks.js
// Small shared hooks for the V3 UI primitives (D20 responsive + a11y helpers).
import { useEffect, useRef, useState } from 'react';

/** Match a CSS media query (defaults to the D20 tablet breakpoint). */
export function useMediaQuery(query) {
  const [matches, setMatches] = useState(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return false;
    return window.matchMedia(query).matches;
  });

  useEffect(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return undefined;
    const mql = window.matchMedia(query);
    const onChange = (e) => setMatches(e.matches);
    setMatches(mql.matches);
    mql.addEventListener('change', onChange);
    return () => mql.removeEventListener('change', onChange);
  }, [query]);

  return matches;
}

/** True when the viewport is at or below the tablet breakpoint (D20). */
export function useIsTablet() {
  return useMediaQuery('(max-width: 900px)');
}

/** True when the viewport is at or below the mobile breakpoint. */
export function useIsMobile() {
  return useMediaQuery('(max-width: 640px)');
}

/** Invoke `handler` when a pointer-down happens outside `ref`. */
export function useOnClickOutside(ref, handler) {
  const saved = useRef(handler);
  useEffect(() => { saved.current = handler; }, [handler]);

  useEffect(() => {
    const listener = (event) => {
      const el = ref.current;
      if (!el || (el && el.contains(event.target))) return;
      saved.current(event);
    };
    document.addEventListener('mousedown', listener);
    document.addEventListener('touchstart', listener);
    return () => {
      document.removeEventListener('mousedown', listener);
      document.removeEventListener('touchstart', listener);
    };
  }, [ref]);
}

/** Trap focus inside a dialog/drawer while it is open (D21.9). */
export function useFocusTrap(active, { onEscape } = {}) {
  const ref = useRef(null);

  useEffect(() => {
    if (!active) return undefined;
    const container = ref.current;
    if (!container) return undefined;
    const previouslyFocused = document.activeElement;

    const focusables = () => Array.from(
      container.querySelectorAll('button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'),
    );

    const first = () => focusables()[0];
    const last = () => focusables()[focusables().length - 1];

    const onKeyDown = (e) => {
      if (e.key === 'Escape') {
        e.stopPropagation();
        if (onEscape) onEscape(e);
        return;
      }
      if (e.key !== 'Tab') return;
      const list = focusables();
      if (list.length === 0) return;
      const current = document.activeElement;
      if (e.shiftKey && (current === list[0] || current === container)) {
        e.preventDefault();
        list[list.length - 1].focus();
      } else if (!e.shiftKey && current === list[list.length - 1]) {
        e.preventDefault();
        list[0].focus();
      }
    };

    // Move focus inside when opened.
    const firstEl = first();
    if (firstEl && !container.contains(document.activeElement)) firstEl.focus();

    container.addEventListener('keydown', onKeyDown);
    return () => {
      container.removeEventListener('keydown', onKeyDown);
      if (previouslyFocused && typeof previouslyFocused.focus === 'function') {
        previouslyFocused.focus();
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active]);

  return ref;
}
