/**
 * Global <img> fallback: when a large cover is missing on the CDN, retry the
 * regular cover, then fall back to the placeholder. Runs in capture phase
 * because image error events do not bubble.
 */
export const nextImageFallback = (src) => {
  if (!src || src.includes('/placeholder-anime.svg')) return null;
  if (src.includes('/covers_large/')) return src.replace('/covers_large/', '/covers/');
  return '/placeholder-anime.svg';
};

export const installImageFallback = (root = document) => {
  root.addEventListener('error', (event) => {
    const img = event.target;
    if (!(img instanceof HTMLImageElement) || img.dataset.noFallback !== undefined) return;
    const tries = Number(img.dataset.fallbackTries || 0);
    if (tries >= 2) return;
    const next = nextImageFallback(img.currentSrc || img.src);
    if (!next) return;
    img.dataset.fallbackTries = String(tries + 1);
    img.removeAttribute('srcset');
    img.src = next;
  }, true);
};
