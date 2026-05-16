"""Generate architecture and dependency graphs."""

from repoquest.models import (
  FileInfo,
  ImportEdge,
  RouteInfo,
  GraphNode,
  GraphEdge,
  GraphData,
  GraphViewMode,
)
from repoquest.config import MAX_GRAPH_NODES

GRAPH_ROLE_COLORS = {
  "entrypoint": "#D9ECFF",
  "frontend_page": "#C8E6C9",
  "frontend_component": "#C8E6C9",
  "api_client": "#FFF9C4",
  "backend_route": "#FFCCBC",
  "backend_service": "#FFCCBC",
  "model": "#E0E0E0",
  "test": "#E1BEE7",
  "config": "#F5F5F5",
  "documentation": "#FFFDE7",
}

GRAPH_ROLE_LEGEND = [
  (("entrypoint",), "#D9ECFF", "Entry"),
  (("frontend_page", "frontend_component"), "#C8E6C9", "Frontend"),
  (("api_client",), "#FFF9C4", "API"),
  (("backend_route", "backend_service"), "#FFCCBC", "Backend"),
  (("model",), "#E0E0E0", "Models"),
  (("test",), "#E1BEE7", "Tests"),
  (("config",), "#F5F5F5", "Config"),
  (("documentation",), "#FFFDE7", "Docs"),
]


def generate_architecture_map(
  files: list[FileInfo],
  routes: list[RouteInfo],
) -> str:
  """
  Generate a human-friendly architecture map as DOT string.

  Shows production application flow only. Tests are excluded from the default map.
  """
  # Build DOT graph
  lines = [
    'digraph Architecture {',
    ' rankdir=LR;',
    ' node [shape=box, style="rounded,filled", fontcolor="#111111", color="#333333"];',
    "",
  ]

  # Define safe, readable colors for each role
  role_colors = {
    "entrypoint": "#D9ECFF",
    "frontend_page": "#C8E6C9",
    "frontend_component": "#C8E6C9",
    "api_client": "#FFF9C4",
    "backend_route": "#FFCCBC",
    "backend_service": "#FFCCBC",
    "model": "#E0E0E0",
    "test": "#E1BEE7",
  }

  # Find key files (exclude __init__.py, package markers, and tests)
  key_files = []
  for file in files:
    if file.name == "__init__.py":
      continue
    if file.skipped:
      continue
    # Exclude test files from default architecture map
    if file.role == "test":
      continue
    # Include files with important production roles
    if file.role in role_colors:
      key_files.append(file)

  # Limit to most important files
  priority_order = [
    "entrypoint",
    "frontend_page",
    "frontend_component",
    "api_client",
    "backend_route",
    "backend_service",
    "model",
  ]
  key_files.sort(key=lambda f: (priority_order.index(f.role) if f.role in priority_order else 999, f.path))
  key_files = key_files[:15]

  # Add nodes
  for file in key_files:
    label = file.name
    color = role_colors.get(file.role, "#F5F5F5")
    lines.append(f' "{file.path}" [label="{label}", fillcolor="{color}"];')

  lines.append("")

  # Build edges based on roles and common patterns
  # Group files by role
  entrypoints = [f for f in key_files if f.role == "entrypoint"]
  frontend_pages = [f for f in key_files if f.role == "frontend_page"]
  frontend_components = [f for f in key_files if f.role == "frontend_component"]
  api_clients = [f for f in key_files if f.role == "api_client"]
  backend_routes = [f for f in key_files if f.role == "backend_route"]
  backend_services = [f for f in key_files if f.role == "backend_service"]
  models = [f for f in key_files if f.role == "model"]

  # Frontend flow: entry -> pages -> components/api
  frontend_entry = next((f for f in entrypoints if "frontend" in f.path.lower() or "App.tsx" in f.path or "App.jsx" in f.path), None)
  if not frontend_entry:
    frontend_entry = next((f for f in entrypoints if f.suffix in [".tsx", ".jsx", ".ts", ".js"]), None)

  if frontend_entry:
    for page in frontend_pages[:2]:
      lines.append(f' "{frontend_entry.path}" -> "{page.path}";')

    # Pages to components and API clients
    for page in frontend_pages[:1]:
      for component in frontend_components[:2]:
        lines.append(f' "{page.path}" -> "{component.path}";')
      for api_client in api_clients[:1]:
        lines.append(f' "{page.path}" -> "{api_client.path}";')

  # API call edge (dashed) from frontend to backend
  if api_clients and backend_routes:
    lines.append(f' "{api_clients[0].path}" -> "{backend_routes[0].path}" [style=dashed, color="#0066CC", label="API"];')

  # Backend flow: entry -> routes -> services/models
  backend_entry = next((f for f in entrypoints if "backend" in f.path.lower() or f.name == "main.py"), None)
  if backend_entry:
    for route in backend_routes[:2]:
      lines.append(f' "{backend_entry.path}" -> "{route.path}";')

  # Routes to services and models
  for route in backend_routes[:1]:
    for service in backend_services[:1]:
      lines.append(f' "{route.path}" -> "{service.path}";')
    for model in models[:1]:
      lines.append(f' "{route.path}" -> "{model.path}";')

  lines.append("}")

  return '\n'.join(lines)


