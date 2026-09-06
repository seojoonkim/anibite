import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react';
import { afterEach, it, expect, vi } from 'vitest';
import { LanguageProvider } from '../src/context/LanguageProvider';
import RatingEditor from '../src/components/common/RatingEditor';
import RatingWidget from '../src/components/anime/RatingWidget';
import { seriesService } from '../src/services/seriesService';
afterEach(() => { cleanup(); vi.restoreAllMocks(); });
it('status failures are visible and retry the same intent while all controls are locked', async () => {
 vi.spyOn(seriesService, 'getAnimeSequels').mockResolvedValue({sequels:[]});
 let reject;
 const status = vi.fn().mockImplementationOnce(() => new Promise((_, no) => { reject = no; })).mockResolvedValue(undefined);
 render(<LanguageProvider><RatingWidget animeId={1} currentRating={{rating:3,status:'RATED'}} onRate={vi.fn()} onStatusChange={status}/></LanguageProvider>);
 fireEvent.click(screen.getByRole('button', {name:'보고싶어요'}));
 await waitFor(() => expect(status).toHaveBeenCalledWith('WANT_TO_WATCH'));
 expect(screen.getByRole('slider')).toBeDisabled();
 reject(new Error('offline'));
 await screen.findByRole('alert');
 fireEvent.click(screen.getByRole('button', {name:'다시 시도'}));
 await waitFor(() => expect(status).toHaveBeenCalledTimes(2));
 expect(status).toHaveBeenLastCalledWith('WANT_TO_WATCH');
});
it('successful draft yields to later saved ratings and status clears', async () => {
 const save = vi.fn().mockResolvedValue(undefined);
 const view = rating => <LanguageProvider><RatingEditor rating={rating} onSave={save}/></LanguageProvider>;
 const {rerender} = render(view(3));
 fireEvent.click(screen.getByRole('button', {name:'0.5점 올리기'}));
 await screen.findByText('저장됨');
 rerender(view(3.5));
 rerender(view(0));
 expect(screen.getByRole('slider').value).toBe('0');
 rerender(view(4));
 expect(screen.getByRole('slider').value).toBe('4');
});

it.each([false, true])('series failure keeps dialog and retry intent (all=%s)', async all => {
 vi.spyOn(seriesService, 'getAnimeSequels').mockResolvedValue({sequels:[{id:2,title_romaji:'Sequel'}]});
 const bulk = vi.spyOn(seriesService, 'bulkRateSeries').mockResolvedValue(undefined);
 const status = vi.fn().mockRejectedValueOnce(new Error('offline')).mockResolvedValue(undefined);
 render(<LanguageProvider><RatingWidget animeId={1} currentRating={{rating:3,status:'RATED'}} onRate={vi.fn()} onStatusChange={status}/></LanguageProvider>);
 fireEvent.click(screen.getByRole('button',{name:'보고싶어요'}));
 await screen.findByRole('dialog');
 fireEvent.click(screen.getByRole('button',{name:all ? '모두 적용 (2개)' : '현재만'}));
 await screen.findByRole('alert');
 expect(screen.getByRole('dialog').contains(screen.getByRole('alert'))).toBe(true);
 fireEvent.click(screen.getByRole('button',{name:'다시 시도'}));
 await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
 expect(status).toHaveBeenLastCalledWith('WANT_TO_WATCH');
 expect(bulk).toHaveBeenCalledTimes(all ? 2 : 0);
});
