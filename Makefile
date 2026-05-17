SYSTEM_PYTHON ?= python3
VENV ?= .venv
VENV_PYTHON := $(VENV)/bin/python
PYTHON ?= $(VENV_PYTHON)
PIP := $(PYTHON) -m pip
APP := app/streamlit_app.py
LOCAL_MODEL_BASE_URL ?= http://localhost:11434/v1
LOCAL_MODEL_NAME ?= gemma3:4b
ASSISTANT_SERVICE_URL ?= http://localhost:8765

.PHONY: help python-info venv install install-dev upgrade-pip run run-direct run-ai-mock run-ai-local run-ai-claude run-ai-service assistant-service assistant-service-mock assistant-service-local test lint lint-fix qa sync-cloud-config check-cloud-config clean demo-path docker-run docker-run-assistant docker-run-local docker-run-claude

help:
	@printf "RepoQuest commands\n"
	@printf "\n"
	@printf "  make python-info         Show Python and pip versions\n"
	@printf "  make venv                Create a local virtual environment in .venv\n"
	@printf "  make install             Install runtime dependencies\n"
	@printf "  make install-dev         Install runtime and development dependencies\n"
	@printf "  make upgrade-pip         Upgrade pip in the selected Python environment\n"
	@printf "  make run                 Run RepoQuest via scripts/run_local.py\n"
	@printf "  make run-direct          Run Streamlit directly\n"
	@printf "  make run-ai-mock         Run Streamlit with direct mock AI enabled\n"
	@printf "  make run-ai-local        Run Streamlit with direct local OpenAI-compatible model\n"
	@printf "  make run-ai-claude       Run Streamlit with direct Claude provider; requires CLAUDE_API_KEY\n"
	@printf "  make run-ai-service      Run Streamlit connected to ASSISTANT_SERVICE_URL\n"
	@printf "  make assistant-service   Run async assistant service; provider comes from env\n"
	@printf "  make assistant-service-mock Run async assistant service in mock mode\n"
	@printf "  make assistant-service-local Run async assistant service with local model\n"
	@printf "  make test                Run pytest\n"
	@printf "  make lint                Run ruff check\n"
	@printf "  make lint-fix            Run ruff check --fix\n"
	@printf "  make sync-cloud-config   Copy infra/streamlit config into .streamlit/config.toml\n"
	@printf "  make check-cloud-config  Validate cloud config mirror\n"
	@printf "  make qa                  Run config check, lint, and tests\n"
	@printf "  make clean               Remove local cache directories\n"
	@printf "  make demo-path           Print bundled demo repo path\n"
	@printf "  make docker-run          Run deterministic app with Docker Compose\n"
	@printf "  make docker-run-assistant Run app plus async assistant service in mock mode\n"
	@printf "  make docker-run-local    Run app plus assistant service targeting local model\n"
	@printf "  make docker-run-claude   Run app plus assistant service targeting Claude; requires CLAUDE_API_KEY\n"

python-info:
	@printf "System Python: "
	@$(SYSTEM_PYTHON) --version
	@if [ -x "$(VENV_PYTHON)" ]; then \
		printf "Virtualenv Python: "; \
		$(VENV_PYTHON) --version; \
		$(VENV_PYTHON) -m pip --version; \
	else \
		printf "Virtualenv Python: not created yet. Run 'make venv'.\n"; \
	fi

venv: $(VENV_PYTHON)

$(VENV_PYTHON):
	$(SYSTEM_PYTHON) -m venv $(VENV)

install: venv
	$(PIP) install -r infra/streamlit/requirements.txt

install-dev: venv
	$(PIP) install -r infra/local/requirements-dev.txt

upgrade-pip: venv
	$(PIP) install --upgrade pip

run: venv
	$(PYTHON) scripts/run_local.py

run-direct: venv
	$(PYTHON) -m streamlit run $(APP) --server.maxUploadSize=25 --server.runOnSave=true

