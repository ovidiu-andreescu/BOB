"""Tests for AI assistant state management."""


from repoquest.assistant_state import (
    AIStatus,
    get_ai_status,
    format_ai_status_for_shell,
    format_ai_status_for_sidebar,
    format_ai_status_for_tab,
)


def test_ai_status_disabled(monkeypatch):
    """Test AI status when disabled."""
    monkeypatch.delenv("REPOQUEST_AI_ENABLED", raising=False)
    monkeypatch.delenv("CLAUDE_API_KEY", raising=False)

    status = get_ai_status()

    assert status.status == "disabled"
    assert status.label == "Deterministic"
    assert not status.is_available
    assert not status.is_ready
    assert status.show_enable_hint
    assert not status.is_error
    assert status.provider_info is None


def test_ai_status_no_key(monkeypatch):
    """Test AI status when enabled but no API key."""
    monkeypatch.setenv("REPOQUEST_AI_ENABLED", "true")
    monkeypatch.delenv("CLAUDE_API_KEY", raising=False)

    status = get_ai_status()

    assert status.status == "no_key"
    assert status.label == "AI Needs Key"
    assert not status.is_available
    assert not status.is_ready
    assert status.show_enable_hint
    assert not status.is_error


def test_ai_status_ready_direct(monkeypatch):
    """Test AI status when ready with direct provider."""
    monkeypatch.setenv("REPOQUEST_AI_ENABLED", "true")
    monkeypatch.setenv("CLAUDE_API_KEY", "test-key")
    monkeypatch.setenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
    monkeypatch.delenv("REPOQUEST_ASSISTANT_SERVICE_URL", raising=False)

    status = get_ai_status()

    assert status.status == "ready"
    assert status.label == "AI Ready (Claude)"
    assert status.is_available
    assert status.is_ready
    assert not status.show_enable_hint
    assert not status.is_error
    assert status.provider_info == "Claude: claude-sonnet-4-20250514"


def test_ai_status_service_ready(monkeypatch):
    """Test AI status when using assistant service."""
    monkeypatch.setenv("REPOQUEST_AI_ENABLED", "true")
    monkeypatch.setenv("REPOQUEST_ASSISTANT_SERVICE_URL", "http://assistant:8765")
    monkeypatch.delenv("CLAUDE_API_KEY", raising=False)

    status = get_ai_status()

    assert status.status == "service_ready"
    assert status.label == "AI Ready (Service)"
    assert status.is_available
    assert status.is_ready
    assert not status.show_enable_hint
    assert not status.is_error
    assert status.provider_info == "Service: http://assistant:8765"


def test_format_ai_status_for_shell_disabled(monkeypatch):
    """Test shell formatting for disabled state."""
    monkeypatch.delenv("REPOQUEST_AI_ENABLED", raising=False)

    status = get_ai_status()
    shell_format = format_ai_status_for_shell(status)

    assert shell_format["label"] == "Deterministic"
    assert "disabled" in shell_format["title"].lower()


def test_format_ai_status_for_shell_ready(monkeypatch):
    """Test shell formatting for ready state."""
    monkeypatch.setenv("REPOQUEST_AI_ENABLED", "true")
    monkeypatch.setenv("CLAUDE_API_KEY", "test-key")

    status = get_ai_status()
    shell_format = format_ai_status_for_shell(status)

    assert shell_format["label"] == "AI Ready (Claude)"
    assert "ready" in shell_format["title"].lower()


def test_format_ai_status_for_sidebar_disabled(monkeypatch):
    """Test sidebar formatting for disabled state."""
    monkeypatch.delenv("REPOQUEST_AI_ENABLED", raising=False)

    status = get_ai_status()
    sidebar_format = format_ai_status_for_sidebar(status)

    assert sidebar_format["type"] == "info"
    assert "disabled" in sidebar_format["message"].lower()
    assert "REPOQUEST_AI_ENABLED=true" in sidebar_format["caption"]


