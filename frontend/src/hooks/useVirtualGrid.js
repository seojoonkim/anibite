import { useState, useEffect, useRef } from 'react';

/**
 * Virtual scrolling hook for grid layouts with category sections
 * Only renders sections that are near the viewport
 */
export function useVirtualGrid(sections, { rootMargin = '500px' } = {}) {
  const [visibleSections, setVisibleSections] = useState(new Set());
  const observerRef = useRef(null);
  const sectionRefs = useRef(new Map());

  useEffect(() => {
    // Create intersection observer
    observerRef.current = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          const sectionId = entry.target.dataset.sectionId;
          if (entry.isIntersecting) {
            setVisibleSections((prev) => new Set([...prev, sectionId]));
          }
          // Don't remove sections once loaded to avoid re-render flash
        });
      },
      {
        rootMargin, // Load sections 500px before they enter viewport
        threshold: 0,
      }
    );

    // Observe all section placeholders
    sectionRefs.current.forEach((element) => {
      if (element) {
        observerRef.current.observe(element);
      }
    });

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, [rootMargin, sections.length]);

  const getSectionRef = (sectionId) => (element) => {
    if (element) {
      sectionRefs.current.set(sectionId, element);
      if (observerRef.current) {
        observerRef.current.observe(element);
      }
    } else {
      sectionRefs.current.delete(sectionId);
    }
  };

  const isSectionVisible = (sectionId) => visibleSections.has(sectionId);

  return { getSectionRef, isSectionVisible };
}
