"""Configuration constants for RepoQuest."""

# File scanning limits
MAX_ZIP_SIZE_MB = 25
MAX_FILES_SCANNED = 600
MAX_FILE_SIZE_BYTES = 512_000
MAX_TEXT_PREVIEW_CHARS = 20_000
MAX_GRAPH_NODES = 80

# Onboarding generation limits
MAX_READING_PATH_ITEMS = 9
MAX_COMPONENT_CARDS = 30
MAX_QUIZ_QUESTIONS = 8

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

# Deployment profile detection
def get_deployment_profile() -> str:
    """
    Detect the current deployment profile based on environment configuration.
    
    Returns one of:
    - "deterministic" - Default, no AI, no secrets required
    - "mock_assistant" - AI enabled with mock provider for testing
    - "cloud_assistant" - AI enabled with Claude/cloud provider
    - "local_model" - AI enabled with local model provider
    - "service_assistant" - AI enabled via async assistant service
    """
    from repoquest.assistant_provider import (
        get_assistant_config,
        get_assistant_service_config,
        get_config_value,
    )

    ai_enabled, provider, api_key, _model, _local_base_url, _local_model_name = get_assistant_config()
    
    if not ai_enabled:
        return "deterministic"
    
    # Check for assistant service URL
    service_url, _service_timeout = get_assistant_service_config()
    if service_url:
        # Service mode - check service provider
        service_provider = get_config_value("REPOQUEST_ASSISTANT_SERVICE_PROVIDER").lower()
        if service_provider == "mock":
            return "mock_assistant"
        return "service_assistant"
    
    # Direct provider mode
    if provider == "mock":
        return "mock_assistant"
    elif provider == "local":
        return "local_model"
    elif provider in {"claude", ""}:
        # Default to cloud if API key is present
        if api_key:
            return "cloud_assistant"
        return "deterministic"
    
    return "deterministic"


def get_profile_description(profile: str) -> str:
    """Get a human-friendly description of the deployment profile."""
    descriptions = {
        "deterministic": "Deterministic Code Assistant (no AI, no secrets required)",
        "mock_assistant": "Mock AI Assistant (testing mode, no network calls)",
        "cloud_assistant": "Cloud AI Assistant (Claude API)",
        "local_model": "Local Model Assistant (private/local inference)",
        "service_assistant": "Async Assistant Service (separate service container)",
    }
    return descriptions.get(profile, "Unknown profile")


# Made with Bob
