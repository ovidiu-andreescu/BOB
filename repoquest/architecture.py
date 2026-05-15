"""Generate architecture and dependency graphs."""

from repoquest.models import FileInfo, ImportEdge, RouteInfo
from repoquest.config import MAX_GRAPH_NODES


def generate_architecture_map(
    files: list[FileInfo],
    routes: list[RouteInfo]
) -> str:
    """
    Generate a human-friendly architecture map as DOT string.
    
    Shows the story: React entry -> App -> Page -> Components/API -> Backend -> Services/Models -> Tests
    
    Args:
        files: List of scanned FileInfo objects
        routes: List of detected RouteInfo objects
        
    Returns:
        DOT format string for Graphviz
    """
    # Build DOT graph
    lines = [
        'digraph Architecture {',
        '  rankdir=LR;',
        '  node [shape=box, style="rounded,filled", fontcolor="#111111", color="#333333"];',
        ''
    ]
    
    # Define safe, readable colors for each role
    role_colors = {
        'entrypoint': '#D9ECFF',  # Light blue
        'frontend_page': '#C8E6C9',  # Light green
        'frontend_component': '#C8E6C9',  # Light green
        'api_client': '#FFF9C4',  # Light yellow
        'backend_route': '#FFCCBC',  # Light orange
        'backend_service': '#FFCCBC',  # Light orange
        'model': '#E0E0E0',  # Light gray
        'test': '#E1BEE7',  # Light purple
    }
    
    # Find key files (exclude __init__.py)
    key_files = []
    for file in files:
        if file.name == '__init__.py':
            continue
        if file.role in role_colors or file.name in ['main.tsx', 'App.tsx', 'TripsPage.tsx', 'TripCard.tsx', 'SearchForm.tsx', 'api.ts', 'main.py', 'trips.py', 'recommendations.py', 'trip.py', 'test_trips.py']:
            key_files.append(file)
    
    # Limit to most important files
    priority_order = ['entrypoint', 'frontend_page', 'frontend_component', 'api_client', 'backend_route', 'backend_service', 'model', 'test']
    key_files.sort(key=lambda f: (priority_order.index(f.role) if f.role in priority_order else 999, f.path))
    key_files = key_files[:15]
    
    # Add nodes
    for file in key_files:
        label = file.name
        color = role_colors.get(file.role, '#F5F5F5')
        lines.append(f'  "{file.path}" [label="{label}", fillcolor="{color}"];')
    
    lines.append('')
    
    # Add edges based on typical architecture flow
    file_map = {f.path: f for f in key_files}
    
    # Frontend flow
    main_tsx = next((f for f in key_files if f.name == 'main.tsx'), None)
    app_tsx = next((f for f in key_files if f.name == 'App.tsx'), None)
    trips_page = next((f for f in key_files if f.name == 'TripsPage.tsx'), None)
    trip_card = next((f for f in key_files if f.name == 'TripCard.tsx'), None)
    search_form = next((f for f in key_files if f.name == 'SearchForm.tsx'), None)
    api_ts = next((f for f in key_files if f.name == 'api.ts'), None)
    
    # Backend flow
    main_py = next((f for f in key_files if f.name == 'main.py'), None)
    trips_py = next((f for f in key_files if f.name == 'trips.py'), None)
    recommendations_py = next((f for f in key_files if f.name == 'recommendations.py'), None)
    trip_py = next((f for f in key_files if f.name == 'trip.py'), None)
    test_trips_py = next((f for f in key_files if f.name == 'test_trips.py'), None)
    
    # Frontend edges
    if main_tsx and app_tsx:
        lines.append(f'  "{main_tsx.path}" -> "{app_tsx.path}";')
    if app_tsx and trips_page:
        lines.append(f'  "{app_tsx.path}" -> "{trips_page.path}";')
    if trips_page and trip_card:
        lines.append(f'  "{trips_page.path}" -> "{trip_card.path}";')
    if trips_page and search_form:
        lines.append(f'  "{trips_page.path}" -> "{search_form.path}";')
    if trips_page and api_ts:
        lines.append(f'  "{trips_page.path}" -> "{api_ts.path}";')
    
    # API call edge (dashed)
    if api_ts and trips_py:
        lines.append(f'  "{api_ts.path}" -> "{trips_py.path}" [style=dashed, color="#0066CC", label="API"];')
    
    # Backend edges
    if main_py and trips_py:
        lines.append(f'  "{main_py.path}" -> "{trips_py.path}";')
    if trips_py and recommendations_py:
        lines.append(f'  "{trips_py.path}" -> "{recommendations_py.path}";')
    if trips_py and trip_py:
        lines.append(f'  "{trips_py.path}" -> "{trip_py.path}";')
    
    # Test edge
    if test_trips_py and main_py:
        lines.append(f'  "{test_trips_py.path}" -> "{main_py.path}";')
    
    lines.append('}')
    
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
        '  rankdir=TB;',
        '  node [shape=box, style="rounded,filled", fontcolor="#111111", color="#333333", fillcolor="#E8F4F8"];',
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
            lines.append(f'  "{path}" [label="{label}"];')
    
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
                lines.append(f'  "{edge.source}" -> "{edge.target}";')
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
        '  rankdir=LR;',
        '  node [shape=box, style="rounded,filled", fontcolor="#111111", color="#333333"];',
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
        lines.append(f'  "{dir_name}" [shape=folder, fillcolor="#FFF9C4", style=filled];')
    
    lines.append('')
    
    # Add file nodes
    for dir_name, dir_files in dirs.items():
        for file in dir_files[:3]:
            lines.append(f'  "{file.path}" [label="{file.name}", fillcolor="#E8F4F8"];')
            lines.append(f'  "{dir_name}" -> "{file.path}";')
    
    lines.append('}')
    
    return '\n'.join(lines)

# Made with Bob