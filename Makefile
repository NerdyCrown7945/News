.PHONY: dev down seed ingest

dev:
	docker compose up --build

down:
	docker compose down -v

seed:
	docker compose run --rm backend python scripts/seed_sources.py

ingest:
	curl -X POST http://localhost:8000/ingest/run
