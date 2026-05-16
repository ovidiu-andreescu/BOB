"""Tests for reading path generation."""


from repoquest.sample_loader import load_demo_repo
from repoquest.detectors import generate_fingerprint
from repoquest.reading_path import generate_reading_path
from repoquest.models import RepositorySnapshot, ProjectFingerprint


def test_reading_path_starts_with_readme():
  """Test that reading path starts with README.md for demo repo."""
  snapshot = load_demo_repo()
  fingerprint = generate_fingerprint(snapshot)

  reading_path = generate_reading_path(snapshot, fingerprint)

  assert len(reading_path) > 0
  assert reading_path[0].path.endswith("README.md")
  assert reading_path[0].order == 1


def test_reading_path_includes_backend_route():
  """Test that reading path includes a backend route file."""
  snapshot = load_demo_repo()
  fingerprint = generate_fingerprint(snapshot)

  reading_path = generate_reading_path(snapshot, fingerprint)

  # Should include backend/routes/trips.py
  route_paths = [item.path for item in reading_path if "routes" in item.path.lower()]
  assert len(route_paths) > 0


def test_reading_path_includes_frontend_file():
  """Test that reading path includes a frontend entry or page file."""
  snapshot = load_demo_repo()
  fingerprint = generate_fingerprint(snapshot)

  reading_path = generate_reading_path(snapshot, fingerprint)

  # Should include frontend files like App.tsx or pages
  frontend_paths = [
    item.path for item in reading_path
    if "frontend" in item.path.lower() and item.path.endswith((".tsx", ".jsx"))
  ]
  assert len(frontend_paths) > 0


def test_reading_path_has_estimated_minutes():
  """Test that each reading path item has estimated minutes."""
  snapshot = load_demo_repo()
  fingerprint = generate_fingerprint(snapshot)

  reading_path = generate_reading_path(snapshot, fingerprint)

  for item in reading_path:
    assert item.estimated_minutes > 0
    assert item.estimated_minutes <= 5 # Reasonable upper bound


def test_reading_path_has_reasons():
  """Test that each reading path item has a reason."""
  snapshot = load_demo_repo()
  fingerprint = generate_fingerprint(snapshot)

  reading_path = generate_reading_path(snapshot, fingerprint)

  for item in reading_path:
    assert item.reason
    assert len(item.reason) > 10 # Should be a meaningful reason


def test_reading_path_respects_max_items():
  """Test that reading path respects MAX_READING_PATH_ITEMS limit."""
  from repoquest.config import MAX_READING_PATH_ITEMS

  snapshot = load_demo_repo()
  fingerprint = generate_fingerprint(snapshot)

  reading_path = generate_reading_path(snapshot, fingerprint)

  assert len(reading_path) <= MAX_READING_PATH_ITEMS


def test_reading_path_orders_correctly():
  """Test that reading path items are ordered correctly."""
  snapshot = load_demo_repo()
  fingerprint = generate_fingerprint(snapshot)

  reading_path = generate_reading_path(snapshot, fingerprint)

  # Check that order numbers are sequential
  for i, item in enumerate(reading_path):
    assert item.order == i + 1


def test_reading_path_prioritizes_backend_before_frontend():
  """Test that backend files generally come before frontend files."""
  snapshot = load_demo_repo()
  fingerprint = generate_fingerprint(snapshot)

  reading_path = generate_reading_path(snapshot, fingerprint)

  # Find first backend and first frontend file (excluding README)
  backend_index = None
  frontend_index = None

  for i, item in enumerate(reading_path):
    if "backend" in item.path.lower() and backend_index is None:
      backend_index = i
    if "frontend" in item.path.lower() and frontend_index is None:
      frontend_index = i

  # If both exist, backend should come first
  if backend_index is not None and frontend_index is not None:
    assert backend_index < frontend_index


