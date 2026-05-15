"""Extract API routes from backend files."""

import re
from repoquest.models import RouteInfo, FileInfo


def extract_fastapi_routes(files: list[FileInfo]) -> list[RouteInfo]:
    """
    Extract FastAPI routes from scanned files.
    
    Looks for decorators like:
    - @app.get("/path")
    - @app.post("/path")
    - @router.get("/path")
    - @router.post("/path")
    - @router.delete("/path/{id}")
    
    For the demo repo, applies /api prefix to router routes based on
    app.include_router(router, prefix="/api") pattern in main.py.
    
    Args:
        files: List of scanned FileInfo objects
        
    Returns:
        List of RouteInfo objects
    """
    routes = []
    
    # First, detect router prefixes from main.py
    router_prefixes = _detect_router_prefixes(files)
    
    # Regex patterns for FastAPI decorators
    # Matches: @app.get("/trips") or @router.post("/trips/{trip_id}")
    decorator_pattern = re.compile(
        r'@(app|router)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
        re.IGNORECASE
    )
    
    # Pattern to find function name after decorator
    function_pattern = re.compile(r'^\s*(?:async\s+)?def\s+(\w+)\s*\(')
    
    for file_info in files:
        # Only check Python files
        if file_info.suffix not in ['.py']:
            continue
            
        # Skip if file was skipped or has no content
        if file_info.skipped or not file_info.text_preview:
            continue
        
        # Check if file contains FastAPI imports
        if 'fastapi' not in file_info.text_preview.lower():
            continue
        
        # Determine if this file uses a router with a prefix
        route_prefix = ""
        if 'APIRouter' in file_info.text_preview or '@router.' in file_info.text_preview:
            # Check if this router file has a known prefix
            for router_file, prefix in router_prefixes.items():
                if router_file in file_info.path:
                    route_prefix = prefix
                    break
        
        lines = file_info.text_preview.split('\n')
        
        for i, line in enumerate(lines):
            match = decorator_pattern.search(line)
            if match:
                decorator_type = match.group(1)  # 'app' or 'router'
                method = match.group(2).upper()
                path = match.group(3)
                
                # Apply prefix for router routes
                if decorator_type == 'router' and route_prefix:
                    full_path = route_prefix + path
                else:
                    full_path = path
                
                # Try to find function name on next line
                function_name = None
                if i + 1 < len(lines):
                    func_match = function_pattern.match(lines[i + 1])
                    if func_match:
                        function_name = func_match.group(1)
                
                routes.append(RouteInfo(
                    framework="fastapi",
                    method=method,
                    path=full_path,
                    file_path=file_info.path,
                    function_name=function_name
                ))
    
    return routes


def _detect_router_prefixes(files: list[FileInfo]) -> dict[str, str]:
    """
    Detect router prefixes from main.py or app.py files.
    
    Looks for patterns like:
    app.include_router(trips.router, prefix="/api", tags=["trips"])
    
    Args:
        files: List of scanned FileInfo objects
        
    Returns:
        Dict mapping router module names to their prefixes
    """
    prefixes = {}
    
    # Pattern to match include_router calls
    # Example: app.include_router(trips.router, prefix="/api")
    pattern = re.compile(
        r'app\.include_router\s*\(\s*(\w+)\.router\s*,\s*prefix\s*=\s*["\']([^"\']+)["\']',
        re.IGNORECASE
    )
    
    for file_info in files:
        if file_info.suffix != '.py' or file_info.skipped:
            continue
        
        # Look in main.py or app.py files
        if 'main.py' not in file_info.path and 'app.py' not in file_info.path:
            continue
        
        if not file_info.text_preview:
            continue
        
        for match in pattern.finditer(file_info.text_preview):
            router_module = match.group(1)  # e.g., "trips"
            prefix = match.group(2)  # e.g., "/api"
            prefixes[router_module] = prefix
    
    return prefixes


def extract_all_routes(files: list[FileInfo]) -> list[RouteInfo]:
    """
    Extract all API routes from scanned files.
    
    Currently only supports FastAPI.
    Can be extended for Flask, Express, etc.
    
    Args:
        files: List of scanned FileInfo objects
        
    Returns:
        List of RouteInfo objects sorted by path and method
    """
    routes = []
    
    # Extract FastAPI routes
    routes.extend(extract_fastapi_routes(files))
    
    # Sort by path first (feature routes before root), then by method
    # This puts /api routes before / and /health
    def sort_key(r):
        # Feature routes (with /api) come first
        priority = 0 if r.path.startswith('/api') else 1
        return (priority, r.path, r.method)
    
    routes.sort(key=sort_key)
    
    return routes

# Made with Bob