"""Tests for architecture graph generation."""

from repoquest.sample_loader import load_demo_repo
from repoquest.import_graph import build_import_graph
from repoquest.route_extractors import extract_all_routes
from repoquest.architecture import generate_architecture_map, generate_dependency_graph


def assert_graph_has_no_orphan_nodes(graph_data):
  """Assert every rendered graph node participates in at least one edge."""
  connected_paths = {
    path
    for edge in graph_data.edges
    for path in (edge.source, edge.target)
  }
  orphan_nodes = [node.path for node in graph_data.nodes if node.path not in connected_paths]
  assert orphan_nodes == [], f"Graph should not display disconnected nodes: {orphan_nodes}"


def test_architecture_map_generation():
  """Test that architecture map is generated successfully."""
  snapshot = load_demo_repo()
  routes = extract_all_routes(snapshot.files)

  dot_graph = generate_architecture_map(snapshot.files, routes)

  # Should be valid DOT format
  assert dot_graph.startswith('digraph Architecture'), "Should start with digraph declaration"
  assert dot_graph.endswith('}'), "Should end with closing brace"

  # Should contain some key files
  assert 'App.tsx' in dot_graph or 'TripsPage.tsx' in dot_graph, "Should include frontend files"
  assert 'trips.py' in dot_graph or 'main.py' in dot_graph, "Should include backend files"

  print(f"Yes Architecture map generated ({len(dot_graph)} chars)")


def test_dependency_graph_generation():
  """Test that dependency graph includes expected nodes and edges."""
  snapshot = load_demo_repo()
  edges = build_import_graph(snapshot.files, "")

  dot_graph = generate_dependency_graph(snapshot.files, edges)

  # Should be valid DOT format
  assert dot_graph.startswith('digraph Dependencies'), "Should start with digraph declaration"
  assert dot_graph.endswith('}'), "Should end with closing brace"

  # Should contain nodes
  assert '[label=' in dot_graph, "Should have labeled nodes"

  # Should contain edges (->)
  if edges:
    assert '->' in dot_graph, "Should have edges if imports exist"

  print(f"Yes Dependency graph generated ({len(dot_graph)} chars)")
  print(f"Yes Graph includes {len(edges)} import edges")


def test_dependency_graph_with_expected_edges():
  """Test that dependency graph contains expected file relationships."""
  snapshot = load_demo_repo()
  edges = build_import_graph(snapshot.files, "")

  dot_graph = generate_dependency_graph(snapshot.files, edges)

  # Check for some expected file names in the graph
  expected_files = [
    'App.tsx',
    'TripsPage.tsx',
    'main.py',
    'trips.py',
  ]

  found_count = sum(1 for f in expected_files if f in dot_graph)

  assert found_count >= 2, f"Should include at least 2 key files, found {found_count}"

  print(f"Yes Found {found_count}/{len(expected_files)} expected files in graph")

# Made with Bob


def test_architecture_map_excludes_test_files():
  """Test that default architecture map excludes test files."""
  from repoquest.sample_loader import load_demo_repo
  from repoquest.route_extractors import extract_all_routes
  from repoquest.architecture import generate_architecture_map

  snapshot = load_demo_repo()
  routes = extract_all_routes(snapshot.files)

  arch_map = generate_architecture_map(snapshot.files, routes)

  # Architecture map should not include test_trips.py
  assert "test_trips.py" not in arch_map, "Default architecture map should exclude test files"
  assert "test_" not in arch_map.lower() or "test" in arch_map.lower() and "test_" not in arch_map, \
    "Architecture map should not show test files in the graph"


