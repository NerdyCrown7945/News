# News MVP (Local-First + GitHub Pages Fallback)

AI/과학기술 RSS를 수집하고, SQLite에 저장하며, 프론트엔드는 **로컬 API 우선 + 정적 JSON fallback** 방식으로 동작하는 프로젝트입니다.

## 프로젝트 구조
- `backend/`: FastAPI + SQLite(`backend/data/news.db`)
- `frontend/`: Next.js UI
- `frontend/public/data/feed.json`: 리스트 화면용 정적 fallback 데이터
- `frontend/public/data/articles/*.json`: 상세 화면용 정적 fallback 데이터

## 동작 모드

### 1) 로컬(Local-First) 모드
- 프론트는 먼저 `NEXT_PUBLIC_API_BASE`(기본값: `http://127.0.0.1:8000`)의 백엔드 API를 호출합니다.
- 예:
  - `GET {NEXT_PUBLIC_API_BASE}/feed?...`
  - `GET {NEXT_PUBLIC_API_BASE}/article/{id}`
  - (로컬 전용) `POST {NEXT_PUBLIC_API_BASE}/ingest/run`
- API 호출이 실패하거나 비정상 응답이면 정적 JSON fallback으로 자동 전환합니다.

### 2) GitHub Pages 모드
- GitHub Pages에서는 백엔드 서버가 없으므로 `/feed`, `/article/{id}`, `/ingest/run` 같은 API를 직접 호출할 수 없습니다.
- 따라서 프론트는 자동으로 아래 정적 데이터를 사용합니다.
  - `/public/data/feed.json`
  - `/public/data/articles/*.json`
- Pages 환경에서는 “수집 실행” 기능이 비활성화되며, 로컬 전용 기능임을 UI로 안내합니다.

## GitHub Pages에서 실데이터를 쓰려면
1. 백엔드를 별도 서버(예: Render, Fly.io, EC2 등)에 배포합니다.
2. 프론트 환경변수 `NEXT_PUBLIC_API_BASE`를 해당 백엔드 URL로 설정합니다.
3. 프론트를 다시 빌드/배포하면 Pages에서도 외부 백엔드 API를 우선 사용하고, 실패 시 정적 fallback을 사용할 수 있습니다.

## 로컬 실행 (Windows 기준)

### 1) Python venv + 백엔드 의존성 설치
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r backend/requirements.txt
```

### 2) 백엔드 실행
```powershell
make backend-dev
```

### 3) 수집 실행
```powershell
make ingest
# 또는
curl -X POST http://127.0.0.1:8000/ingest/run
```

### 4) 프론트 실행
```powershell
cd frontend
npm install
# 선택: API 주소 변경
# echo NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000 > .env.local
npm run dev
```

브라우저: `http://127.0.0.1:3000/News/news`