def test_reading_path_skips_skipped_files():
  """Test that reading path does not include skipped files."""
  snapshot = load_demo_repo()
  fingerprint = generate_fingerprint(snapshot)

  reading_path = generate_reading_path(snapshot, fingerprint)

  # Get all paths in reading path
  reading_paths = {item.path for item in reading_path}

  # Check that no skipped files are in the reading path
  for file_info in snapshot.files:
    if file_info.skipped:
      assert file_info.path not in reading_paths


def test_reading_path_empty_snapshot():
  """Test reading path generation with empty snapshot."""
  snapshot = RepositorySnapshot(
    source_name="empty",
    files=[],
    total_files_seen=0,
    total_files_scanned=0,
    warnings=[],
  )
  fingerprint = ProjectFingerprint(
    project_type="Unknown",
    confidence=0.0,
    frameworks=[],
    entry_points=[],
    key_folders=[],
    summary="Empty repository",
    warnings=[],
  )

  reading_path = generate_reading_path(snapshot, fingerprint)

  assert len(reading_path) == 0


def test_reading_path_total_time_reasonable():
  """Test that total reading time is reasonable (around 30 minutes)."""
  snapshot = load_demo_repo()
  fingerprint = generate_fingerprint(snapshot)

  reading_path = generate_reading_path(snapshot, fingerprint)

  total_minutes = sum(item.estimated_minutes for item in reading_path)

  # Should be roughly 30 minutes, give or take
  assert 15 <= total_minutes <= 45


def test_reading_path_excludes_init_py():
  """Test that reading path excludes __init__.py files."""
  snapshot = load_demo_repo()
  fingerprint = generate_fingerprint(snapshot)

  reading_path = generate_reading_path(snapshot, fingerprint)

  # No reading path item should be __init__.py
  init_paths = [item.path for item in reading_path if item.path.endswith("__init__.py")]
  assert len(init_paths) == 0, "__init__.py files should not appear in reading path"



def test_reading_path_includes_test_file():
  """Test that reading path includes at least one test file for repos with tests."""
  snapshot = load_demo_repo()
  fingerprint = generate_fingerprint(snapshot)

  reading_path = generate_reading_path(snapshot, fingerprint)

  # Should include backend/tests/test_trips.py
  test_paths = [item.path for item in reading_path if "test" in item.path.lower()]
  assert len(test_paths) > 0, "Reading path should include at least one test file"

  # Specifically check for test_trips.py
  assert any("test_trips.py" in path for path in test_paths), \
    "Reading path should include backend/tests/test_trips.py"



# Made with Bob



def test_get_language_for_st_code():
  """Test language mapping for st.code() syntax highlighting."""
  from repoquest.reading_path import get_language_for_st_code
  from repoquest.models import FileInfo

  # Test Python
  py_file = FileInfo(
    path="test.py",
    name="test.py",
    suffix=".py",
    size_bytes=100,
    language="Python",
    role="backend_service",
    text_preview="",
    line_count=10
  )
  assert get_language_for_st_code(py_file) == "python"

  # Test TypeScript
  ts_file = FileInfo(
    path="test.ts",
    name="test.ts",
    suffix=".ts",
    size_bytes=100,
    language="TypeScript",
    role="api_client",
    text_preview="",
    line_count=10
  )
  assert get_language_for_st_code(ts_file) == "typescript"

  # Test JavaScript
  js_file = FileInfo(
    path="test.js",
    name="test.js",
    suffix=".js",
    size_bytes=100,
    language="JavaScript",
    role="frontend_component",
    text_preview="",
    line_count=10
  )
  assert get_language_for_st_code(js_file) == "javascript"

  # Test JSON
  json_file = FileInfo(
    path="package.json",
    name="package.json",
    suffix=".json",
    size_bytes=100,
    language="JSON",
    role="config",
    text_preview="",
    line_count=10
  )
  assert get_language_for_st_code(json_file) == "json"

  # Test unknown language
  unknown_file = FileInfo(
    path="test.xyz",
    name="test.xyz",
    suffix=".xyz",
    size_bytes=100,
    language="Unknown",
    role="unknown",
    text_preview="",
    line_count=10
  )
  assert get_language_for_st_code(unknown_file) is None