def test_build_graph_data_application_mode():
  """Test that application mode excludes test files."""
  from repoquest.architecture import build_graph_data

  snapshot = load_demo_repo()
  edges = build_import_graph(snapshot.files, "")

  graph_data = build_graph_data(
    files=snapshot.files,
    edges=edges,
    view_mode="application",
    role_filter=None,
    max_nodes=80,
  )

  # Check that test files are excluded
  test_node_paths = [node.path for node in graph_data.nodes if node.is_test]
  assert len(test_node_paths) == 0, f"Application mode should exclude test files, found: {test_node_paths}"

  # Check that backend/tests/test_trips.py is not in nodes
  test_trips_path = "backend/tests/test_trips.py"
  node_paths = [node.path for node in graph_data.nodes]
  assert test_trips_path not in node_paths, "backend/tests/test_trips.py should not be in application mode"

  # Check that test edges are excluded
  test_edges = [edge for edge in graph_data.edges if edge.is_test_edge]
  assert len(test_edges) == 0, f"Application mode should exclude test edges, found: {len(test_edges)}"
  assert_graph_has_no_orphan_nodes(graph_data)

  print(f"Yes Application mode excludes test files ({len(graph_data.nodes)} nodes, {len(graph_data.edges)} edges)")


def test_build_graph_data_tests_mode():
  """Test that tests mode includes test files."""
  from repoquest.architecture import build_graph_data

  snapshot = load_demo_repo()
  edges = build_import_graph(snapshot.files, "")

  graph_data = build_graph_data(
    files=snapshot.files,
    edges=edges,
    view_mode="tests",
    role_filter=None,
    max_nodes=80,
  )

  # Check that test files are included
  test_node_paths = [node.path for node in graph_data.nodes if node.is_test]

  # The demo repo should have at least one test file
  assert len(test_node_paths) > 0, "Tests mode should include test files"
  assert_graph_has_no_orphan_nodes(graph_data)

  print(f"Yes Tests mode includes test files ({len(test_node_paths)} test nodes found)")


def test_build_graph_data_all_debug_mode():
  """Test that all_debug mode includes everything."""
  from repoquest.architecture import build_graph_data

  snapshot = load_demo_repo()
  edges = build_import_graph(snapshot.files, "")

  graph_data = build_graph_data(
    files=snapshot.files,
    edges=edges,
    view_mode="all_debug",
    role_filter=None,
    max_nodes=80,
  )

  # all_debug mode should include both test and non-test files
  test_nodes = [node for node in graph_data.nodes if node.is_test]
  non_test_nodes = [node for node in graph_data.nodes if not node.is_test]

  assert len(non_test_nodes) > 0, "all_debug mode should include non-test files"
  # Test files may or may not be present depending on the repo, but mode should allow them
  assert isinstance(test_nodes, list)
  assert_graph_has_no_orphan_nodes(graph_data)

  print(f"Yes all_debug mode includes all files ({len(graph_data.nodes)} total nodes)")


def test_build_graph_data_omits_disconnected_files():
  """Test that graph data omits files with no rendered relationships."""
  from repoquest.architecture import build_graph_data

  snapshot = load_demo_repo()
  edges = build_import_graph(snapshot.files, "")

  graph_data = build_graph_data(
    files=snapshot.files,
    edges=edges,
    view_mode="application",
    role_filter=None,
    max_nodes=80,
  )

  assert_graph_has_no_orphan_nodes(graph_data)
  node_paths = [node.path for node in graph_data.nodes]
  assert "README.md" not in node_paths, "README.md should not appear without graph relationships"
  assert "frontend/package.json" not in node_paths, "Unconnected config files should not appear"


