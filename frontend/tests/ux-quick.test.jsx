import {render,screen,fireEvent,cleanup} from '@testing-library/react';
import {MemoryRouter} from 'react-router-dom';
import {it,expect,vi,afterEach} from 'vitest';
import Rate from '../src/pages/Rate';
import { LanguageProvider } from '../src/context/LanguageProvider';
import { LogoWiggleProvider } from '../src/context/LogoWiggleProvider';
import {animeService} from '../src/services/animeService';
afterEach(()=>{cleanup();vi.restoreAllMocks();vi.unstubAllGlobals();});
it('makes quick rating visible without hover and separate from detail links',async()=>{
 vi.stubGlobal('IntersectionObserver',class{observe(){}unobserve(){}disconnect(){}});
 vi.spyOn(animeService,'getAnimeForRating').mockResolvedValue({items:[{id:1,title_romaji:'Fixture',title_korean:'테스트 작품',cover_image_url:'/placeholder-anime.svg',user_rating:0}],total:1});
 vi.spyOn(animeService,'getAnimeRatingStats').mockResolvedValue({rated:0,watchLater:0,pass:0,averageRating:0});
 render(<MemoryRouter><LanguageProvider><LogoWiggleProvider><Rate/></LogoWiggleProvider></LanguageProvider></MemoryRouter>);
 const slider=await screen.findByRole('slider');expect(slider.closest('a')).toBeNull();
 expect(screen.getByRole('link',{name:'캐릭터'}).getAttribute('href')).toBe('/rate-characters');
 fireEvent.focus(slider);expect(slider.closest('[aria-hidden=true]')).toBeNull();
});