def test_format_ai_status_for_sidebar_no_key(monkeypatch):
    """Test sidebar formatting for no key state."""
    monkeypatch.setenv("REPOQUEST_AI_ENABLED", "true")
    monkeypatch.delenv("CLAUDE_API_KEY", raising=False)

    status = get_ai_status()
    sidebar_format = format_ai_status_for_sidebar(status)

    assert sidebar_format["type"] == "warning"
    assert "CLAUDE_API_KEY" in sidebar_format["message"]
    assert "CLAUDE_API_KEY" in sidebar_format["caption"]


def test_format_ai_status_for_sidebar_ready(monkeypatch):
    """Test sidebar formatting for ready state."""
    monkeypatch.setenv("REPOQUEST_AI_ENABLED", "true")
    monkeypatch.setenv("CLAUDE_API_KEY", "test-key")
    monkeypatch.setenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")

    status = get_ai_status()
    sidebar_format = format_ai_status_for_sidebar(status)

    assert sidebar_format["type"] == "success"
    assert "ready" in sidebar_format["message"].lower()
    assert "Claude: claude-sonnet-4-20250514" in sidebar_format["caption"]


def test_format_ai_status_for_tab_ready(monkeypatch):
    """Test tab formatting returns empty string when ready."""
    monkeypatch.setenv("REPOQUEST_AI_ENABLED", "true")
    monkeypatch.setenv("CLAUDE_API_KEY", "test-key")

    status = get_ai_status()
    tab_caption = format_ai_status_for_tab(status)

    assert tab_caption == ""  # Don't show anything when ready


def test_format_ai_status_for_tab_disabled(monkeypatch):
    """Test tab formatting for disabled state."""
    monkeypatch.delenv("REPOQUEST_AI_ENABLED", raising=False)

    status = get_ai_status()
    tab_caption = format_ai_status_for_tab(status)

    assert tab_caption != ""
    assert "enable" in tab_caption.lower()


def test_format_ai_status_for_tab_no_key(monkeypatch):
    """Test tab formatting for no key state."""
    monkeypatch.setenv("REPOQUEST_AI_ENABLED", "true")
    monkeypatch.delenv("CLAUDE_API_KEY", raising=False)

    status = get_ai_status()
    tab_caption = format_ai_status_for_tab(status)

    assert tab_caption != ""
    assert "CLAUDE_API_KEY" in tab_caption


def test_ai_status_properties():
    """Test AIStatus property methods."""
    # Ready state
    ready_status = AIStatus(
        status="ready",
        label="AI Ready",
        message="Ready",
        is_available=True,
        provider_info="Claude",
    )
    assert ready_status.is_ready
    assert not ready_status.show_enable_hint
    assert not ready_status.is_error

    # Disabled state
    disabled_status = AIStatus(
        status="disabled",
        label="Disabled",
        message="Disabled",
        is_available=False,
    )
    assert not disabled_status.is_ready
    assert disabled_status.show_enable_hint
    assert not disabled_status.is_error

    # Error state
    error_status = AIStatus(
        status="provider_error",
        label="Error",
        message="Error",
        is_available=False,
    )
    assert not error_status.is_ready
    assert not error_status.show_enable_hint
    assert error_status.is_error


def test_ai_status_with_local_env(tmp_path, monkeypatch):
    """Test AI status reads from local .env file."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("REPOQUEST_AI_ENABLED", raising=False)
    monkeypatch.delenv("CLAUDE_API_KEY", raising=False)

    (tmp_path / ".env").write_text(
        "REPOQUEST_AI_ENABLED=true\n"
        "CLAUDE_API_KEY=test-key-from-env\n"
        "CLAUDE_MODEL=test-model\n",
        encoding="utf-8",
    )

    status = get_ai_status()

    assert status.is_ready
    assert status.provider_info == "Claude: test-model"


# Made with Bob