def generate_dependency_graph(
  files: list[FileInfo],
  edges: list[ImportEdge],
  max_nodes: int | None = None
) -> str:
  """
  Generate a technical dependency graph as DOT string showing actual imports.

  Args:
    files: List of scanned FileInfo objects
    edges: List of ImportEdge objects
    max_nodes: Maximum number of nodes to include (defaults to MAX_GRAPH_NODES)

  Returns:
    DOT format string for Graphviz
  """
  if max_nodes is None:
    max_nodes = MAX_GRAPH_NODES

  # Build DOT graph
  lines = [
    'digraph Dependencies {',
    ' rankdir=TB;',
    ' node [shape=box, style="rounded,filled", fontcolor="#111111", color="#333333", fillcolor="#E8F4F8"];',
    ''
  ]

  # Get files that are actually connected (exclude __init__.py unless it's the only option)
  connected_files = set()
  for edge in edges:
    # Exclude __init__.py from display
    if not edge.source.endswith('/__init__.py'):
      connected_files.add(edge.source)
    if not edge.target.endswith('/__init__.py'):
      connected_files.add(edge.target)

  # Build file map
  file_map = {f.path: f for f in files}

  # Prioritize certain roles
  priority_roles = ['entrypoint', 'backend_route', 'frontend_page', 'api_client', 'backend_service', 'model', 'frontend_component']

  # Score files by priority
  def file_priority(path: str) -> int:
    if path not in file_map:
      return 999
    role = file_map[path].role
    if role in priority_roles:
      return priority_roles.index(role)
    return len(priority_roles)

  # Sort connected files by priority
  sorted_files = sorted(connected_files, key=file_priority)
  selected_paths = set(sorted_files[:max_nodes])

  # Add nodes
  for path in selected_paths:
    if path in file_map:
      label = file_map[path].name
      lines.append(f' "{path}" [label="{label}"];')

  lines.append('')

  # Add edges (only between selected nodes, exclude __init__.py targets)
  added_edges = set()
  for edge in edges:
    # Skip edges involving __init__.py
    if edge.source.endswith('/__init__.py') or edge.target.endswith('/__init__.py'):
      continue

    if edge.source in selected_paths and edge.target in selected_paths:
      edge_key = (edge.source, edge.target)
      if edge_key not in added_edges:
        lines.append(f' "{edge.source}" -> "{edge.target}";')
        added_edges.add(edge_key)

  lines.append('}')

  return '\n'.join(lines)


