import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react';
import { MemoryRouter, useLocation } from 'react-router-dom';
import { afterEach, it, expect, vi } from 'vitest';
import { LanguageProvider } from '../src/context/LanguageProvider';
import NotificationDropdown from '../src/components/common/NotificationDropdown';
import { notificationService } from '../src/services/notificationService';
import api from '../src/services/api';
afterEach(() => {cleanup(); vi.restoreAllMocks();});
const item = {is_read:1, type:'like', actor_user_id:2, actor_username:'Reader', time:'2025-01-01T00:00:00', item_id:1};
function Location() { return <output>{useLocation().search}</output>; }
it('owns mark-read when Navbar supplies no callback and honors server read flags', async () => {
 vi.spyOn(notificationService,'getRecentNotifications').mockResolvedValue({items:[item]});
 const post = vi.spyOn(api,'post').mockResolvedValue({data:{}});
 const {container} = render(<MemoryRouter><LanguageProvider><NotificationDropdown isOpen onClose={vi.fn()}/><Location/></LanguageProvider></MemoryRouter>);
 await screen.findAllByText(/Reader님/);
 expect(container.querySelectorAll('.animate-pulse')).toHaveLength(0);
 fireEvent.click(screen.getAllByText('모두 읽음')[0]);
 await waitFor(() => expect(post).toHaveBeenCalledWith('/api/notifications/mark-read'));
 fireEvent.click(screen.getAllByText('알림 모두보기 →')[0]);
 await screen.findByText('?filter=notifications');
});
it('view all navigates even when marking read rejects', async () => {
 vi.spyOn(notificationService,'getRecentNotifications').mockResolvedValue({items:[item]});
 const mark = vi.fn().mockRejectedValue(new Error('offline'));
 render(<MemoryRouter><LanguageProvider><NotificationDropdown isOpen onClose={vi.fn()} onMarkAllRead={mark}/><Location/></LanguageProvider></MemoryRouter>);
 await screen.findAllByText(/Reader님/);
 fireEvent.click(screen.getAllByText('알림 모두보기 →')[0]);
 await screen.findByText('?filter=notifications');
});