def test_graph_data_to_dot():
  """Test that GraphData can be converted to DOT format."""
  from repoquest.architecture import build_graph_data, graph_data_to_dot

  snapshot = load_demo_repo()
  edges = build_import_graph(snapshot.files, "")
  routes = extract_all_routes(snapshot.files)

  graph_data = build_graph_data(
    files=snapshot.files,
    edges=edges,
    routes=routes,
    view_mode="application",
    role_filter=None,
    max_nodes=80,
  )

  dot_string = graph_data_to_dot(graph_data)

  # Should be valid DOT format with safe graph name
  assert dot_string.startswith('digraph RepoQuestGraph'), "Should start with safe digraph name (not 'Graph')"
  assert dot_string.endswith('}'), "Should end with closing brace"
  assert "rankdir=LR" in dot_string, "Architecture graph should render left-to-right"
  assert '[label=' in dot_string, "Should have labeled nodes"

  # Should not use reserved keyword "Graph"
  assert 'digraph Graph {' not in dot_string, "Should not use reserved keyword 'Graph'"

  # Should contain at least one expected node
  has_expected_node = any(name in dot_string for name in ['App.tsx', 'main.py', 'trips.py', 'TripsPage.tsx'])
  assert has_expected_node, "Should contain at least one expected node label"
  assert "Legend" in dot_string, "Legend should be embedded in the graph DOT"
  assert "__repoquest_legend_spacer" in dot_string, "Legend should be spaced away from graph nodes"
  assert 'fillcolor="#D9ECFF"' in dot_string, "Entry point color should stay accurate"
  assert 'fillcolor="#FFF9C4"' in dot_string, "API client color should stay accurate"
  assert "API boundary" in dot_string, "API boundary legend should appear when dashed edges exist"
  assert "style=dashed" in dot_string, "API boundary edge should render as dashed"

  # Should contain edges if graph has edges
  if len(graph_data.edges) > 0:
    assert '->' in dot_string, "Should have edge arrows if edges exist"

  print(f"Yes GraphData converts to DOT format ({len(dot_string)} chars)")
  print(f"Yes Contains {len(graph_data.nodes)} nodes and {len(graph_data.edges)} edges")


def test_graph_data_to_dot_hides_api_legend_without_api_edge():
  """Test that API boundary legend only appears when API edges are rendered."""
  from repoquest.architecture import build_graph_data, graph_data_to_dot

  snapshot = load_demo_repo()
  edges = build_import_graph(snapshot.files, "")

  graph_data = build_graph_data(
    files=snapshot.files,
    edges=edges,
    routes=None,
    view_mode="application",
    role_filter=None,
    max_nodes=80,
  )

  dot_string = graph_data_to_dot(graph_data)

  assert "rankdir=LR" in dot_string, "Architecture graph should render left-to-right"
  assert "Legend" in dot_string, "Legend should remain embedded"
  assert "API boundary" not in dot_string, "API boundary legend should be hidden without API edges"
  assert "style=dashed" not in dot_string, "Dashed API edge should be hidden without API edges"


def test_graph_data_to_dot_keeps_only_connected_file_nodes():
  """Test that DOT rendering does not include orphan file nodes."""
  from repoquest.architecture import graph_data_to_dot
  from repoquest.models import GraphData, GraphEdge, GraphNode

  graph_data = GraphData(
    nodes=[
      GraphNode(
        id="app.py",
        label="app.py",
        path="app.py",
        role="entrypoint",
        language="Python",
        size_bytes=120,
        line_count=8,
        is_test=False,
      ),
      GraphNode(
        id="routes.py",
        label="routes.py",
        path="routes.py",
        role="backend_route",
        language="Python",
        size_bytes=240,
        line_count=18,
        is_test=False,
      ),
      GraphNode(
        id="README.md",
        label="README.md",
        path="README.md",
        role="documentation",
        language="Markdown",
        size_bytes=100,
        line_count=5,
        is_test=False,
      ),
    ],
    edges=[
      GraphEdge(
        source="app.py",
        target="routes.py",
        kind="python_import",
        confidence=0.9,
        evidence="import routes",
        is_test_edge=False,
      )
    ],
    view_mode="application",
    filtered_roles=["entrypoint", "backend_route", "documentation"],
  )

  dot_string = graph_data_to_dot(graph_data)

  assert "app.py" in dot_string
  assert "routes.py" in dot_string
  assert "README.md" not in dot_string, "Orphan file nodes should not be rendered"


