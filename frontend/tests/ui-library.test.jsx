import { render, screen, cleanup } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, it, expect, vi } from 'vitest';
import MyAniPass from '../src/pages/MyAniPass';
import { userService } from '../src/services/userService';
import { followService } from '../src/services/followService';
vi.mock('../src/context/AuthContext', () => ({useAuth: () => ({user:{id:1,username:'fixture',created_at:'2025-01-01'}})}));
vi.mock('../src/context/LanguageContext', () => ({useLanguage: () => ({language:'en'})}));
vi.mock('../src/components/profile/OtakuMeter', () => ({default: () => <p>Statistics meter</p>}));
afterEach(() => {cleanup();vi.restoreAllMocks();sessionStorage.clear();});
it('renders authenticated library statistics behind Suspense', async () => {
 for (const name of ['getGenrePreferences','getRatingDistribution','getYearDistribution','getFormatDistribution','getEpisodeLengthDistribution','getStudioStats','getSeasonStats','getGenreCombinations']) vi.spyOn(userService,name).mockResolvedValue([]);
 vi.spyOn(userService,'getStats').mockResolvedValue({total_rated:0,otaku_score:0});
 vi.spyOn(userService,'getWatchTime').mockResolvedValue({total_minutes:0});
 vi.spyOn(userService,'getRatingStats').mockResolvedValue(null);
 vi.spyOn(followService,'getFollowCounts').mockResolvedValue({followers_count:0,following_count:0});
 render(<MemoryRouter initialEntries={['/my-anipass?tab=anipass']}><MyAniPass/></MemoryRouter>);
 expect(await screen.findByText('Statistics meter')).toBeTruthy();
});
