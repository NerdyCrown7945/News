# AI & Science/Tech News Digest

RSS 기반으로 뉴스를 수집/요약해 **정적 프론트 데이터(`frontend/public/data`)**와 **모바일/Flutter용 백엔드 API(FastAPI)**를 함께 운영하는 프로젝트입니다.

## 아키텍처 목표

- **현재 배포 프론트**: GitHub Pages(정적) → `public/data` JSON을 직접 읽음
- **장기 모바일 연동**: FastAPI 백엔드가 동일 데이터를 API로 제공
- 즉, 지금은 **빌드 타임 정적 데이터 생성은 유지**하면서, 로컬/서버에서는 **API 엔드포인트도 병행 제공**합니다.

## Backend API (FastAPI)

구현된 엔드포인트:

- `GET /health`
- `GET /feed?topic=ai&range=24h`
- `GET /article/{id}`
- (운영/개발용) `POST /ingest/run`

### 모듈 구조

- `backend/app/api.py`: FastAPI 라우트
- `backend/app/ingest.py`: RSS 수집/정제 파이프라인 실행
- `backend/app/dedupe.py`: URL/제목 중복 제거 유틸
- `backend/app/summarize.py`: 요약 인터페이스 + 규칙 기반 더미 요약기
- `backend/app/store.py`: SQLite 저장소/DB 초기화

기본 DB는 `backend/data.db`(SQLite)입니다.

## 로컬 실행 방법

```bash
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

### 데이터 수집(로컬)

초기 실행 후 소스가 없으면 `backend/sources.json`을 읽어 소스를 자동 생성합니다.

```bash
curl -X POST http://localhost:8000/ingest/run
```

이후 API 호출:

```bash
curl "http://localhost:8000/feed?topic=ai&range=24h"
curl "http://localhost:8000/article/1"
curl "http://localhost:8000/health"
```

## Flutter에서 호출 예시

```dart
final baseUrl = 'https://your-backend.example.com';

// 피드
final feedRes = await http.get(
  Uri.parse('$baseUrl/feed?topic=ai&range=24h'),
);

// 기사 상세
final articleRes = await http.get(
  Uri.parse('$baseUrl/article/123'),
);
```

## 배포 전략 (권장)

- **프론트엔드**: GitHub Pages 유지
  - 기존처럼 `backend/scripts/generate_news_data.py`로 `frontend/public/data` 생성
- **백엔드(FastAPI)**: Render / Railway / Fly.io 중 택1
  - `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
  - 초기에는 SQLite로 시작 가능
  - 트래픽 증가 시 Postgres로 전환(환경변수 `DATABASE_URL`)

## 기존 Pages용 정적 데이터 생성 유지

아래 스크립트는 그대로 유지됩니다.

```bash
python backend/scripts/generate_news_data.py --sources backend/sources.json --output frontend/public
```

생성물:

- `frontend/public/data/feed.json`
- `frontend/public/data/articles/{id}.json`

즉, **GitHub Pages(정적 소비)**와 **모바일/API 소비**를 동시에 지원하는 구조입니다.
