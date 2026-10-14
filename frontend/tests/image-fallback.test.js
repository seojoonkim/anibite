import { describe, it, expect } from 'vitest';
import { nextImageFallback } from '../src/utils/imageFallback';

describe('nextImageFallback', () => {
  it('steps covers_large -> covers -> placeholder', () => {
    expect(nextImageFallback('https://images.anibite.com/images/covers_large/1.jpg')).toBe('https://images.anibite.com/images/covers/1.jpg');
    expect(nextImageFallback('https://images.anibite.com/images/covers/1.jpg')).toBe('/placeholder-anime.svg');
    expect(nextImageFallback('/placeholder-anime.svg')).toBeNull();
  });
});
