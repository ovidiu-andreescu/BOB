"""Tests for route extraction."""

from repoquest.sample_loader import load_demo_repo
from repoquest.route_extractors import extract_all_routes


def test_fastapi_route_extraction():
  """Test that FastAPI routes are extracted from demo repo."""
  # Load demo repo
  snapshot = load_demo_repo()

  # Extract routes
  routes = extract_all_routes(snapshot.files)

  # Should find routes from backend/routes/trips.py
  assert len(routes) >= 4, f"Expected at least 4 routes, found {len(routes)}"

  # Check for expected routes with /api prefix
  route_paths = {(r.method, r.path) for r in routes}

  expected_routes = [
    ("GET", "/api/trips"),
    ("POST", "/api/trips"),
    ("DELETE", "/api/trips/{trip_id}"),
    ("GET", "/api/recommendations"),
  ]

  for method, path in expected_routes:
    assert (method, path) in route_paths, f"Missing route: {method} {path}"

  # Verify all routes are FastAPI
  for route in routes:
    assert route.framework == "fastapi", f"Expected fastapi, got {route.framework}"

  # Verify routes have file paths
  for route in routes:
    assert route.file_path, "Route should have file_path"

  print(f"Yes Found {len(routes)} routes")
  print("Yes All expected /api routes present")
  for route in routes:
    print(f" {route.method} {route.path} -> {route.file_path}")


def test_route_sorting():
  """Test that routes are sorted with /api routes first."""
  snapshot = load_demo_repo()
  routes = extract_all_routes(snapshot.files)

  # Feature routes (/api) should come before root routes (/, /health)
  api_routes = [r for r in routes if r.path.startswith('/api')]
  root_routes = [r for r in routes if not r.path.startswith('/api')]

  if api_routes and root_routes:
    # Find indices
    first_api_idx = routes.index(api_routes[0])
    first_root_idx = routes.index(root_routes[0])

    assert first_api_idx < first_root_idx, "/api routes should come before root routes"
    print("Yes Routes sorted correctly (/api routes first)")


def test_route_prefix_detection():
  """Test that router prefixes are correctly applied."""
  snapshot = load_demo_repo()
  routes = extract_all_routes(snapshot.files)

  # Routes from backend/routes/trips.py should have /api prefix
  trips_routes = [r for r in routes if 'trips.py' in r.file_path]

  for route in trips_routes:
    if route.path not in ['/', '/health']: # Skip root routes
      assert route.path.startswith('/api'), f"Route {route.path} should have /api prefix"

  print("Yes Router prefixes correctly applied")

# Made with Bob