def generate_simple_graph(files: list[FileInfo]) -> str:
  """
  Generate a simple fallback graph when no imports are detected.

  Args:
    files: List of scanned FileInfo objects

  Returns:
    DOT format string for Graphviz
  """
  lines = [
    'digraph SimpleStructure {',
    ' rankdir=LR;',
    ' node [shape=box, style="rounded,filled", fontcolor="#111111", color="#333333"];',
    ''
  ]

  # Group by directory (exclude __init__.py)
  dirs = {}
  for file in files[:15]:
    if file.name == '__init__.py':
      continue
    dir_name = file.path.split('/')[0] if '/' in file.path else 'root'
    if dir_name not in dirs:
      dirs[dir_name] = []
    dirs[dir_name].append(file)

  # Add directory nodes
  for dir_name in dirs:
    lines.append(f' "{dir_name}" [shape=folder, fillcolor="#FFF9C4", style=filled];')

  lines.append('')

  # Add file nodes
  for dir_name, dir_files in dirs.items():
    for file in dir_files[:3]:
      lines.append(f' "{file.path}" [label="{file.name}", fillcolor="#E8F4F8"];')
      lines.append(f' "{dir_name}" -> "{file.path}";')

  lines.append('}')

  return '\n'.join(lines)

# Made with Bob



def build_graph_data(
  files: list[FileInfo],
  edges: list[ImportEdge],
  routes: list[RouteInfo] | None = None,
  view_mode: GraphViewMode = "application",
  role_filter: list[str] | None = None,
  max_nodes: int | None = None,
) -> GraphData:
  """
  Build JSON-first graph data structure with filtering support.

  Args:
    files: List of scanned FileInfo objects
    edges: List of ImportEdge objects
    routes: Optional route metadata used to add evidence-based API boundary edges
    view_mode: Graph view mode ("application", "tests", "all_debug")
    role_filter: Optional internal role filter. The Streamlit UI does not expose this.
    max_nodes: Maximum number of nodes to include (defaults to MAX_GRAPH_NODES)

  Returns:
    GraphData object with filtered nodes and edges
  """
  if max_nodes is None:
    max_nodes = MAX_GRAPH_NODES

  # Filter files based on view mode
  filtered_files = []
  for file in files:
    # Skip __init__.py files
    if file.name == "__init__.py":
      continue
    if file.skipped:
      continue

    # Apply view mode filter
    if view_mode == "application":
      # Exclude test files in application mode
      if file.is_test:
        continue
    elif view_mode == "tests":
      # In tests mode, include test files and files they likely test
      # For now, include test files and all non-test files
      pass
    # all_debug mode includes everything

    # Apply role filter if provided
    if role_filter and file.role not in role_filter:
      continue

    filtered_files.append(file)

  # Prioritize certain roles
  priority_roles = [
    "entrypoint",
    "backend_route",
    "frontend_page",
    "api_client",
    "backend_service",
    "model",
    "frontend_component",
    "test",
  ]

  def file_priority(f: FileInfo) -> int:
    if f.role in priority_roles:
      return priority_roles.index(f.role)
    return len(priority_roles)

  # Sort files and collect candidate paths before edge pruning.
  filtered_files.sort(key=file_priority)
  candidate_paths = {f.path for f in filtered_files}

  # Filter edges based on view mode and candidate nodes.
  graph_edges = []
  added_edges = set()

  for edge in edges:
    # Skip edges not in candidate nodes
    if edge.source not in candidate_paths or edge.target not in candidate_paths:
      continue

    # Apply view mode filter
    if view_mode == "application":
      # Exclude test edges in application mode
      if edge.is_test_edge:
        continue
    elif view_mode == "tests":
      # In tests mode, prefer test edges but include all
      pass
    # all_debug mode includes everything

    # Avoid duplicate edges
    edge_key = (edge.source, edge.target)
    if edge_key in added_edges:
      continue
    added_edges.add(edge_key)

    graph_edge = GraphEdge(
      source=edge.source,
      target=edge.target,
      kind=edge.kind,
      confidence=edge.confidence,
      evidence=edge.evidence,
      is_test_edge=edge.is_test_edge,
    )
    graph_edges.append(graph_edge)

  if routes:
    graph_edges.extend(_build_api_boundary_edges(filtered_files, candidate_paths, routes, added_edges))

  # Only display nodes that participate in at least one rendered edge.
  connected_paths = {
    path
    for edge in graph_edges
    for path in (edge.source, edge.target)
  }
  filtered_files = [file for file in filtered_files if file.path in connected_paths]
  filtered_files = filtered_files[:max_nodes]
  selected_paths = {file.path for file in filtered_files}
  graph_edges = [
    edge for edge in graph_edges
    if edge.source in selected_paths and edge.target in selected_paths
  ]

  # Prune again after the max-node limit so no orphan nodes remain.
  connected_paths = {
    path
    for edge in graph_edges
    for path in (edge.source, edge.target)
  }
  filtered_files = [file for file in filtered_files if file.path in connected_paths]

  graph_nodes = [
    GraphNode(
      id=file.path,
      label=file.name,
      path=file.path,
      role=file.role,
      language=file.language,
      size_bytes=file.size_bytes,
      line_count=file.line_count,
      is_test=file.is_test,
    )
    for file in filtered_files
  ]

  # Determine which roles are included
  included_roles = list(set(node.role for node in graph_nodes))

  return GraphData(
    nodes=graph_nodes,
    edges=graph_edges,
    view_mode=view_mode,
    filtered_roles=included_roles,
  )


