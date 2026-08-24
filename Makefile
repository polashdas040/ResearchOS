.PHONY: dev test lint format migrate migration

dev:
	docker compose up --build

test:
	pytest -q
	npm.cmd --workspace apps/web test -- --runInBand

lint:
	ruff check .
	mypy apps packages
	npm.cmd --workspace apps/web run lint

format:
	ruff format .
	ruff check --fix .
	npm.cmd --workspace apps/web format

migrate:
	alembic upgrade head

migration:
	alembic revision --autogenerate -m "$(message)"
