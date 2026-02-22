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
│   ├── public/data
│   │   ├── feed.json
│   │   └── articles/{id}.json
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
- Frontend: http://localhost:3000/News/news
- Backend: http://localhost:8000/docs

### 2) RSS 소스 시드 (예시 10개)
```bash
make seed
```

### 3) 수집 실행
```bash
curl -X POST http://localhost:8000/ingest/run
```

## 정적 데이터 스키마 (GitHub Pages export)

### `frontend/public/data/feed.json`
`/news` 목록 화면에서 사용하는 배열 데이터.

```json
[
  {
    "id": "a01",
    "title": "기사 제목",
    "source": "매체명",
    "topic": "ai",
    "published_at": "2026-02-22T12:00:00Z",
    "importance": 87,
    "one_liner": "한 줄 요약"
  }
]
```

필드 설명:
- `id` (string): 상세 JSON 파일명과 동일한 고유 ID
- `topic` (`ai` | `scitech`)
- `importance` (number): 중요도 정렬용 점수

### `frontend/public/data/articles/{id}.json`
`/news/[id]` 상세 화면에서 사용하는 단일 객체 데이터.

```json
{
  "id": "a01",
  "title": "기사 제목",
  "source": "매체명",
  "topic": "ai",
  "published_at": "2026-02-22T12:00:00Z",
  "url": "https://example.com/articles/a01",
  "one_liner": "한 줄 요약",
  "summary_lines": ["3~5줄 요약 1", "요약 2", "요약 3"],
  "key_points": ["핵심 포인트 1", "핵심 포인트 2"],
  "related": [
    {
      "id": "a02",
      "title": "연관 기사 제목",
      "source": "매체명",
      "published_at": "2026-02-22T08:00:00Z"
    }
  ]
}
```

## API

### POST `/ingest/run`
모든 enabled RSS 소스를 가져와 새 기사를 저장합니다.
- 중복 기준: `url_canonical`
- 본문 추출: 현재 snippet 기반 (`TODO`로 확장 포인트 유지)

### GET `/feed?topic=ai&range=24h`
주제별 최신 기사 목록(요약 포함) 반환.

### GET `/article/{id}`
기사 상세(요약 + 원문 링크) 반환.

## 요약기 전략
- 현재: 규칙 기반(문장 3~5개 추출)
- 추후: `LLMSummarizerStub` 인터페이스에 실제 LLM 호출 구현
