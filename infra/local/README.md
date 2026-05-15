# Local Development Profile

This profile is for local development, testing, and demo iteration.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r infra/local/requirements-dev.txt
python scripts/run_local.py
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r infra/local/requirements-dev.txt
python scripts/run_local.py
```

Useful Make targets:

```bash
make install-dev
make run
make test
make lint
make qa
```
