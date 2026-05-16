"""Tests for local model assistant provider."""

import json
import urllib.error
from unittest.mock import Mock, patch
from repoquest.assistant_provider import (
    LocalModelAssistantProvider,
    get_assistant_config,
    get_assistant_provider,
)
from repoquest.assistant_models import AssistantRequest


def test_local_provider_config_parsing():
    """Test that local provider config can be parsed without a running model."""
    with patch.dict("os.environ", {
        "REPOQUEST_AI_ENABLED": "true",
        "REPOQUEST_ASSISTANT_PROVIDER": "local",
        "REPOQUEST_LOCAL_MODEL_BASE_URL": "http://localhost:11434/v1",
        "REPOQUEST_LOCAL_MODEL_NAME": "llama3.1",
    }):
        enabled, provider, api_key, model, local_url, local_model = get_assistant_config()
        
        assert enabled is True
        assert provider == "local"
        assert local_url == "http://localhost:11434/v1"
        assert local_model == "llama3.1"


def test_local_provider_uses_configured_values():
    """Test that local provider uses configured base URL and model name."""
    provider = LocalModelAssistantProvider(
        base_url="http://test.local:8080/v1",
        model="test-model"
    )
    
    assert provider.base_url == "http://test.local:8080/v1"
    assert provider.model == "test-model"


def test_local_provider_strips_trailing_slash():
    """Test that local provider strips trailing slash from base URL."""
    provider = LocalModelAssistantProvider(
        base_url="http://test.local:8080/v1/",
        model="test-model"
    )
    
    assert provider.base_url == "http://test.local:8080/v1"


def test_local_provider_adds_v1_when_missing():
    """Test that local provider normalizes OpenAI-compatible base URLs."""
    provider = LocalModelAssistantProvider(
        base_url="http://test.local:8080",
        model="test-model"
    )

    assert provider.base_url == "http://test.local:8080/v1"


def test_local_provider_missing_base_url():
    """Test that local provider returns error when base URL is missing."""
    provider = LocalModelAssistantProvider(base_url="", model="test-model")
    
    request = AssistantRequest(
        section_id="test",
        section_title="Test",
        user_goal="Test goal",
        context_summary="Test context",
        evidence_files=[],
        capped_snippets={},
    )
    
    response = provider.generate(request)
    
    assert response.status == "error"
    assert "REPOQUEST_LOCAL_MODEL_BASE_URL" in response.message
    assert response.provider == "local"


def test_local_provider_missing_model_name():
    """Test that local provider returns error when model name is missing."""
    provider = LocalModelAssistantProvider(
        base_url="http://test.local:8080/v1",
        model=""
    )
    
    request = AssistantRequest(
        section_id="test",
        section_title="Test",
        user_goal="Test goal",
        context_summary="Test context",
        evidence_files=[],
        capped_snippets={},
    )
    
    response = provider.generate(request)
    
    assert response.status == "error"
    assert "REPOQUEST_LOCAL_MODEL_NAME" in response.message
    assert response.provider == "local"


def test_local_provider_network_failure():
    """Test that local provider network failures return assistant errors."""
    provider = LocalModelAssistantProvider(
        base_url="http://nonexistent.local:9999/v1",
        model="test-model"
    )
    
    request = AssistantRequest(
        section_id="test",
        section_title="Test",
        user_goal="Test goal",
        context_summary="Test context",
        evidence_files=[],
        capped_snippets={},
    )
    
    response = provider.generate(request)
    
    assert response.status == "error"
    assert response.provider == "local"
    assert response.model == "test-model"
    assert "Network error" in response.message or "error" in response.message.lower()


def test_local_provider_mock_success():
    """Test local provider with mocked successful response."""
    provider = LocalModelAssistantProvider(
        base_url="http://test.local:8080/v1",
        model="test-model"
    )
    
    mock_response_data = {
        "choices": [
            {
                "message": {
                    "content": "This is a test response from the local model."
                }
            }
        ]
    }
    
    request = AssistantRequest(
        section_id="test",
        section_title="Test",
        user_goal="Test goal",
        context_summary="Test context",
        evidence_files=["test.py"],
        capped_snippets={"test.py": "def test(): pass"},
    )
    
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_response = Mock()
        mock_response.read.return_value = json.dumps(mock_response_data).encode("utf-8")
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response
        
        response = provider.generate(request)
    
    assert response.status == "ok"
    assert response.response_text == "This is a test response from the local model."
    assert response.provider == "local"
    assert response.model == "test-model"