run-ai-mock: venv
	REPOQUEST_AI_ENABLED=true \
	REPOQUEST_ASSISTANT_PROVIDER=mock \
	$(PYTHON) -m streamlit run $(APP) --server.maxUploadSize=25 --server.runOnSave=true

run-ai-local: venv
	REPOQUEST_AI_ENABLED=true \
	REPOQUEST_ASSISTANT_PROVIDER=local \
	REPOQUEST_LOCAL_MODEL_BASE_URL=$(LOCAL_MODEL_BASE_URL) \
	REPOQUEST_LOCAL_MODEL_NAME=$(LOCAL_MODEL_NAME) \
	$(PYTHON) -m streamlit run $(APP) --server.maxUploadSize=25 --server.runOnSave=true

run-ai-claude: venv
	REPOQUEST_AI_ENABLED=true \
	REPOQUEST_ASSISTANT_PROVIDER=claude \
	$(PYTHON) -m streamlit run $(APP) --server.maxUploadSize=25 --server.runOnSave=true

run-ai-service: venv
	REPOQUEST_AI_ENABLED=true \
	REPOQUEST_ASSISTANT_SERVICE_URL=$(ASSISTANT_SERVICE_URL) \
	$(PYTHON) -m streamlit run $(APP) --server.maxUploadSize=25 --server.runOnSave=true

assistant-service: venv
	$(PYTHON) -m services.assistant_service

assistant-service-mock: venv
	REPOQUEST_AI_ENABLED=true \
	REPOQUEST_ASSISTANT_SERVICE_PROVIDER=mock \
	$(PYTHON) -m services.assistant_service

assistant-service-local: venv
	REPOQUEST_AI_ENABLED=true \
	REPOQUEST_ASSISTANT_SERVICE_PROVIDER=local \
	REPOQUEST_LOCAL_MODEL_BASE_URL=$(LOCAL_MODEL_BASE_URL) \
	REPOQUEST_LOCAL_MODEL_NAME=$(LOCAL_MODEL_NAME) \
	$(PYTHON) -m services.assistant_service

test: venv
	$(PYTHON) -m pytest -q

lint: venv
	$(PYTHON) -m ruff check .

lint-fix: venv
	$(PYTHON) -m ruff check . --fix

sync-cloud-config: venv
	$(PYTHON) scripts/sync_streamlit_cloud_config.py --write

check-cloud-config: venv
	$(PYTHON) scripts/sync_streamlit_cloud_config.py --check

qa: check-cloud-config lint test

clean:
	find . -type d \( -name __pycache__ -o -name .pytest_cache -o -name .ruff_cache -o -name .mypy_cache \) -prune -exec rm -rf {} +

demo-path:
	@printf "%s\n" "examples/demo_repos/mini_travel_planner"

docker-run:
	docker compose up --build repoquest

docker-run-assistant:
	REPOQUEST_AI_ENABLED=true \
	REPOQUEST_ASSISTANT_SERVICE_URL=http://assistant:8765 \
	REPOQUEST_ASSISTANT_SERVICE_PROVIDER=mock \
	docker compose --profile assistant up --build

docker-run-local:
	REPOQUEST_AI_ENABLED=true \
	REPOQUEST_ASSISTANT_SERVICE_URL=http://assistant:8765 \
	REPOQUEST_ASSISTANT_SERVICE_PROVIDER=local \
	REPOQUEST_LOCAL_MODEL_BASE_URL=http://host.docker.internal:11434/v1 \
	REPOQUEST_LOCAL_MODEL_NAME=$(LOCAL_MODEL_NAME) \
	docker compose --profile assistant up --build

docker-run-claude:
	REPOQUEST_AI_ENABLED=true \
	REPOQUEST_ASSISTANT_SERVICE_URL=http://assistant:8765 \
	REPOQUEST_ASSISTANT_SERVICE_PROVIDER=claude \
	docker compose --profile assistant up --build
