"""Configuration constants for RepoQuest."""

# File scanning limits
MAX_ZIP_SIZE_MB = 25
MAX_FILES_SCANNED = 600
MAX_FILE_SIZE_BYTES = 512_000
MAX_TEXT_PREVIEW_CHARS = 20_000
MAX_GRAPH_NODES = 80

# Folders to ignore during scanning
IGNORE_FOLDERS = {
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
    ".next",
    "coverage",
    ".streamlit",
    ".DS_Store",
}

# File extensions to skip (binary files)
SKIP_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".ico",
    ".pdf",
    ".mp4",
    ".mov",
    ".avi",
    ".zip",
    ".tar",
    ".gz",
    ".7z",
    ".exe",
    ".dll",
    ".so",
    ".pyc",
    ".lock",
}

# Language mapping by extension
LANGUAGE_MAP = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".json": "JSON",
    ".md": "Markdown",
    ".txt": "Text",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".toml": "TOML",
    ".css": "CSS",
    ".html": "HTML",
    ".sh": "Shell",
}

# Made with Bob
