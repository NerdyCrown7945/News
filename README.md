# AI & Science/Tech News Digest

RSS 기반으로 뉴스를 수집/요약해 `frontend/public/data` 정적 JSON을 생성하는 프로젝트입니다.

## 핵심 동작

`backend/scripts/generate_news_data.py` 실행 시 아래를 자동 수행합니다.

1. `backend/sources.json`의 RSS 목록 로드 (`ai` / `scitech` topic 구분)
2. 피드 파싱 + 네트워크 타임아웃/실패 내성 처리
3. 중복 제거
   - `url_canonical` 기준
   - 제목 유사도(SequenceMatcher) 기준
4. 규칙 기반 요약 생성
   - 첫 문단
   - 핵심 문장(길이/문장 분해 기반)
   - LLM 확장용 인터페이스(`LLMSummarizerStub`) 유지
5. 결과 저장
   - `frontend/public/data/feed.json`
   - `frontend/public/data/articles/{id}.json`

## 실행 방법

```bash
pip install -r backend/requirements.txt
python backend/scripts/generate_news_data.py --sources backend/sources.json --output frontend/public
```

## 출력 스키마

### `frontend/public/data/feed.json`

```json
[
  {
    "id": "string",
    "title": "string",
    "source": "string",
    "published_at": "ISO8601",
    "topic": "ai|scitech",
    "one_liner": "string",
    "tags": ["string"],
    "url": "string",
    "cluster_id": "string"
  }
]
```

### `frontend/public/data/articles/{id}.json`

```json
{
  "id": "string",
  "title": "string",
  "summary_lines": ["string"],
  "key_points": ["string"],
  "url": "string",
  "related": [
    {
      "id": "string",
      "title": "string",
      "source": "string",
      "published_at": "ISO8601"
    }
  ]
}
```

## 소스 추가/수정 방법

초기 소스는 `backend/sources.json`에 16개가 들어 있습니다.

각 항목 형식:

```json
{
  "name": "매체명",
  "topic": "ai",
  "feed_url": "https://.../rss.xml",
  "tags": ["llm", "research"],
  "enabled": true
}
```

- `topic`은 반드시 `ai` 또는 `scitech`
- `enabled: false`로 일시 비활성화 가능
- 태그는 프론트 필터/표시 확장용 메타데이터

## GitHub Actions 자동화

- `.github/workflows/update-news-data.yml`
  - 하루 2회(`0 */12 * * *`) + 수동 실행
  - 데이터 생성 후 변경 사항이 있으면 자동 커밋/푸시
- `.github/workflows/main.yml`
  - GitHub Pages 정적 배포 워크플로우

즉, 데이터 워크플로우가 JSON을 갱신해 푸시하면 Pages 배포 워크플로우가 후속 실행됩니다.
