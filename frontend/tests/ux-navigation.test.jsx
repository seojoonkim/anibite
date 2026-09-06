import { render, screen, within, cleanup } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, expect, it, vi } from 'vitest';
import Navbar from '../src/components/common/Navbar';
import { AuthProvider } from '../src/context/AuthProvider';
import { LanguageProvider } from '../src/context/LanguageProvider';
import { LogoWiggleProvider } from '../src/context/LogoWiggleProvider';
import { userService } from '../src/services/userService';
import { notificationService } from '../src/services/notificationService';
afterEach(() => { cleanup(); vi.restoreAllMocks(); });
it('offers four primary mobile destinations and public search without private requests', () => {
 const stats = vi.spyOn(userService,'getStats'); const notifications = vi.spyOn(notificationService,'getUnreadCount');
 render(<MemoryRouter><AuthProvider><LanguageProvider><LogoWiggleProvider><Navbar/></LogoWiggleProvider></LanguageProvider></AuthProvider></MemoryRouter>);
 const mobile = screen.getByRole('navigation',{name:'모바일 주요 메뉴'});
 expect(within(mobile).getAllByRole('link').map(a=>a.textContent)).toEqual(['발견','평가','피드','내 서재']);
 expect(screen.getByRole('searchbox',{name:'작품 검색'})).toBeTruthy();
 expect(stats).not.toHaveBeenCalled(); expect(notifications).not.toHaveBeenCalled();
});
