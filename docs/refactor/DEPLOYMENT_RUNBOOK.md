# Release deployment gates

This release is NOT deployed merely because tests pass. Record final commit, CI, Railway deployment and Vercel deployment IDs after completing each gate.

## Local verification

Use Python 3.11 (the Docker/CI runtime), not macOS system Python 3.9. Run `python -m pytest backend/tests -q`, `python -m unittest discover -s scripts/tests -v`, pip check/audit and frontend lint/unit/build/audit/Playwright. Only synthetic disposable databases are used by these tests.

## Railway

- Confirm account, project, production service and existing persistent volume before mutations. Known historical project ID from GitHub deployment metadata: `c88822f0-9c6d-4596-96af-73691c3382c5`; environment ID `b4e7e203-8863-4351-a023-d26737e3355a`. These are lookup hints, not proof of current settings.
- The release explicitly selects Dockerfile/Python 3.11, canonical check-only startup and `/ready` health gate. Validate effective configuration and mounted `/app/data`. Do not restart the OLD unsafe downloader implementation.
- Production requires valid injected SECRET_KEY (at least 32 characters), DATABASE_PATH, OAuth/integration settings. Check presence/validity without printing secrets. Do not use development mode as an authentication workaround.
- Obtain private SQLite-backup-API snapshot on the actual volume, check integrity and rehearse migration on a separate restored copy. Never fetch the historical GitHub release database or initialize a missing production DB.
- Freeze migration code before rehearsal; version-1 checksum includes its code/schema payload. Stop all old writers for migration: old trigger-based and new service-based projections are not a rolling-write upgrade.
- Apply approved `python -m migrations migrate`, followed by `python -m migrations check`, only in the verified volume-mounted execution context. Compare data counts, IDs and social references before/after. No implicit init/download/migration at worker startup.
- Railway pre-deploy containers do NOT mount persistent volumes. Do not put SQLite migrations in preDeployCommand. Source: https://docs.railway.com/guides/pre-deploy-command
- Bring up new API, verify `/ready`, public/guarded routes, persistence and logs. Never restore a backup over live writers/sidecars. Rollback must be rehearsed and compatible with trigger retirement.

## Vercel

Existing project `anibite`, project ID `prj_PDhigXpej6Oe1rrSeLqE3Rsn8JL4`, root `frontend`, Vite build `npm run build`, output `dist`. Verify production build variables VITE_API_URL, VITE_IMAGE_BASE_URL and VITE_GOOGLE_CLIENT_ID without exposing values. Upload exclusions must omit backend/database/environment artifacts. Promote only after API readiness, then check www.anibite.com, deep links, actual API calls/CORS and asset loading. Synthetic browser tests do not verify real Google login.

## Existing exposure and backups

The public repository has a historical release asset named anime.db and already tracked DB files. Metadata/paths were checked, not database contents. New upload exclusions and replacement backup workflow do not erase historical exposure or establish automated production backups. Investigation, private encrypted backup retention and any deletion/key rotation require a separate explicit operational decision. See ../SAFE_BACKUPS.md.
