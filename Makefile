.DEFAULT_GOAL := help
.PHONY: help up up-build down logs ps test-backend test-frontend migrate clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

up: ## Start the full stack (db, backend, frontend) in the foreground
	docker compose up --build

up-build: ## Rebuild images without starting containers (e.g. after a dependency change)
	docker compose build

down: ## Stop the stack and remove its containers
	docker compose down

logs: ## Follow logs of all running services
	docker compose logs -f

ps: ## List the stack's containers and their status
	docker compose ps

migrate: ## Apply backend database migrations by hand (normally automatic on `make up`)
	docker compose exec backend uv run alembic upgrade head

test-backend: ## Run the backend test suite against a disposable test database
	docker compose --profile test up --build --abort-on-container-exit --exit-code-from backend-test test-db backend-test
	docker compose --profile test down

test-frontend: ## Run the frontend test suite
	docker compose run --build --rm frontend npm test -- --watchAll=false

clean: ## Stop the stack and remove its volumes (database data, installed deps)
	docker compose down --volumes
