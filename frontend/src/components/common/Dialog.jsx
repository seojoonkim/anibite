import { useEffect, useId, useRef } from 'react';
import { createPortal } from 'react-dom';

export default function Dialog({ open = true, title, children, onClose, busy = false }) {
 const ref = useRef(null);
 const closeRef = useRef(onClose);
 const busyRef = useRef(busy);
 const titleId = useId();
 useEffect(() => { closeRef.current = onClose; busyRef.current = busy; }, [onClose, busy]);
 useEffect(() => {
  if (!open) return;
  const previous = document.activeElement;
  const panel = ref.current;
  const host = panel.parentElement;
  const siblings = [...document.body.children].filter(node => node !== host);
  const states = siblings.map(node => [node, node.inert]);
  states.forEach(([node]) => { node.inert = true; });
  const overflow = document.body.style.overflow;
  document.body.style.overflow = 'hidden';
  const focusables = () => [...panel.querySelectorAll('button:not([disabled]), a[href], input:not([disabled]), textarea:not([disabled]), select:not([disabled]), [tabindex="0"]')].filter(node => !node.hidden);
  (focusables()[0] || panel).focus();
  const keydown = event => {
   if (event.key === 'Escape') { event.preventDefault(); event.stopPropagation(); if (!busyRef.current) closeRef.current?.(); }
   if (event.key !== 'Tab') return;
   const nodes = focusables(); const first = nodes[0]; const last = nodes[nodes.length - 1];
   if (!first) { event.preventDefault(); panel.focus(); }
   else if (event.shiftKey && (document.activeElement === first || document.activeElement === panel)) { event.preventDefault(); last.focus(); }
   else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
  };
  const focusin = event => { if (!panel.contains(event.target)) (focusables()[0] || panel).focus(); };
  document.addEventListener('keydown', keydown);
  document.addEventListener('focusin', focusin);
  return () => { document.removeEventListener('keydown', keydown); document.removeEventListener('focusin', focusin); states.forEach(([node, inert]) => { node.inert = inert; }); document.body.style.overflow = overflow; if (previous?.isConnected) previous.focus(); };
 }, [open]);
 if (!open) return null;
 return createPortal(<div className="dialog-backdrop"><section ref={ref} role="dialog" aria-modal="true" aria-labelledby={titleId} aria-busy={busy} tabIndex={-1} className="dialog-panel"><h2 id={titleId} className="sr-only">{title}</h2>{children}</section></div>, document.body);
}
