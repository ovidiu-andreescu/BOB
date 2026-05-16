"""Tests for test intelligence module."""

import pytest
from repoquest.models import RepositorySnapshot, FileInfo, RouteInfo, ComponentCard
from repoquest.test_intelligence import (
  get_test_inventory,
  detect_test_framework,
  extract_test_quality_signals,
  generate_test_intelligence,
)


def test_get_test_inventory_excludes_init_files():
  """Test that __init__.py files are excluded from test inventory."""
  snapshot = RepositorySnapshot(
    source_name="test",
    files=[
      FileInfo(
        path="tests/__init__.py",
        name="__init__.py",
        suffix=".py",
        size_bytes=10,
        language="python",
        role="test",
        text_preview="",
        line_count=1,
        skipped=False,
      ),
      FileInfo(
        path="tests/test_trips.py",
        name="test_trips.py",
        suffix=".py",
        size_bytes=500,
        language="python",
        role="test",
        text_preview="def test_something(): assert True",
        line_count=50,
        skipped=False,
      ),
    ],
    total_files_seen=2,
    total_files_scanned=2,
    warnings=[],
  )

  inventory = get_test_inventory(snapshot)
  assert len(inventory) == 1
  assert inventory[0].path == "tests/test_trips.py"


def test_detect_test_framework_pytest():
  """Test pytest framework detection."""
  file_info = FileInfo(
    path="test_example.py",
    name="test_example.py",
    suffix=".py",
    size_bytes=100,
    language="python",
    role="test",
    text_preview="import pytest\ndef test_something():\n  assert True",
    line_count=3,
    skipped=False,
  )

  framework = detect_test_framework(file_info)
  assert framework == "pytest"


def test_extract_test_quality_signals():
  """Test quality signals extraction."""
  file_info = FileInfo(
    path="test_example.py",
    name="test_example.py",
    suffix=".py",
    size_bytes=200,
    language="python",
    role="test",
    text_preview="""
import pytest
from fastapi.testclient import TestClient

def test_something():
  assert 1 == 1
  assert True
""",
    line_count=7,
    skipped=False,
  )

  signals = extract_test_quality_signals(file_info)
  assert signals["assertion_count"] >= 2
  assert signals["has_test_client"] is True


def test_generate_test_intelligence_with_demo_repo():
  """Test that test intelligence generates for demo repo structure."""
  snapshot = RepositorySnapshot(
    source_name="demo",
    files=[
      FileInfo(
        path="backend/tests/test_trips.py",
        name="test_trips.py",
        suffix=".py",
        size_bytes=1000,
        language="python",
        role="test",
        text_preview="""
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_list_trips():
  response = client.get("/api/trips")
  assert response.status_code == 200
""",
        line_count=50,
        skipped=False,
      ),
      FileInfo(
        path="backend/main.py",
        name="main.py",
        suffix=".py",
        size_bytes=500,
        language="python",
        role="entrypoint",
        text_preview="from fastapi import FastAPI\napp = FastAPI()",
        line_count=20,
        skipped=False,
      ),
    ],
    total_files_seen=2,
    total_files_scanned=2,
    warnings=[],
  )

  routes = [
    RouteInfo(
      framework="FastAPI",
      method="GET",
      path="/api/trips",
      file_path="backend/routes/trips.py",
      function_name="list_trips",
    )
  ]

  test_intel = generate_test_intelligence(
    snapshot=snapshot,
    routes=routes,
    import_edges=[],
    component_cards=[],
  )

  assert len(test_intel.test_insights) == 1
  assert test_intel.test_insights[0].test_file == "backend/tests/test_trips.py"
  assert test_intel.test_insights[0].framework == "pytest"
  assert test_intel.test_insights[0].quality_signals["has_test_client"] is True
  assert test_intel.test_insights[0].quality_signals["assertion_count"] > 0


def test_test_intelligence_detects_missing_coverage():
  """Test that missing coverage is detected."""
  snapshot = RepositorySnapshot(
    source_name="demo",
    files=[
      FileInfo(
        path="backend/routes/trips.py",
        name="trips.py",
        suffix=".py",
        size_bytes=500,
        language="python",
        role="backend_route",
        text_preview="",
        line_count=20,
        skipped=False,
      ),
    ],
    total_files_seen=1,
    total_files_scanned=1,
    warnings=[],
  )

  routes = [
    RouteInfo(
      framework="FastAPI",
      method="POST",
      path="/api/trips",
      file_path="backend/routes/trips.py",
      function_name="create_trip",
    )
  ]

  test_intel = generate_test_intelligence(
    snapshot=snapshot,
    routes=routes,
    import_edges=[],
    component_cards=[],
  )

  assert len(test_intel.missing_coverage) > 0


