# AI & Science/Tech News Digest (MVP)

FastAPI + Next.js 기반 뉴스 다이제스트 MVP입니다.

## 리포지토리 구조

```
.
├── backend
│   ├── app
│   │   ├── database.py
│   │   ├── ingest.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   └── summarizer.py
│   ├── scripts
│   │   └── seed_sources.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend
│   ├── app
│   │   ├── news
│   │   │   ├── [id]/page.tsx
│   │   │   └── page.tsx
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── components/NewsList.tsx
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── Makefile
└── README.md
```

## 설치/실행

### 1) 개발 실행
```bash
make dev
```
- Frontend: http://localhost:3000/news
- Backend: http://localhost:8000/docs

### 2) RSS 소스 시드 (예시 10개)
```bash
make seed
```

### 3) 수집 실행
```bash
curl -X POST http://localhost:8000/ingest/run
```

## API

### POST `/ingest/run`
모든 enabled RSS 소스를 가져와 새 기사를 저장합니다.
- 중복 기준: `url_canonical`
- 본문 추출: 현재 snippet 기반 (`TODO`로 확장 포인트 유지)

예시 응답:
```json
{
  "fetched_sources": 10,
  "created_articles": 25,
  "skipped_duplicates": 120
}
```

### GET `/feed?topic=ai&range=24h`
주제별 최신 기사 목록(요약 포함) 반환.

예시 응답:
```json
[
  {
    "id": 101,
    "title": "New model update",
    "url": "https://example.com/news/1",
    "source_name": "OpenAI Blog",
    "topic": "ai",
    "published_at": "2026-02-22T09:00:00+00:00",
    "summary": {
      "one_liner": "OpenAI announced ...",
      "summary_lines": ["...", "..."],
      "key_points": ["...", "..."]
    }
  }
]
```

### GET `/article/{id}`
기사 상세(요약 + 원문 링크) 반환.

예시 응답:
```json
{
  "id": 101,
  "title": "New model update",
  "url": "https://example.com/news/1",
  "source_name": "OpenAI Blog",
  "topic": "ai",
  "published_at": "2026-02-22T09:00:00+00:00",
  "snippet": "...",
  "content_text": "...",
  "summary": {
    "one_liner": "OpenAI announced ...",
    "summary_lines": ["...", "..."],
    "key_points": ["...", "..."]
  }
}
```

## 요약기 전략
- 현재: 규칙 기반(문장 3~5개 추출)
- 추후: `LLMSummarizerStub` 인터페이스에 실제 LLM 호출 구현