def test_get_understand_points():
  """Test that understand points are generated for different file roles."""
  from repoquest.reading_path import get_understand_points
  from repoquest.models import FileInfo

  # Test README
  readme = FileInfo(
    path="README.md",
    name="README.md",
    suffix=".md",
    size_bytes=1000,
    language="Markdown",
    role="documentation",
    text_preview="",
    line_count=50
  )
  points = get_understand_points(readme)
  assert len(points) > 0
  assert any("purpose" in p.lower() or "setup" in p.lower() for p in points)

  # Test backend route
  route_file = FileInfo(
    path="backend/routes/trips.py",
    name="trips.py",
    suffix=".py",
    size_bytes=500,
    language="Python",
    role="backend_route",
    text_preview="",
    line_count=30
  )
  points = get_understand_points(route_file)
  assert len(points) > 0
  assert any("endpoint" in p.lower() or "route" in p.lower() for p in points)

  # Test frontend page
  page_file = FileInfo(
    path="frontend/src/pages/TripsPage.tsx",
    name="TripsPage.tsx",
    suffix=".tsx",
    size_bytes=800,
    language="TypeScript",
    role="frontend_page",
    text_preview="",
    line_count=40
  )
  points = get_understand_points(page_file)
  assert len(points) > 0
  assert any("component" in p.lower() or "props" in p.lower() or "state" in p.lower() for p in points)

  # Test API client
  api_file = FileInfo(
    path="frontend/src/services/api.ts",
    name="api.ts",
    suffix=".ts",
    size_bytes=600,
    language="TypeScript",
    role="api_client",
    text_preview="",
    line_count=35
  )
  points = get_understand_points(api_file)
  assert len(points) > 0
  assert any("api" in p.lower() or "endpoint" in p.lower() or "request" in p.lower() for p in points)

  # Test test file
  test_file = FileInfo(
    path="backend/tests/test_trips.py",
    name="test_trips.py",
    suffix=".py",
    size_bytes=400,
    language="Python",
    role="test",
    text_preview="",
    line_count=25
  )
  points = get_understand_points(test_file)
  assert len(points) > 0
  assert any("test" in p.lower() or "assertion" in p.lower() for p in points)


def test_get_improvement_ideas():
  """Test that improvement ideas are generated for different file roles."""
  from repoquest.reading_path import get_improvement_ideas
  from repoquest.models import FileInfo

  # Test backend route
  route_file = FileInfo(
    path="backend/routes/trips.py",
    name="trips.py",
    suffix=".py",
    size_bytes=500,
    language="Python",
    role="backend_route",
    text_preview="",
    line_count=30
  )
  ideas = get_improvement_ideas(route_file)
  assert len(ideas) > 0
  assert any("test" in i.lower() or "validation" in i.lower() or "error" in i.lower() for i in ideas)

  # Test frontend component
  component_file = FileInfo(
    path="frontend/src/components/TripCard.tsx",
    name="TripCard.tsx",
    suffix=".tsx",
    size_bytes=400,
    language="TypeScript",
    role="frontend_component",
    text_preview="",
    line_count=20
  )
  ideas = get_improvement_ideas(component_file)
  assert len(ideas) > 0
  assert any("test" in i.lower() or "accessibility" in i.lower() for i in ideas)

  # Test API client
  api_file = FileInfo(
    path="frontend/src/services/api.ts",
    name="api.ts",
    suffix=".ts",
    size_bytes=600,
    language="TypeScript",
    role="api_client",
    text_preview="",
    line_count=35
  )
  ideas = get_improvement_ideas(api_file)
  assert len(ideas) > 0
  assert any("error" in i.lower() or "timeout" in i.lower() or "retry" in i.lower() for i in ideas)


