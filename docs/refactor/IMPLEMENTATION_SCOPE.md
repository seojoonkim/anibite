# Implementation coordination
User approved all improvements and subsequently authorized finishing and deployment. Push/deploy only after quality gates, independent review, verified production backup and explicit migration readiness. Never publish database contents or credentials.
Backend worker owns backend/**, pytest.ini, docker-startup.sh and migration docs.
Data frontend worker owns frontend/src/services/**, hooks/**, pages/Browse.jsx, pages/Feed.jsx and tests/data*.test.*.
UX worker owns App.jsx, components/**, context/**, pages/Login/Register/Rate/RateCharacters/WriteReviews/AnimeDetail/CharacterDetail/Settings/Leaderboard/MyAniPass.jsx, index.css, styles/**, index.html, tailwind config, UX tests.
Parent owns package files, test infrastructure, e2e/local fixtures, CI/docs, integration/verification.
Never revert another worker edits. Test first, record RED/GREEN, no commits until independent review.