def test_local_provider_extracts_citations():
    """Test that local provider extracts citations from response."""
    provider = LocalModelAssistantProvider(
        base_url="http://test.local:8080/v1",
        model="test-model"
    )
    
    mock_response_data = {
        "choices": [
            {
                "message": {
                    "content": "The file `test.py` contains a test function."
                }
            }
        ]
    }
    
    request = AssistantRequest(
        section_id="test",
        section_title="Test",
        user_goal="Test goal",
        context_summary="Test context",
        evidence_files=["test.py", "other.py"],
        capped_snippets={},
    )
    
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_response = Mock()
        mock_response.read.return_value = json.dumps(mock_response_data).encode("utf-8")
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response
        
        response = provider.generate(request)
    
    assert response.status == "ok"
    assert len(response.citations) == 1
    assert response.citations[0].file_path == "test.py"


def test_get_assistant_provider_returns_local_when_configured():
    """Test that factory returns local provider when configured."""
    with patch.dict("os.environ", {
        "REPOQUEST_AI_ENABLED": "true",
        "REPOQUEST_ASSISTANT_PROVIDER": "local",
        "REPOQUEST_LOCAL_MODEL_BASE_URL": "http://localhost:11434/v1",
        "REPOQUEST_LOCAL_MODEL_NAME": "llama3.1",
    }):
        provider = get_assistant_provider()
        
        assert isinstance(provider, LocalModelAssistantProvider)
        assert provider.base_url == "http://localhost:11434/v1"
        assert provider.model == "llama3.1"


def test_get_assistant_provider_returns_disabled_when_local_incomplete():
    """Test that factory returns disabled provider when local config is incomplete."""
    with patch.dict("os.environ", {
        "REPOQUEST_AI_ENABLED": "true",
        "REPOQUEST_ASSISTANT_PROVIDER": "local",
        "REPOQUEST_LOCAL_MODEL_BASE_URL": "",
        "REPOQUEST_LOCAL_MODEL_NAME": "",
    }):
        provider = get_assistant_provider()
        
        # Should return disabled provider when local config is incomplete
        from repoquest.assistant_provider import DisabledAssistantProvider
        assert isinstance(provider, DisabledAssistantProvider)


def test_local_provider_empty_response():
    """Test local provider handles empty response from model."""
    provider = LocalModelAssistantProvider(
        base_url="http://test.local:8080/v1",
        model="test-model"
    )
    
    mock_response_data = {
        "choices": [
            {
                "message": {
                    "content": ""
                }
            }
        ]
    }
    
    request = AssistantRequest(
        section_id="test",
        section_title="Test",
        user_goal="Test goal",
        context_summary="Test context",
        evidence_files=[],
        capped_snippets={},
    )
    
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_response = Mock()
        mock_response.read.return_value = json.dumps(mock_response_data).encode("utf-8")
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response
        
        response = provider.generate(request)
    
    assert response.status == "error"
    assert "Empty response" in response.message


def test_local_provider_404_mentions_chat_completions():
    """Test that 404s explain the required OpenAI-compatible chat endpoint."""
    provider = LocalModelAssistantProvider(
        base_url="http://test.local:8080/v1",
        model="test-model"
    )

    request = AssistantRequest(
        section_id="test",
        section_title="Test",
        user_goal="Test goal",
        context_summary="Test context",
        evidence_files=[],
        capped_snippets={},
    )

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="http://test.local:8080/v1/chat/completions",
            code=404,
            msg="not found",
            hdrs=None,
            fp=None,
        )
        response = provider.generate(request)

    assert response.status == "error"
    assert "chat completions endpoint" in response.message
    assert "http://test.local:8080/v1/chat/completions" in response.message

# Made with Bob
