"""Parse imports and build dependency graphs."""

import ast
import re
from pathlib import PurePosixPath
from repoquest.models import ImportEdge, FileInfo


def parse_python_imports(file_info: FileInfo, all_files: list[FileInfo]) -> list[ImportEdge]:
    """
    Parse Python imports using AST and resolve to actual files.
    
    Args:
        file_info: FileInfo object with Python code
        all_files: All scanned files for resolution
        
    Returns:
        List of ImportEdge objects
    """
    edges = []
    
    if file_info.suffix != '.py' or file_info.skipped or not file_info.text_preview:
        return edges
    
    # Build file lookup map (exclude __init__.py from primary targets)
    file_map = {}
    init_map = {}
    for f in all_files:
        if f.suffix == '.py':
            if f.name == '__init__.py':
                init_map[f.path] = f
            else:
                file_map[f.path] = f
    
    try:
        tree = ast.parse(file_info.text_preview)
    except SyntaxError:
        return edges
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            # import module
            for alias in node.names:
                target = _resolve_python_import(alias.name, file_info.path, file_map, init_map)
                if target:
                    edges.append(ImportEdge(
                        source=file_info.path,
                        target=target,
                        kind="python_import",
                        confidence=1.0
                    ))
        
        elif isinstance(node, ast.ImportFrom):
            # from module import name
            if node.module:
                # Handle relative imports
                if node.level > 0:
                    target = _resolve_relative_python_import(
                        file_info.path, node.module or "", node.level, file_map, init_map
                    )
                else:
                    target = _resolve_python_import(node.module, file_info.path, file_map, init_map)
                
                if target:
                    edges.append(ImportEdge(
                        source=file_info.path,
                        target=target,
                        kind="python_import",
                        confidence=0.9 if node.level > 0 else 1.0
                    ))
    
    return edges


def _resolve_python_import(module_name: str, source_path: str, file_map: dict, init_map: dict) -> str | None:
    """
    Resolve Python import to actual file path.
    
    For "from routes import trips", prefer backend/routes/trips.py over backend/routes/__init__.py.
    
    Args:
        module_name: Module name like "routes.trips" or "routes"
        source_path: Path of file doing the import
        file_map: Map of non-__init__ file paths
        init_map: Map of __init__.py file paths
        
    Returns:
        Resolved file path or None
    """
    # Get source directory
    source_dir = str(PurePosixPath(source_path).parent)
    
    # Split module into parts
    module_parts = module_name.split('.')
    
    # Try to resolve relative to source directory
    candidates = []
    
    # Try as direct file (prefer this)
    module_path = '/'.join(module_parts)
    candidates.append(f"{source_dir}/{module_path}.py")
    
    # Also try from project root for backend/frontend structure
    if 'backend' in source_path:
        parts = source_path.split('/')
        if 'backend' in parts:
            idx = parts.index('backend')
            root = '/'.join(parts[:idx+1])
            candidates.append(f"{root}/{module_path}.py")
    
    # Check candidates in file_map first (non-__init__ files)
    for path in candidates:
        if path in file_map:
            return path
    
    # Fall back to __init__.py only if no direct file found
    for path in candidates:
        init_path = f"{path.rsplit('.py', 1)[0]}/__init__.py"
        if init_path in init_map:
            return init_path
    
    return None


def _resolve_relative_python_import(
    source_path: str, module: str, level: int, file_map: dict, init_map: dict
) -> str | None:
    """
    Resolve relative Python imports.
    
    Args:
        source_path: Path of the file doing the import
        module: Module name (may be empty for "from . import x")
        level: Number of dots (1 for ".", 2 for "..", etc.)
        file_map: Map of non-__init__ file paths
        init_map: Map of __init__.py file paths
        
    Returns:
        Resolved file path or None
    """
    source_dir = PurePosixPath(source_path).parent
    
    # Go up 'level' directories
    target_dir = source_dir
    for _ in range(level):
        target_dir = target_dir.parent
    
    # Combine with module name if present
    if module:
        module_parts = module.split('.')
        target_path = target_dir / '/'.join(module_parts)
        
        # Try as direct file first
        py_path = str(target_path) + '.py'
        if py_path in file_map:
            return py_path
        
        # Fall back to __init__.py
        init_path = str(target_path) + '/__init__.py'
        if init_path in init_map:
            return init_path
    else:
        # Just relative import from parent
        init_path = str(target_dir / '__init__.py')
        if init_path in init_map:
            return init_path
    
    return None