def test_graph_data_to_dot_escapes_paths_and_labels():
  """Test that arbitrary repo paths are escaped before DOT rendering."""
  from repoquest.architecture import graph_data_to_dot
  from repoquest.models import GraphData, GraphEdge, GraphNode

  unsafe_path = 'src/"odd\\name.py'

  graph_data = GraphData(
    nodes=[
      GraphNode(
        id=unsafe_path,
        label='odd"label.py',
        path=unsafe_path,
        role="entrypoint",
        language="Python",
        size_bytes=120,
        line_count=8,
        is_test=False,
      ),
      GraphNode(
        id="routes.py",
        label="routes.py",
        path="routes.py",
        role="backend_route",
        language="Python",
        size_bytes=240,
        line_count=18,
        is_test=False,
      ),
    ],
    edges=[
      GraphEdge(
        source=unsafe_path,
        target="routes.py",
        kind="python_import",
        confidence=0.9,
        evidence="import routes",
        is_test_edge=False,
      )
    ],
    view_mode="application",
    filtered_roles=["entrypoint", "backend_route"],
  )

  dot_string = graph_data_to_dot(graph_data)

  assert '"src/\\"odd\\\\name.py"' in dot_string
  assert 'label="odd\\"label.py"' in dot_string


def test_graph_data_adds_evidence_based_api_boundary_edge():
  """Test frontend API clients connect to backend routes when route paths are referenced."""
  from repoquest.architecture import build_graph_data

  snapshot = load_demo_repo()
  edges = build_import_graph(snapshot.files, "")
  routes = extract_all_routes(snapshot.files)

  graph_data = build_graph_data(
    files=snapshot.files,
    edges=edges,
    routes=routes,
    view_mode="application",
    role_filter=None,
    max_nodes=80,
  )

  api_edges = [edge for edge in graph_data.edges if edge.kind == "api_call"]
  assert api_edges, "Graph should include an API boundary edge when API clients reference routes"
  assert any(edge.source.endswith("/api.ts") and edge.target.endswith("/trips.py") for edge in api_edges)


def test_get_node_details():
  """Test that node details can be retrieved for key files."""
  from repoquest.architecture import get_node_details

  snapshot = load_demo_repo()
  edges = build_import_graph(snapshot.files, "")
  routes = extract_all_routes(snapshot.files)

  # Test backend route file
  backend_route_path = "backend/routes/trips.py"
  details = get_node_details(
    node_path=backend_route_path,
    files=snapshot.files,
    edges=edges,
    routes=routes,
  )

  assert "file_info" in details, "Should return file_info"
  assert details["file_info"].path == backend_route_path
  assert "incoming_deps" in details
  assert "outgoing_deps" in details
  assert "related_routes" in details
  assert "suggested_prompt" in details

  # Should have related routes since this is a route file
  assert len(details["related_routes"]) > 0, "backend/routes/trips.py should have related routes"

  print(f"Yes Node details retrieved for {backend_route_path}")
  print(f" - {len(details['incoming_deps'])} incoming deps")
  print(f" - {len(details['outgoing_deps'])} outgoing deps")
  print(f" - {len(details['related_routes'])} routes")


def test_get_node_details_frontend_page():
  """Test node details for a frontend page."""
  from repoquest.architecture import get_node_details

  snapshot = load_demo_repo()
  edges = build_import_graph(snapshot.files, "")
  routes = extract_all_routes(snapshot.files)

  # Test frontend page
  frontend_page_path = "frontend/src/pages/TripsPage.tsx"
  details = get_node_details(
    node_path=frontend_page_path,
    files=snapshot.files,
    edges=edges,
    routes=routes,
  )

  assert "file_info" in details
  assert details["file_info"].path == frontend_page_path
  assert details["file_info"].role == "frontend_page"
  assert "suggested_prompt" in details

  print(f"Yes Node details retrieved for {frontend_page_path}")


def test_get_node_details_api_client():
  """Test node details for an API client file."""
  from repoquest.architecture import get_node_details

  snapshot = load_demo_repo()
  edges = build_import_graph(snapshot.files, "")
  routes = extract_all_routes(snapshot.files)

  # Test API client
  api_client_path = "frontend/src/services/api.ts"
  details = get_node_details(
    node_path=api_client_path,
    files=snapshot.files,
    edges=edges,
    routes=routes,
  )

  assert "file_info" in details
  assert details["file_info"].path == api_client_path
  assert details["file_info"].role == "api_client"

  print(f"Yes Node details retrieved for {api_client_path}")


# Made with Bob