def test_test_plan_uses_safe_wording():
  """Test that test plan uses trusted local clone wording."""
  snapshot = RepositorySnapshot(
    source_name="demo",
    files=[
      FileInfo(
        path="backend/tests/test_trips.py",
        name="test_trips.py",
        suffix=".py",
        size_bytes=100,
        language="python",
        role="test",
        text_preview="def test_something(): pass",
        line_count=10,
        skipped=False,
      ),
    ],
    total_files_seen=1,
    total_files_scanned=1,
    warnings=[],
  )

  test_intel = generate_test_intelligence(
    snapshot=snapshot,
    routes=[],
    import_edges=[],
    component_cards=[],
  )

  assert "trusted local clone" in test_intel.test_plan.lower()
  assert "repoquest" not in test_intel.test_plan.lower() or "do not" in test_intel.test_plan.lower()


def test_map_targets_does_not_match_by_basename_substring():
  """Test that backend/tests/test_trips.py does not map to frontend/src/main.tsx by substring."""
  from repoquest.test_intelligence import map_test_to_likely_targets
  from repoquest.models import ImportEdge

  snapshot = RepositorySnapshot(
    source_name="demo",
    files=[
      FileInfo(
        path="backend/tests/test_trips.py",
        name="test_trips.py",
        suffix=".py",
        size_bytes=500,
        language="python",
        role="test",
        text_preview="from backend.main import app",
        line_count=20,
        skipped=False,
      ),
      FileInfo(
        path="backend/main.py",
        name="main.py",
        suffix=".py",
        size_bytes=300,
        language="python",
        role="entrypoint",
        text_preview="from fastapi import FastAPI",
        line_count=15,
        skipped=False,
      ),
      FileInfo(
        path="frontend/src/main.tsx",
        name="main.tsx",
        suffix=".tsx",
        size_bytes=200,
        language="typescript",
        role="entrypoint",
        text_preview="import React from 'react'",
        line_count=10,
        skipped=False,
      ),
      FileInfo(
        path="frontend/src/services/api.ts",
        name="api.ts",
        suffix=".ts",
        size_bytes=400,
        language="typescript",
        role="api_client",
        text_preview="export const api = {}",
        line_count=25,
        skipped=False,
      ),
    ],
    total_files_seen=4,
    total_files_scanned=4,
    warnings=[],
  )

  test_file = snapshot.files[0]

  # With import edge
  import_edges = [
    ImportEdge(source="backend/tests/test_trips.py", target="backend/main.py", kind="import", confidence=1.0)
  ]

  targets = map_test_to_likely_targets(test_file, snapshot, import_edges)

  # Should map to backend/main.py only
  assert "backend/main.py" in targets
  assert "frontend/src/main.tsx" not in targets
  assert "frontend/src/services/api.ts" not in targets


def test_covered_routes_requires_evidence_in_test():
  """Test that routes are only marked covered if test content references them."""
  from repoquest.test_intelligence import infer_covered_routes

  test_file = FileInfo(
    path="backend/tests/test_trips.py",
    name="test_trips.py",
    suffix=".py",
    size_bytes=500,
    language="python",
    role="test",
    text_preview="""
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_list_trips():
  response = client.get("/api/trips")
  assert response.status_code == 200

def test_create_trip():
  response = client.post("/api/trips", json={"destination": "Paris"})
  assert response.status_code == 201
""",
    line_count=50,
    skipped=False,
  )

  routes = [
    RouteInfo(framework="FastAPI", method="GET", path="/api/trips", file_path="backend/routes/trips.py", function_name="list_trips"),
    RouteInfo(framework="FastAPI", method="POST", path="/api/trips", file_path="backend/routes/trips.py", function_name="create_trip"),
    RouteInfo(framework="FastAPI", method="GET", path="/", file_path="backend/main.py", function_name="root"),
    RouteInfo(framework="FastAPI", method="GET", path="/health", file_path="backend/main.py", function_name="health"),
  ]

  covered = infer_covered_routes(test_file, ["backend/routes/trips.py", "backend/main.py"], routes)

  # Should only cover routes that appear in test content
  assert "GET /api/trips" in covered
  assert "POST /api/trips" in covered
  assert "GET /" not in covered # Not in test content
  assert "GET /health" not in covered # Not in test content


def test_framework_detection_prefers_vitest_over_jest():
  """Test that vitest is detected before generic jest patterns."""
  vitest_file = FileInfo(
    path="src/App.test.ts",
    name="App.test.ts",
    suffix=".ts",
    size_bytes=200,
    language="typescript",
    role="test",
    text_preview="import { describe, it, expect } from 'vitest'\ndescribe('App', () => { it('works', () => {}) })",
    line_count=10,
    skipped=False,
  )

  framework = detect_test_framework(vitest_file)
  assert framework == "vitest"

# Made with Bob
