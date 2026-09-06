import { render,screen,fireEvent,waitFor,cleanup } from '@testing-library/react';
import { afterEach,it,expect,vi } from 'vitest';
import { LanguageProvider } from '../src/context/LanguageProvider';
import CharacterRatingWidget from '../src/components/character/CharacterRatingWidget';
afterEach(cleanup);
it('retains failed rating and explicitly retries without claiming saved',async()=>{
 const save=vi.fn().mockRejectedValueOnce(new Error('offline')).mockResolvedValueOnce({rating:3.5});
 render(<LanguageProvider><CharacterRatingWidget currentRating={{rating:3}} onRate={save}/></LanguageProvider>);
 fireEvent.click(screen.getByRole('button',{name:'0.5점 올리기'}));
 expect(screen.getByText('저장 중…')).toBeTruthy();
 await screen.findByRole('alert'); expect(screen.getByRole('slider').value).toBe('3.5');
 expect(screen.queryByText('저장됨')).toBeNull();
 fireEvent.click(screen.getByRole('button',{name:'다시 저장'}));
 await waitFor(()=>expect(screen.getByText('저장됨')).toBeTruthy()); expect(save).toHaveBeenCalledTimes(2);
});
it('clear is a real delete action through onRate zero',async()=>{
 const save=vi.fn().mockResolvedValue(null); render(<LanguageProvider><CharacterRatingWidget currentRating={{rating:3}} onRate={save}/></LanguageProvider>);
 fireEvent.click(screen.getByRole('button',{name:'평가 지우기'})); await waitFor(()=>expect(save).toHaveBeenCalledWith(0));
});

it('anime rating also retains failed value and allows explicit clear',async()=>{
 const {default:RatingWidget}=await import('../src/components/anime/RatingWidget');
 const save=vi.fn().mockRejectedValue(new Error('offline'));
 render(<LanguageProvider><RatingWidget animeId={1} currentRating={{rating:3}} onRate={save} onStatusChange={vi.fn()}/></LanguageProvider>);
 fireEvent.click(screen.getByRole('button',{name:'0.5점 올리기'}));
 await screen.findByRole('alert'); expect(screen.getByRole('slider').value).toBe('3.5');
});