def graph_data_to_dot(graph_data: GraphData) -> str:
  """
  Convert GraphData to DOT format string for Graphviz rendering.

  Args:
    graph_data: GraphData object

  Returns:
    DOT format string
  """
  connected_node_ids = {
    path
    for edge in graph_data.edges
    for path in (edge.source, edge.target)
  }
  connected_nodes = [node for node in graph_data.nodes if node.id in connected_node_ids]
  selected_node_ids = {node.id for node in connected_nodes}
  connected_edges = [
    edge for edge in graph_data.edges
    if edge.source in selected_node_ids and edge.target in selected_node_ids
  ]
  rendered_graph = GraphData(
    nodes=connected_nodes,
    edges=connected_edges,
    view_mode=graph_data.view_mode,
    filtered_roles=graph_data.filtered_roles,
  )

  lines = [
    'digraph RepoQuestGraph {',
    ' rankdir=LR;',
    ' graph [fontsize=9, margin=0.08, pad=0.16, ranksep=0.78, nodesep=0.34, ratio=compress, size="10,6"];',
    ' node [shape=box, style="rounded,filled", fontcolor="#111111", color="#333333", '
    'fontsize=10, margin="0.08,0.04", height=0.34, penwidth=1.1];',
    ' edge [fontsize=8, arrowsize=0.65, penwidth=1.1];',
    '',
  ]

  # Add nodes
  for node in connected_nodes:
    color = GRAPH_ROLE_COLORS.get(node.role, "#E8F4F8")
    lines.append(
      f' {_dot_quote(node.id)} [label={_dot_quote(node.label)}, fillcolor="{color}"];'
    )

  lines.append('')

  # Add edges
  for edge in connected_edges:
    # Use dashed line for API boundaries
    if edge.kind == "api_call":
      lines.append(
        f' {_dot_quote(edge.source)} -> {_dot_quote(edge.target)} '
        '[style=dashed, color="#0066CC", label="API"];'
      )
    else:
      lines.append(f' {_dot_quote(edge.source)} -> {_dot_quote(edge.target)};')

  if connected_nodes:
    lines.extend(_build_spaced_legend_lines(rendered_graph, connected_nodes[-1].id))

  lines.append('}')

  return '\n'.join(lines)


