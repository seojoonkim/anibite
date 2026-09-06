import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react';
import { MemoryRouter, Routes, Route, useLocation } from 'react-router-dom';
import { afterEach, expect, it, vi } from 'vitest';
import { AuthProvider } from '../src/context/AuthProvider';
import { useAuth } from '../src/context/AuthContext';
import { LanguageProvider } from '../src/context/LanguageProvider';
import Login from '../src/pages/Login';
import { authService } from '../src/services/authService';
afterEach(() => { cleanup(); vi.restoreAllMocks(); });
function Destination() { const l = useLocation(); return <p>Destination: {l.pathname}{l.search}{l.hash}</p>; }
it.each(['/anime/12?tab=reviews#mine','//evil.example','/\\evil.example'])('login validates and restores internal return route %s', async from => {
 vi.spyOn(authService, 'login').mockResolvedValue({user:{id: 1,username:'test'}});
 localStorage.setItem('bookmarks_migrated_1','true');
 render(<MemoryRouter initialEntries={[{pathname:'/login', state:{from}}]}><AuthProvider><LanguageProvider><Routes><Route path="/login" element={<Login/>}/><Route path="*" element={<Destination/>}/></Routes></LanguageProvider></AuthProvider></MemoryRouter>);
 fireEvent.change(screen.getByLabelText('아이디 또는 이메일'), {target:{value:'test'}});
 fireEvent.change(screen.getByLabelText('비밀번호'), {target:{value:'secret'}});
 expect(screen.getByLabelText('비밀번호').autocomplete).toBe('current-password');
 fireEvent.click(screen.getByRole('button', {name:'로그인', exact:true}));
 await waitFor(() => expect(screen.getByText(`Destination: ${from.startsWith('/anime/') ? from : '/browse'}`)).toBeTruthy());
});

it('does not trust cached privilege after a rejected or unavailable session',async()=>{
 localStorage.setItem('token','fixture-expired');localStorage.setItem('user',JSON.stringify({id:9,is_admin:true,otaku_score:12}));
 vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:false,status:401}));
 function Session(){const {user,loading}=useAuth();return <p>{loading?'pending':user?'private':'guest'}</p>;}
 render(<AuthProvider><Session/></AuthProvider>);
 await screen.findByText('guest');expect(localStorage.getItem('token')).toBeNull();vi.unstubAllGlobals();
});
