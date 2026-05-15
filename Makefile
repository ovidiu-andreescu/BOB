SYSTEM_PYTHON ?= python3
VENV ?= .venv
VENV_PYTHON := $(VENV)/bin/python
PYTHON ?= $(VENV_PYTHON)
PIP := $(PYTHON) -m pip
APP := app/streamlit_app.py

.PHONY: help python-info venv install install-dev upgrade-pip run run-direct test lint lint-fix qa sync-cloud-config check-cloud-config clean demo-path

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
	@printf "  make test                Run pytest\n"
	@printf "  make lint                Run ruff check\n"
	@printf "  make lint-fix            Run ruff check --fix\n"
	@printf "  make sync-cloud-config   Copy infra/streamlit config into .streamlit/config.toml\n"
	@printf "  make check-cloud-config  Validate cloud config mirror\n"
	@printf "  make qa                  Run config check, lint, and tests\n"
	@printf "  make clean               Remove local cache directories\n"
	@printf "  make demo-path           Print bundled demo repo path\n"

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
