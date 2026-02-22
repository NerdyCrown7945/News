.PHONY: dev down backend-dev frontend-dev ingest

dev:
	docker compose up --build

down:
	docker compose down -v

backend-dev:
	uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000

frontend-dev:
	cd frontend && npm run dev

ingest:
	curl -X POST http://127.0.0.1:8000/ingest/run
