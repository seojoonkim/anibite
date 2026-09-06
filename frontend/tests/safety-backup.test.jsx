import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import BackupLogs from '../src/pages/BackupLogs';
vi.mock('../src/context/LanguageContext', () => ({ useLanguage: () => ({ language: 'ko' }) }));

describe('backup operations safety', () => {
  it('does not expose a browser button to delete production duplicates', () => {
    render(<BackupLogs />);
    expect(screen.queryByRole('button', { name: /중복.*제거/ })).not.toBeInTheDocument();
  });
  it('explains that migration requires a verified backup and approval', () => {
    render(<BackupLogs />);
    expect(screen.getByText(/복원 검증/)).toBeInTheDocument();
    expect(screen.getByText(/승인/)).toBeInTheDocument();
  });
});
