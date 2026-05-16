"""Tests for rule-driven deterministic analysis."""

from pathlib import Path

from repoquest.detectors import detect_framework, generate_fingerprint
from repoquest.framework_rules import EXPRESS_RULE
from repoquest.import_graph import build_import_graph
from repoquest.models import FileInfo, RepositorySnapshot
from repoquest.quest import generate_component_cards, generate_quiz
from repoquest.reading_path import generate_reading_path
from repoquest.response_templates import get_role_label, get_understand_points_for_file
from repoquest.route_extractors import extract_all_routes
from repoquest.scanner import guess_file_role
from repoquest.workflows import generate_work_plan


def _file(path: str, text: str, language: str = "Unknown") -> FileInfo:
  path_obj = Path(path)
  return FileInfo(
    path=path,
    name=path_obj.name,
    suffix=path_obj.suffix,
    size_bytes=len(text.encode("utf-8")),
    language=language,
    role=guess_file_role(path_obj),
    text_preview=text,
    line_count=max(1, text.count("\n") + 1),
  )


def _alternate_snapshot() -> RepositorySnapshot:
  files = [
    _file("README.md", "# Inventory Desk\n\nSmall inventory dashboard.", "Markdown"),
    _file(
      "frontend/package.json",
      '{"dependencies": {"@vitejs/plugin-react": "latest", "react": "^18.0.0"}}',
      "JSON",
    ),
    _file("frontend/vite.config.ts", "import { defineConfig } from 'vite'", "TypeScript"),
    _file(
      "frontend/src/main.tsx",
      "import React from 'react';\nimport Dashboard from './Dashboard';",
      "TypeScript",
    ),
    _file(
      "frontend/src/Dashboard.tsx",
      "import CatalogPage from './pages/CatalogPage';\nexport default function Dashboard() { return <CatalogPage />; }",
      "TypeScript",
    ),
    _file(
      "frontend/src/pages/CatalogPage.tsx",
      "import { listItems } from '../services/client';\nexport function CatalogPage() { return null; }",
      "TypeScript",
    ),
    _file(
      "frontend/src/services/client.ts",
      "export async function listItems() { return fetch('/api/items'); }",
      "TypeScript",
    ),
    _file(
      "backend/main.py",
      "from fastapi import FastAPI\nfrom routes import inventory_router\napp = FastAPI()\napp.include_router(inventory_router.router, prefix='/api')",
      "Python",
    ),
    _file(
      "backend/routes/inventory_router.py",
      "from fastapi import APIRouter\nfrom services.catalog_service import list_items\nrouter = APIRouter()\n@router.get('/items')\ndef get_items():\n  return list_items()",
      "Python",
    ),
    _file(
      "backend/services/catalog_service.py",
      "from models.item_record import ItemRecord\ndef list_items():\n  return [ItemRecord(id='1', name='Notebook')]",
      "Python",
    ),
    _file(
      "backend/models/item_record.py",
      "from pydantic import BaseModel\nclass ItemRecord(BaseModel):\n  id: str\n  name: str",
      "Python",
    ),
    _file(
      "backend/tests/test_inventory.py",
      "from main import app\ndef test_get_items():\n  assert app is not None",
      "Python",
    ),
  ]
  return RepositorySnapshot(
    source_name="inventory_fixture",
    files=files,
    total_files_seen=len(files),
    total_files_scanned=len(files),
    warnings=[],
  )


def test_alternate_repo_generates_deterministic_outputs_without_demo_names():
  """A non-demo full-stack repo should produce useful output from generic rules."""
  snapshot = _alternate_snapshot()
  fingerprint = generate_fingerprint(snapshot)
  routes = extract_all_routes(snapshot.files)
  import_edges = build_import_graph(snapshot.files, "")
  reading_path = generate_reading_path(snapshot, fingerprint)
  component_cards = generate_component_cards(snapshot, fingerprint, routes)
  quiz = generate_quiz(snapshot, fingerprint, routes)
  work_plan = generate_work_plan(snapshot, fingerprint, routes, import_edges, reading_path, component_cards)

  framework_names = [framework.name for framework in fingerprint.frameworks]
  assert "React + Vite" in framework_names
  assert "FastAPI" in framework_names
  assert fingerprint.project_type == "Full-stack web application"
  assert any(path == "frontend/src/main.tsx" for path in fingerprint.entry_points)
  assert any(route.path in {"/api/items", "/items"} for route in routes)
  assert any(item.path == "backend/routes/inventory_router.py" for item in reading_path)
  assert any(card.path == "backend/routes/inventory_router.py" for card in component_cards)
  assert quiz
  assert work_plan.tasks

  generated_text = "\n".join(
    [fingerprint.summary]
    + [item.path for item in reading_path]
    + [card.path for card in component_cards]
    + [question.question for question in quiz]
    + [option for question in quiz for option in question.options]
  )
  for demo_only_name in ("TripsPage", "TripCard", "SearchForm", "mini_travel_planner"):
    assert demo_only_name not in generated_text


def test_express_not_detected_from_weak_route_like_signal():
  """Generic app.get text should not trigger Express without stronger evidence."""
  snapshot = RepositorySnapshot(
    source_name="weak_js",
    files=[
      _file(
        "src/router.js",
        "export function register(app) { app.get('/items', () => null); }",
        "JavaScript",
      )
    ],
    total_files_seen=1,
    total_files_scanned=1,
    warnings=[],
  )

  assert detect_framework(EXPRESS_RULE, snapshot) is None


def test_response_templates_have_generic_fallbacks():
  """Unknown roles should still get deterministic generic guidance."""
  file_info = _file("misc/tool.notes", "notes")
  assert get_role_label(file_info.role) == "Unknown"
  points = get_understand_points_for_file(file_info)
  assert points
  assert any("purpose" in point.lower() for point in points)


def test_repoquest_core_does_not_reference_demo_specific_filenames():
  """Production analysis code should not special-case bundled demo filenames."""
  repoquest_dir = Path(__file__).resolve().parents[1] / "repoquest"
  allowed_files = {"sample_loader.py"}
  forbidden_terms = (
    "TripsPage",
    "TripCard",
    "SearchForm",
    "mini_travel_planner",
    "recommendations.py",
    "trips.py",
    "api.ts",
  )

  for path in repoquest_dir.glob("*.py"):
    if path.name in allowed_files:
      continue
    text = path.read_text(encoding="utf-8")
    for term in forbidden_terms:
      assert term not in text, f"{term} should not appear in {path.name}"

# Made with Bob