def _build_spaced_legend_lines(graph_data: GraphData, anchor_node_id: str) -> list[str]:
  """Build an embedded legend node with invisible spacing from the graph body."""
  return [
    '',
    ' "__repoquest_legend_spacer" [shape=point, style=invis, label="", width=0.48, height=0.01];',
    f' {_dot_quote(anchor_node_id)} -> "__repoquest_legend_spacer" '
    '[style=invis, arrowhead=none, weight=0, minlen=3];',
    ' "__repoquest_legend" [shape=plain, margin=0, label=<' +
    _build_graph_legend_html(graph_data) + '>];',
    ' "__repoquest_legend_spacer" -> "__repoquest_legend" '
    '[style=invis, arrowhead=none, weight=0, minlen=1];',
  ]


def _dot_quote(value: str) -> str:
  """Return a DOT-safe quoted string."""
  escaped = (
    str(value)
    .replace("\\", "\\\\")
    .replace('"', '\\"')
    .replace("\r", "")
    .replace("\n", "\\n")
  )
  return f'"{escaped}"'


def _route_variants(route_path: str) -> list[str]:
  """Return path variants that an API client might contain."""
  if route_path in {"/", ""}:
    return []

  variants = {route_path}
  if route_path.startswith("/api/"):
    variants.add(route_path.removeprefix("/api"))

  for variant in list(variants):
    if "{" in variant:
      variants.add(variant.split("{", 1)[0].rstrip("/"))

  return sorted(
    [variant for variant in variants if variant and variant != "/"],
    key=len,
    reverse=True,
  )


def _api_client_mentions_route(api_client: FileInfo, route: RouteInfo) -> bool:
  """Return whether an API client preview references a detected route path."""
  text = api_client.text_preview
  if not text:
    return False
  return any(variant in text for variant in _route_variants(route.path))


def _build_api_boundary_edges(
  files: list[FileInfo],
  candidate_paths: set[str],
  routes: list[RouteInfo],
  added_edges: set[tuple[str, str]],
) -> list[GraphEdge]:
  """Build evidence-backed API edges from frontend API clients to backend routes."""
  api_clients = [file for file in files if file.role == "api_client"]
  route_file_paths = {route.file_path for route in routes}
  route_file_paths &= candidate_paths
  if not api_clients or not route_file_paths:
    return []

  boundary_edges = []
  for api_client in api_clients:
    if api_client.path not in candidate_paths:
      continue
    for route_file_path in sorted(route_file_paths):
      matching_routes = [
        route for route in routes
        if route.file_path == route_file_path and _api_client_mentions_route(api_client, route)
      ]
      if not matching_routes:
        continue

      edge_key = (api_client.path, route_file_path)
      if edge_key in added_edges:
        continue
      added_edges.add(edge_key)
      evidence = ", ".join(f"{route.method} {route.path}" for route in matching_routes[:3])
      boundary_edges.append(GraphEdge(
        source=api_client.path,
        target=route_file_path,
        kind="api_call",
        confidence=0.75,
        evidence=f"API client references detected route paths: {evidence}",
        is_test_edge=False,
      ))

  return boundary_edges


