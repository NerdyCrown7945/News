# News MVP (Local-First + GitHub Pages Fallback)

AI/과학기술 RSS를 수집하고(SQLite), 한국어 요약(더미)을 제공하는 프로젝트입니다.

## 현재 구조
- `backend/`: FastAPI + SQLite(`backend/data/news.db`)
- `frontend/`: Next.js UI
- `frontend/public/data/`: GitHub Pages용 정적 fallback 데이터(seed)
- `backend/sources.json`: RSS 소스(토픽 `ai`, `scitech`)

## 동작 모드
- **로컬 개발 모드**: 프론트가 `NEXT_PUBLIC_API_BASE`(기본 `http://127.0.0.1:8000`)로 백엔드 API 호출
- **GitHub Pages 모드**: 백엔드가 없으므로 `frontend/public/data` 정적 JSON fallback으로 동작

## 백엔드 API
- `GET /health`
- `POST /ingest/run`
- `GET /feed?topic=ai|scitech|all&range=24h|7d|30d&query=...&tags=...&sort=new`
- `GET /article/{id}`
- `GET /search?query=...&from=YYYY-MM-DD&to=YYYY-MM-DD&topic=...`

## 로컬 실행 (Windows 기준)

### 1) 백엔드
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r backend/requirements.txt
make backend-dev
```

### 2) 수집 실행
```powershell
make ingest
# 또는
curl -X POST http://127.0.0.1:8000/ingest/run
```

### 3) 프론트
```powershell
cd frontend
npm install
# 기본값은 http://127.0.0.1:8000
# 필요 시 변경:
# echo NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000 > .env.local
npm run dev
```

브라우저: `http://127.0.0.1:3000/News/news`

## GitHub Pages 동작 안내
- Pages에는 서버가 없어서 `/feed`, `/ingest/run` 같은 백엔드 API를 직접 사용할 수 없습니다.
- 따라서 Pages에서는 `public/data/feed.json`, `public/data/articles/*.json` 정적 데이터로 자동 fallback합니다.
- 실시간 실데이터를 쓰려면 FastAPI 백엔드를 별도 서버(Render/Railway/Fly.io 등)에 배포한 뒤 `NEXT_PUBLIC_API_BASE`를 해당 URL로 설정해야 합니다.

## UI fallback 표시
- API 실패 시 목록/상세 하단에 `현재는 정적 데이터(샘플/캐시)를 표시 중` 배지가 나타납니다.
- Pages 환경에서는 `수집 실행` 버튼이 비활성화됩니다(로컬에서만 동작).
