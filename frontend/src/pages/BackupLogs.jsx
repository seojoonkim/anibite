import { useLanguage } from '../context/LanguageContext';

const messages = {
  ko: {
    title: '백업과 데이터 관리',
    description: '운영 데이터 변경은 웹 화면이 아닌 별도 관리 절차로 수행합니다.',
    backup: '변경 전에 일관된 백업을 만들고 별도 환경에서 복원 검증을 완료하세요.',
    migration: '중복 정리와 스키마 변경에는 담당자 승인과 버전이 지정된 마이그레이션이 필요합니다.',
    status: '이 화면은 실제 백업 성공 여부나 자동 실행 일정을 확인하지 않습니다. 운영 작업 로그에서 확인하세요.',
    guide: '백업 가이드',
    workflow: '운영 작업 기록',
  },
  ja: {
    title: 'バックアップとデータ管理',
    description: '本番データの変更は、この画面ではなく承認された管理手順で実施します。',
    backup: '変更前に整合性のあるバックアップを取得し、別の環境で復元を検証してください。',
    migration: '重複整理とスキーマ変更には承認とバージョン管理されたマイグレーションが必要です。',
    status: 'この画面ではバックアップの成功や自動実行の予定を確認していません。運用ログを確認してください。',
    guide: 'バックアップガイド', workflow: '運用ログ',
  },
  en: {
    title: 'Backup and data management',
    description: 'Production changes use an approved operations procedure, not a browser action.',
    backup: 'Create a consistent backup and verify restoration in a separate environment before changing data.',
    migration: 'Duplicate cleanup and schema changes require approval and a versioned migration.',
    status: 'This screen does not verify backup success or an automatic schedule. Check the operations logs.',
    guide: 'Backup guide', workflow: 'Operations logs',
  },
};

export default function BackupLogs() {
  const { language } = useLanguage();
  const text = messages[language] || messages.en;
  return (
    <main className="min-h-screen pt-16 pb-24 px-4">
      <section className="max-w-3xl mx-auto bg-surface border border-border rounded-xl p-6 space-y-5" aria-labelledby="backup-title">
        <h1 id="backup-title" className="text-2xl font-bold text-text-primary">{text.title}</h1>
        <p className="text-text-secondary">{text.description}</p>
        <ul className="list-disc pl-5 space-y-3 text-text-primary">
          <li>{text.backup}</li>
          <li>{text.migration}</li>
        </ul>
        <p className="text-sm text-text-secondary">{text.status}</p>
        <div className="flex flex-wrap gap-4">
          <a className="text-primary underline underline-offset-4" href="https://github.com/seojoonkim/anibite/blob/main/BACKUP_GUIDE.md" target="_blank" rel="noopener noreferrer">{text.guide}</a>
          <a className="text-primary underline underline-offset-4" href="https://github.com/seojoonkim/anibite/actions" target="_blank" rel="noopener noreferrer">{text.workflow}</a>
        </div>
      </section>
    </main>
  );
}
