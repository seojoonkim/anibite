import { useState, useEffect } from 'react';
import { useLanguage } from '../context/LanguageContext';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function BackupLogs() {
  const { language } = useLanguage();
  const [loading, setLoading] = useState(false);
  const [cleaningDuplicates, setCleaningDuplicates] = useState(false);
  const [message, setMessage] = useState('');

  const text = {
    ko: {
      title: '백업 시스템',
      subtitle: '데이터베이스 백업 및 중복 제거',
      cleanDuplicates: '중복 데이터 제거',
      cleanDuplicatesDesc: '프로덕션 DB에서 중복된 평가를 제거합니다',
      cleaning: '제거 중...',
      backupInfo: '백업 정보',
      backupSchedule: '백업 스케줄',
      schedule1: '6시간마다 자동 백업 (09:00, 15:00, 21:00, 03:00 KST)',
      schedule2: 'GitHub Artifacts: 최근 30개 (약 7.5일)',
      schedule3: 'GitHub Releases: 매일 자정 1개 영구 보관',
      viewBackups: '백업 확인',
      githubActions: 'GitHub Actions에서 백업 확인',
      githubReleases: 'GitHub Releases에서 장기 백업 확인',
      docs: '백업 가이드',
      viewDocs: 'BACKUP_GUIDE.md 보기'
    },
    ja: {
      title: 'バックアップシステム',
      subtitle: 'データベースバックアップと重複削除',
      cleanDuplicates: '重複データ削除',
      cleanDuplicatesDesc: 'プロダクションDBから重複した評価を削除します',
      cleaning: '削除中...',
      backupInfo: 'バックアップ情報',
      backupSchedule: 'バックアップスケジュール',
      schedule1: '6時間ごとに自動バックアップ (09:00, 15:00, 21:00, 03:00 KST)',
      schedule2: 'GitHub Artifacts: 最近30個 (約7.5日)',
      schedule3: 'GitHub Releases: 毎日深夜1個永久保管',
      viewBackups: 'バックアップ確認',
      githubActions: 'GitHub Actionsでバックアップ確認',
      githubReleases: 'GitHub Releasesで長期バックアップ確認',
      docs: 'バックアップガイド',
      viewDocs: 'BACKUP_GUIDE.md 表示'
    },
    en: {
      title: 'Backup System',
      subtitle: 'Database Backup & Duplicate Removal',
      cleanDuplicates: 'Clean Duplicates',
      cleanDuplicatesDesc: 'Remove duplicate ratings from production database',
      cleaning: 'Cleaning...',
      backupInfo: 'Backup Information',
      backupSchedule: 'Backup Schedule',
      schedule1: 'Auto backup every 6 hours (09:00, 15:00, 21:00, 03:00 KST)',
      schedule2: 'GitHub Artifacts: Last 30 backups (~7.5 days)',
      schedule3: 'GitHub Releases: 1 daily permanent backup',
      viewBackups: 'View Backups',
      githubActions: 'Check backups in GitHub Actions',
      githubReleases: 'Check long-term backups in GitHub Releases',
      docs: 'Backup Guide',
      viewDocs: 'View BACKUP_GUIDE.md'
    }
  };

  const t = text[language] || text.en;

  const handleCleanDuplicates = async () => {
    if (!confirm('중복 데이터를 제거하시겠습니까? 최신 평가만 유지하고 나머지는 삭제됩니다.')) {
      return;
    }

    setCleaningDuplicates(true);
    setMessage('');

    try {
      const response = await fetch(`${API_BASE_URL}/api/admin/clean-duplicates`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();

      if (data.success) {
        const total = data.total_removed || 0;
        setMessage(`✅ 완료! 총 ${total}개 중복 제거됨\n` +
          `- 캐릭터 평가: ${data.character_ratings_removed}\n` +
          `- 애니 평가: ${data.user_ratings_removed}\n` +
          `- 캐릭터 활동: ${data.character_activities_removed}\n` +
          `- 애니 활동: ${data.anime_activities_removed}`
        );
      } else {
        setMessage('❌ 제거 실패: ' + (data.detail || 'Unknown error'));
      }
    } catch (error) {
      console.error('Error cleaning duplicates:', error);
      setMessage('❌ 에러: ' + error.message);
    } finally {
      setCleaningDuplicates(false);
    }
  };

  return (
    <div className="min-h-screen pt-10 md:pt-12 bg-transparent">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* 헤더 */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-text-primary mb-2">{t.title}</h1>
          <p className="text-text-secondary">{t.subtitle}</p>
        </div>

        {/* 메시지 */}
        {message && (
          <div className="mb-6 p-4 bg-surface-elevated rounded-lg border border-border">
            <pre className="text-sm text-text-primary whitespace-pre-wrap font-mono">
              {message}
            </pre>
          </div>
        )}

        {/* 중복 제거 섹션 */}
        <div className="bg-surface rounded-lg border border-border p-6 mb-6">
          <h2 className="text-xl font-bold text-text-primary mb-4">{t.cleanDuplicates}</h2>
          <p className="text-text-secondary mb-4">{t.cleanDuplicatesDesc}</p>

          <button
            onClick={handleCleanDuplicates}
            disabled={cleaningDuplicates}
            className="px-6 py-3 bg-accent hover:bg-accent-hover text-white rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {cleaningDuplicates ? t.cleaning : t.cleanDuplicates}
          </button>
        </div>

        {/* 백업 정보 섹션 */}
        <div className="bg-surface rounded-lg border border-border p-6 mb-6">
          <h2 className="text-xl font-bold text-text-primary mb-4">{t.backupInfo}</h2>

          <div className="space-y-4">
            <div>
              <h3 className="font-semibold text-text-primary mb-2">{t.backupSchedule}</h3>
              <ul className="list-disc list-inside space-y-1 text-text-secondary">
                <li>{t.schedule1}</li>
                <li>{t.schedule2}</li>
                <li>{t.schedule3}</li>
              </ul>
            </div>

            <div>
              <h3 className="font-semibold text-text-primary mb-2">{t.viewBackups}</h3>
              <div className="space-y-2">
                <a
                  href="https://github.com/seojoonkim/anibite/actions/workflows/backup-db.yml"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block px-4 py-2 bg-surface-elevated hover:bg-surface-hover border border-border rounded-lg transition-colors"
                >
                  <span className="text-text-primary font-medium">📊 {t.githubActions}</span>
                </a>
                <a
                  href="https://github.com/seojoonkim/anibite/releases"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block px-4 py-2 bg-surface-elevated hover:bg-surface-hover border border-border rounded-lg transition-colors"
                >
                  <span className="text-text-primary font-medium">💾 {t.githubReleases}</span>
                </a>
              </div>
            </div>

            <div>
              <h3 className="font-semibold text-text-primary mb-2">{t.docs}</h3>
              <a
                href="https://github.com/seojoonkim/anibite/blob/main/BACKUP_GUIDE.md"
                target="_blank"
                rel="noopener noreferrer"
                className="block px-4 py-2 bg-surface-elevated hover:bg-surface-hover border border-border rounded-lg transition-colors"
              >
                <span className="text-text-primary font-medium">📖 {t.viewDocs}</span>
              </a>
            </div>
          </div>
        </div>

        {/* 현재 시간 (참고용) */}
        <div className="text-center text-sm text-text-secondary">
          Last updated: {new Date().toLocaleString('ko-KR', { timeZone: 'Asia/Seoul' })} KST
        </div>
      </div>
    </div>
  );
}
