import { execFileSync } from 'node:child_process';
import { expect, it } from 'vitest';
it('owned detail/profile code has no undefined references or conditional hooks', () => {
 let output; try { output=execFileSync('node',['node_modules/eslint/bin/eslint.js','src/pages/AnimeDetail.jsx','src/pages/CharacterDetail.jsx','src/pages/MyAniPass.jsx','src/components/common/ContentMenu.jsx','-f','json'],{encoding:'utf8'}); } catch(error) { output=error.stdout; }
 const defects=JSON.parse(output).flatMap(file=>file.messages.filter(m=>['no-undef','react-hooks/rules-of-hooks'].includes(m.ruleId)).map(m=>`${file.filePath}:${m.line} ${m.message}`));
 expect(defects).toEqual([]);
},30000);
