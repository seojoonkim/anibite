import { render, screen, cleanup } from '@testing-library/react';
import { MemoryRouter, Routes, Route, useLocation } from 'react-router-dom';
import { fireEvent } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import AnimeDetail from '../src/pages/AnimeDetail';
import CharacterDetail from '../src/pages/CharacterDetail';
import { animeService } from '../src/services/animeService';
import { characterReviewService } from '../src/services/characterReviewService';
import { characterService } from '../src/services/characterService';
vi.mock('../src/context/AuthContext', () => ({useAuth: () => ({user:null})}));
vi.mock('../src/context/LanguageContext', () => ({useLanguage: () => ({language:'en',getAnimeTitle: a => a.title_romaji})}));
vi.mock('../src/hooks/useActivity', () => ({useActivities: () => ({activities:[],refetch:vi.fn()})}));
vi.mock('../src/hooks/usePrefetch', () => ({getPrefetchedData: () => null}));
function Login() { return <output>{useLocation().state?.from}</output>; }
afterEach(() => {cleanup();vi.restoreAllMocks();});
it.each(['anime','character'])('gates guest %s composition with a review return anchor', async kind => {
 vi.spyOn(characterReviewService,'getCharacterReviews').mockResolvedValue({items:[],total:0});
 vi.spyOn(animeService,'getAnimeById').mockResolvedValue({id:1,title_romaji:'Fixture',genres:[],characters:[],studios:[]});
 vi.spyOn(characterService,'getCharacterDetail').mockResolvedValue({id:1,name_full:'Fixture',anime_appearances:[],voice_actors:[]});
 const {container} = render(<MemoryRouter initialEntries={[`/${kind}/1?source=test`]}><Routes><Route path="/anime/:id" element={<AnimeDetail/>}/><Route path="/character/:id" element={<CharacterDetail/>}/><Route path="/login" element={<Login/>}/></Routes></MemoryRouter>);
 const link = await screen.findByRole('link',{name:'Log in to write a review'});
 expect(container.querySelector('#reviews')).toBeTruthy();
 if(kind === 'anime') expect(container.querySelector('#my-rating')).toBeTruthy();
 expect(screen.queryByRole('button',{name:'Write Review'})).toBeNull();
 fireEvent.click(link);
 expect(await screen.findByText(`/${kind}/1?source=test#reviews`)).toBeTruthy();
});
