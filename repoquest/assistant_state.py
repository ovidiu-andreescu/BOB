"""AI assistant state management for RepoQuest UI."""

from dataclasses import dataclass
from typing import Literal

from repoquest.assistant_provider import (
    get_assistant_config,
    get_assistant_service_config,
)


AIStatusType = Literal[
    "disabled",
    "ready",
    "no_key",
    "service_ready",
    "service_unavailable",
    "provider_error",
    "validation_error",
]


@dataclass
class AIStatus:
    """AI assistant status for UI display."""

    status: AIStatusType
    label: str
    message: str
    is_available: bool
    provider_info: str | None = None

    @property
    def is_ready(self) -> bool:
        """Check if AI is ready to use."""
        return self.status in {"ready", "service_ready"}

    @property
    def show_enable_hint(self) -> bool:
        """Check if we should show how to enable AI."""
        return self.status in {"disabled", "no_key"}

    @property
    def is_error(self) -> bool:
        """Check if status represents an error state."""
        return self.status in {"service_unavailable", "provider_error", "validation_error"}


def get_ai_status() -> AIStatus:
    """
    Get comprehensive AI assistant status for UI display.

    Returns a single AIStatus object that represents the current state
    of the AI assistant system, including provider info and availability.
    """
    ai_enabled, provider, api_key, model, local_base_url, local_model_name = get_assistant_config()
    service_url, _service_timeout = get_assistant_service_config()

    # Disabled state
    if not ai_enabled:
        return AIStatus(
            status="disabled",
            label="Deterministic",
            message="AI Assistant is disabled. All analysis is deterministic.",
            is_available=False,
            provider_info=None,
        )

    # Service mode
    if service_url:
        return AIStatus(
            status="service_ready",
            label="AI Ready (Service)",
            message="AI Assistant service is configured and ready.",
            is_available=True,
            provider_info=f"Service: {service_url}",
        )

    # Local provider mode
    if provider == "local":
        if not local_base_url or not local_model_name:
            return AIStatus(
                status="no_key",
                label="AI Needs Config",
                message="AI Assistant is enabled but local model configuration is incomplete.",
                is_available=False,
                provider_info="Set REPOQUEST_LOCAL_MODEL_BASE_URL and REPOQUEST_LOCAL_MODEL_NAME",
            )
        return AIStatus(
            status="ready",
            label="AI Ready (Local)",
            message="AI Assistant is ready with local model.",
            is_available=True,
            provider_info=f"Local: {local_model_name} @ {local_base_url}",
        )

    # Claude provider mode - check for API key
    if not api_key:
        return AIStatus(
            status="no_key",
            label="AI Needs Key",
            message="AI Assistant is enabled but CLAUDE_API_KEY is not configured.",
            is_available=False,
            provider_info=None,
        )

    # Ready with Claude provider
    return AIStatus(
        status="ready",
        label="AI Ready (Claude)",
        message="AI Assistant is ready with Claude provider.",
        is_available=True,
        provider_info=f"Claude: {model}",
    )


def format_ai_status_for_shell(status: AIStatus) -> dict[str, str]:
    """
    Format AI status for compact shell/hero display.

    Returns a dict with 'label' and optional 'title' for tooltip.
    """
    return {
        "label": status.label,
        "title": status.message,
    }


def format_ai_status_for_sidebar(status: AIStatus) -> dict[str, str]:
    """
    Format AI status for sidebar display with more detail.

    Returns a dict with 'message', 'type' (success/info/warning), and optional 'caption'.
    """
    if status.is_ready:
        return {
            "message": status.message,
            "type": "success",
            "caption": status.provider_info or "",
        }
    elif status.status == "no_key":
        caption = status.provider_info or "Set CLAUDE_API_KEY in .env or Streamlit secrets to enable."
        return {
            "message": status.message,
            "type": "warning",
            "caption": caption,
        }
    elif status.status == "disabled":
        return {
            "message": status.message,
            "type": "info",
            "caption": "Set REPOQUEST_AI_ENABLED=true to enable AI features. See docs/local_models.md for local model setup.",
        }
    else:
        return {
            "message": status.message,
            "type": "warning",
            "caption": "",
        }


def format_ai_status_for_tab(status: AIStatus) -> str:
    """
    Format AI status for tab-level display (compact, non-repetitive).

    Returns a single-line caption or empty string if AI is ready.
    """
    if status.is_ready:
        return ""  # Don't show anything in tabs when AI is ready
    elif status.status == "disabled":
        return "Enable AI in settings to add evidence-cited review notes."
    elif status.status == "no_key":
        return "Configure CLAUDE_API_KEY to enable AI review features."
    else:
        return "AI Assistant is not available."


# Made with Bob
