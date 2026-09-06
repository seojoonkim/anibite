import { readFileSync } from 'node:fs';
import { expect, it } from 'vitest';
const source = path => readFileSync(new URL(path, import.meta.url),'utf8');
it('keeps chart dependencies behind dynamic imports on profile', () => {
 const file = source('../src/pages/MyAniPass.jsx');
 expect(file).not.toMatch(/import \w+ from ['"][^'"]*(?:Chart|GenrePreferences|FormatDistribution|StudioStats|SeasonStats)['"]/);
 expect(file).toContain('lazy(');
});
it('does not override every inline button background and supports reduced motion', () => {
 const css = source('../src/index.css'); expect(css).not.toContain('button[style*="background"]');
 expect(css).toContain('prefers-reduced-motion'); expect(css).toContain('env(safe-area-inset-bottom');
});
it('uses AniBite domain and default Korean document', () => {
 const html = source('../index.html'); expect(html).toContain('lang="ko"'); expect(html).not.toContain('anipass.app');
});