def test_get_bob_prompt_for_file():
  """Test that AI assistant actions are generated for different file roles."""
  from repoquest.reading_path import get_bob_prompt_for_file
  from repoquest.models import FileInfo

  # Test backend route
  route_file = FileInfo(
    path="backend/routes/trips.py",
    name="trips.py",
    suffix=".py",
    size_bytes=500,
    language="Python",
    role="backend_route",
    text_preview="",
    line_count=30
  )
  prompt = get_bob_prompt_for_file(route_file)
  assert len(prompt) > 0
  assert "backend/routes/trips.py" in prompt
  assert any(keyword in prompt.lower() for keyword in ["test", "edge case", "pytest"])

  # Test frontend page
  page_file = FileInfo(
    path="frontend/src/pages/TripsPage.tsx",
    name="TripsPage.tsx",
    suffix=".tsx",
    size_bytes=800,
    language="TypeScript",
    role="frontend_page",
    text_preview="",
    line_count=40
  )
  prompt = get_bob_prompt_for_file(page_file)
  assert len(prompt) > 0
  assert "frontend/src/pages/TripsPage.tsx" in prompt
  assert any(keyword in prompt.lower() for keyword in ["flow", "state", "test"])

  # Test API client
  api_file = FileInfo(
    path="frontend/src/services/api.ts",
    name="api.ts",
    suffix=".ts",
    size_bytes=600,
    language="TypeScript",
    role="api_client",
    text_preview="",
    line_count=35
  )
  prompt = get_bob_prompt_for_file(api_file)
  assert len(prompt) > 0
  assert "frontend/src/services/api.ts" in prompt
  assert any(keyword in prompt.lower() for keyword in ["api", "endpoint", "error"])

  # Test test file
  test_file = FileInfo(
    path="backend/tests/test_trips.py",
    name="test_trips.py",
    suffix=".py",
    size_bytes=400,
    language="Python",
    role="test",
    text_preview="",
    line_count=25
  )
  prompt = get_bob_prompt_for_file(test_file)
  assert len(prompt) > 0
  assert "backend/tests/test_trips.py" in prompt
  assert any(keyword in prompt.lower() for keyword in ["test", "coverage"])


def test_reading_path_preview_exists():
  """Test that reading path items have text previews from FileInfo."""
  snapshot = load_demo_repo()
  fingerprint = generate_fingerprint(snapshot)

  reading_path = generate_reading_path(snapshot, fingerprint)

  # Check that files in reading path have previews
  for item in reading_path:
    file_info = next((f for f in snapshot.files if f.path == item.path), None)
    assert file_info is not None, f"File {item.path} not found in snapshot"

    # Skip check for skipped files
    if not file_info.skipped:
      # Most files should have text previews
      # (Some config files might be empty, but most should have content)
      if file_info.role not in ["config"]:
        assert file_info.text_preview, f"File {item.path} should have text preview"


def test_reading_path_previews_capped():
  """Test that file previews respect MAX_TEXT_PREVIEW_CHARS limit."""
  from repoquest.config import MAX_TEXT_PREVIEW_CHARS

  snapshot = load_demo_repo()
  fingerprint = generate_fingerprint(snapshot)

  reading_path = generate_reading_path(snapshot, fingerprint)

  # Check that all previews are capped
  for item in reading_path:
    file_info = next((f for f in snapshot.files if f.path == item.path), None)
    if file_info and file_info.text_preview:
      assert len(file_info.text_preview) <= MAX_TEXT_PREVIEW_CHARS, \
        f"Preview for {item.path} exceeds MAX_TEXT_PREVIEW_CHARS"


def test_reading_path_skipped_files_no_preview():
  """Test that skipped/binary files don't render previews."""
  snapshot = load_demo_repo()
  fingerprint = generate_fingerprint(snapshot)

  reading_path = generate_reading_path(snapshot, fingerprint)

  # No skipped files should be in reading path
  for item in reading_path:
    file_info = next((f for f in snapshot.files if f.path == item.path), None)
    assert file_info is not None
    assert not file_info.skipped, f"Skipped file {item.path} should not be in reading path"


# Made with Bob