def parse_js_ts_imports(file_info: FileInfo, all_files: list[FileInfo]) -> list[ImportEdge]:
    """
    Parse JavaScript/TypeScript imports using regex and resolve to actual files.
    
    Args:
        file_info: FileInfo object with JS/TS code
        all_files: All scanned files for resolution
        
    Returns:
        List of ImportEdge objects
    """
    edges = []
    
    if file_info.suffix not in ['.js', '.jsx', '.ts', '.tsx', '.mjs']:
        return edges
    
    if file_info.skipped or not file_info.text_preview:
        return edges
    
    # Build file lookup map
    file_map = {f.path: f for f in all_files if f.suffix in ['.js', '.jsx', '.ts', '.tsx', '.mjs']}
    
    # Regex patterns for different import styles
    patterns = [
        # import X from "module" or import { X } from "module"
        re.compile(r'import\s+(?:\w+|\{[^}]+\})\s+from\s+["\']([^"\']+)["\']'),
        # import "module"
        re.compile(r'import\s+["\']([^"\']+)["\']'),
        # require("module")
        re.compile(r'require\s*\(\s*["\']([^"\']+)["\']\s*\)'),
    ]
    
    for pattern in patterns:
        for match in pattern.finditer(file_info.text_preview):
            import_path = match.group(1)
            
            # Only process relative imports (start with . or ..)
            if import_path.startswith('.'):
                target = _resolve_js_ts_import(file_info.path, import_path, file_map)
                if target:
                    edges.append(ImportEdge(
                        source=file_info.path,
                        target=target,
                        kind="js_import" if file_info.suffix in ['.js', '.jsx', '.mjs'] else "ts_import",
                        confidence=0.9
                    ))
    
    return edges


def _resolve_js_ts_import(source_path: str, import_path: str, file_map: dict) -> str | None:
    """
    Resolve relative JS/TS imports to actual file paths using repo-relative paths.
    
    Examples:
    - "./App" from frontend/src/main.tsx -> frontend/src/App.tsx
    - "./pages/TripsPage" from frontend/src/App.tsx -> frontend/src/pages/TripsPage.tsx
    - "../components/TripCard" from frontend/src/pages/TripsPage.tsx -> frontend/src/components/TripCard.tsx
    
    Args:
        source_path: Repo-relative path of the file doing the import
        import_path: Import path (e.g., "./components/TripCard")
        file_map: Map of file paths to FileInfo
        
    Returns:
        Resolved repo-relative file path or None
    """
    # Use PurePosixPath for repo-relative path manipulation
    source_dir = PurePosixPath(source_path).parent
    
    # Resolve the import path relative to source directory
    target_base = source_dir / import_path
    
    # Normalize the path (resolve .. and .)
    try:
        target_base = PurePosixPath(*target_base.parts)  # Normalize
    except (ValueError, IndexError):
        return None
    
    # Try common extensions
    extensions = ['.tsx', '.ts', '.jsx', '.js', '.mjs']
    
    # Try direct file with extensions
    for ext in extensions:
        target_path = str(target_base) + ext
        if target_path in file_map:
            return target_path
    
    # Try index files
    for ext in extensions:
        target_path = str(target_base / f'index{ext}')
        if target_path in file_map:
            return target_path
    
    return None


def build_import_graph(files: list[FileInfo], base_path: str) -> list[ImportEdge]:
    """
    Build import graph from all scanned files.
    
    Args:
        files: List of scanned FileInfo objects
        base_path: Base path of the repository (unused, kept for compatibility)
        
    Returns:
        List of ImportEdge objects representing local file dependencies
    """
    all_edges = []
    
    for file_info in files:
        # Parse Python imports
        if file_info.suffix == '.py':
            all_edges.extend(parse_python_imports(file_info, files))
        
        # Parse JS/TS imports
        elif file_info.suffix in ['.js', '.jsx', '.ts', '.tsx', '.mjs']:
            all_edges.extend(parse_js_ts_imports(file_info, files))
    
    return all_edges

# Made with Bob