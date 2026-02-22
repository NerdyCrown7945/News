# News MVP (Local-First)

AI/과학기술 RSS를 수집하고, SQLite에 저장하고, 한국어 더미 요약을 제공하는 로컬 MVP입니다.

## 현재 구조
- `backend/` FastAPI + SQLite(`backend/data/news.db`)
- `frontend/` Next.js UI (백엔드 API 호출)
- `backend/sources.json` RSS 소스(토픽: `ai`, `scitech`)

## 백엔드 기능
- `GET /health`
- `POST /ingest/run` RSS 수집 실행
- `GET /feed?topic=ai|scitech|all&range=24h|7d|30d&query=...&tags=...&sort=new`
- `GET /article/{id}`
- `GET /search?query=...&from=YYYY-MM-DD&to=YYYY-MM-DD&topic=...`

수집 파이프라인:
- RSS 파싱(feedparser)
- URL canonicalization(utm 제거)
- 본문 추출(urllib 기반 간단 추출, 실패 시 snippet fallback)
- 중복 제거(url_canonical + 제목 유사도)
- 규칙 기반 요약/번역 더미(`backend/app/llm.py`)

## Windows 기준 로컬 실행

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

## 비고
- GitHub Pages 워크플로는 유지되며, 로컬 MVP는 API 기반으로 동작합니다.
- 추후 `OPENAI_API_KEY`를 사용해 `backend/app/llm.py`의 TODO 지점을 실제 LLM 호출로 교체할 수 있습니다.