def _build_graph_legend_html(graph_data: GraphData) -> str:
  """Build an in-graph HTML legend for Graphviz."""
  roles_present = {node.role for node in graph_data.nodes}
  role_rows = [
    (color, label)
    for roles, color, label in GRAPH_ROLE_LEGEND
    if any(role in roles_present for role in roles)
  ]
  has_api_edges = any(edge.kind == "api_call" for edge in graph_data.edges)
  has_import_edges = any(edge.kind != "api_call" for edge in graph_data.edges)

  rows = [
    '<TR><TD COLSPAN="2" BGCOLOR="#F8FAFC">'
    '<FONT POINT-SIZE="9" COLOR="#111111"><B>Legend</B></FONT></TD></TR>'
  ]
  for color, label in role_rows:
    rows.append(
      f'<TR><TD WIDTH="14" BGCOLOR="{color}"></TD>'
      f'<TD ALIGN="LEFT" BGCOLOR="#FFFFFF"><FONT POINT-SIZE="8" COLOR="#111111">{label}</FONT></TD></TR>'
    )

  if has_import_edges or has_api_edges:
    rows.append(
      '<TR><TD COLSPAN="2" BGCOLOR="#F8FAFC">'
      '<FONT POINT-SIZE="8" COLOR="#111111"><B>Edges</B></FONT></TD></TR>'
    )
  if has_import_edges:
    rows.append(
      '<TR><TD ALIGN="CENTER" BGCOLOR="#FFFFFF"><FONT POINT-SIZE="8" COLOR="#111111">→</FONT></TD>'
      '<TD ALIGN="LEFT" BGCOLOR="#FFFFFF"><FONT POINT-SIZE="8" COLOR="#111111">Import</FONT></TD></TR>'
    )
  if has_api_edges:
    rows.append(
      '<TR><TD BGCOLOR="#FFFFFF"><FONT POINT-SIZE="8" COLOR="#0066CC">- - →</FONT></TD>'
      '<TD ALIGN="LEFT" BGCOLOR="#FFFFFF"><FONT POINT-SIZE="8" COLOR="#111111">API boundary</FONT></TD></TR>'
    )

  return (
    '<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="2" BGCOLOR="#FFFFFF" '
    'COLOR="#CBD5E1">'
    + "".join(rows)
    + "</TABLE>"
  )


def get_node_details(
  node_path: str,
  files: list[FileInfo],
  edges: list[ImportEdge],
  routes: list[RouteInfo],
) -> dict:
  """
  Get detailed information about a selected graph node.

  Args:
    node_path: Path of the selected node (FileInfo.path)
    files: List of all FileInfo objects
    edges: List of all ImportEdge objects
    routes: List of all RouteInfo objects

  Returns:
    Dictionary with node details including:
    - file_info: FileInfo object
    - incoming_deps: List of files that import this file
    - outgoing_deps: List of files this file imports
    - related_routes: List of routes defined in this file
    - related_tests: List of test files that might test this file
    - suggested_prompt: AI assistant action for this file
  """
  # Find the file
  file_info = next((f for f in files if f.path == node_path), None)
  if not file_info:
    return {}

  # Find incoming dependencies
  incoming_deps = [e.source for e in edges if e.target == node_path]

  # Find outgoing dependencies
  outgoing_deps = [e.target for e in edges if e.source == node_path]

  # Find related routes
  related_routes = [r for r in routes if r.file_path == node_path]

  # Find related tests (heuristic)
  related_tests = []
  if not file_info.is_test:
    # Look for test files that might test this file
    file_name_base = file_info.name.rsplit(".", 1)[0]
    for f in files:
      if f.is_test:
        # Check if test file name suggests it tests this file
        if file_name_base.lower() in f.name.lower():
          related_tests.append(f.path)

  # Generate suggested assistant action
  if file_info.role == "backend_route":
    suggested_prompt = f"Explain {node_path}, identify edge cases, and generate pytest tests for the detected routes."
  elif file_info.role == "frontend_component":
    suggested_prompt = f"Explain {node_path}, identify props and state management, and suggest component tests."
  elif file_info.role == "frontend_page":
    suggested_prompt = f"Explain {node_path}, identify user flows, and suggest integration tests."
  elif file_info.role == "backend_service":
    suggested_prompt = f"Explain {node_path}, identify business logic, and generate unit tests."
  elif file_info.role == "model":
    suggested_prompt = f"Explain {node_path}, identify validation rules, and suggest test cases."
  elif file_info.role == "test":
    suggested_prompt = f"Explain {node_path} and identify what it tests and any missing test coverage."
  else:
    suggested_prompt = f"Explain {node_path} and its role in the application."

  return {
    "file_info": file_info,
    "incoming_deps": incoming_deps,
    "outgoing_deps": outgoing_deps,
    "related_routes": related_routes,
    "related_tests": related_tests,
    "suggested_prompt": suggested_prompt,
  }


# Made with Bob
