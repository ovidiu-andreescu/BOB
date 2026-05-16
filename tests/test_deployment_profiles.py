"""Tests for deployment profile detection."""

import os
from unittest.mock import patch

from repoquest.config import get_deployment_profile, get_profile_description


class TestDeploymentProfileDetection:
    """Test deployment profile detection logic."""

    def test_deterministic_profile_default(self):
        """Test that deterministic is the default profile."""
        with patch.dict(os.environ, {}, clear=True):
            profile = get_deployment_profile()
            assert profile == "deterministic"

    def test_deterministic_profile_ai_disabled(self):
        """Test deterministic profile when AI is explicitly disabled."""
        with patch.dict(os.environ, {"REPOQUEST_AI_ENABLED": "false"}, clear=True):
            profile = get_deployment_profile()
            assert profile == "deterministic"

    def test_mock_assistant_direct_provider(self):
        """Test mock assistant profile with direct provider."""
        with patch.dict(
            os.environ,
            {
                "REPOQUEST_AI_ENABLED": "true",
                "REPOQUEST_ASSISTANT_PROVIDER": "mock",
            },
            clear=True,
        ):
            profile = get_deployment_profile()
            assert profile == "mock_assistant"

    def test_mock_assistant_service_provider(self):
        """Test mock assistant profile with service provider."""
        with patch.dict(
            os.environ,
            {
                "REPOQUEST_AI_ENABLED": "true",
                "REPOQUEST_ASSISTANT_SERVICE_URL": "http://assistant:8765",
                "REPOQUEST_ASSISTANT_SERVICE_PROVIDER": "mock",
            },
            clear=True,
        ):
            profile = get_deployment_profile()
            assert profile == "mock_assistant"

    def test_cloud_assistant_with_api_key(self):
        """Test cloud assistant profile with API key."""
        with patch.dict(
            os.environ,
            {
                "REPOQUEST_AI_ENABLED": "true",
                "CLAUDE_API_KEY": "sk-ant-test-key",
            },
            clear=True,
        ):
            profile = get_deployment_profile()
            assert profile == "cloud_assistant"

    def test_cloud_assistant_explicit_provider(self):
        """Test cloud assistant profile with explicit provider."""
        with patch.dict(
            os.environ,
            {
                "REPOQUEST_AI_ENABLED": "true",
                "REPOQUEST_ASSISTANT_PROVIDER": "claude",
                "CLAUDE_API_KEY": "sk-ant-test-key",
            },
            clear=True,
        ):
            profile = get_deployment_profile()
            assert profile == "cloud_assistant"

    def test_local_model_profile(self):
        """Test local model profile."""
        with patch.dict(
            os.environ,
            {
                "REPOQUEST_AI_ENABLED": "true",
                "REPOQUEST_ASSISTANT_PROVIDER": "local",
            },
            clear=True,
        ):
            profile = get_deployment_profile()
            assert profile == "local_model"

    def test_service_assistant_profile(self):
        """Test service assistant profile."""
        with patch.dict(
            os.environ,
            {
                "REPOQUEST_AI_ENABLED": "true",
                "REPOQUEST_ASSISTANT_SERVICE_URL": "http://assistant:8765",
            },
            clear=True,
        ):
            profile = get_deployment_profile()
            assert profile == "service_assistant"

    def test_service_assistant_with_claude(self):
        """Test service assistant profile with Claude provider."""
        with patch.dict(
            os.environ,
            {
                "REPOQUEST_AI_ENABLED": "true",
                "REPOQUEST_ASSISTANT_SERVICE_URL": "http://assistant:8765",
                "CLAUDE_API_KEY": "sk-ant-test-key",
            },
            clear=True,
        ):
            profile = get_deployment_profile()
            assert profile == "service_assistant"

    def test_ai_enabled_no_key_returns_deterministic(self):
        """Test that AI enabled without key returns deterministic."""
        with patch.dict(
            os.environ,
            {
                "REPOQUEST_AI_ENABLED": "true",
            },
            clear=True,
        ):
            profile = get_deployment_profile()
            assert profile == "deterministic"

    def test_ai_enabled_variations(self):
        """Test various truthy values for AI_ENABLED."""
        truthy_values = ["true", "True", "TRUE", "1", "yes", "Yes", "on", "On"]
        
        for value in truthy_values:
            with patch.dict(
                os.environ,
                {
                    "REPOQUEST_AI_ENABLED": value,
                    "REPOQUEST_ASSISTANT_PROVIDER": "mock",
                },
                clear=True,
            ):
                profile = get_deployment_profile()
                assert profile == "mock_assistant", f"Failed for value: {value}"

    def test_ai_disabled_variations(self):
        """Test various falsy values for AI_ENABLED."""
        falsy_values = ["false", "False", "FALSE", "0", "no", "No", "off", "Off", ""]
        
        for value in falsy_values:
            with patch.dict(
                os.environ,
                {
                    "REPOQUEST_AI_ENABLED": value,
                },
                clear=True,
            ):
                profile = get_deployment_profile()
                assert profile == "deterministic", f"Failed for value: {value}"


class TestProfileDescriptions:
    """Test profile description strings."""

    def test_all_profiles_have_descriptions(self):
        """Test that all profiles have descriptions."""
        profiles = [
            "deterministic",
            "mock_assistant",
            "cloud_assistant",
            "local_model",
            "service_assistant",
        ]
        
        for profile in profiles:
            desc = get_profile_description(profile)
            assert desc, f"Profile {profile} has no description"
            assert len(desc) > 10, f"Profile {profile} description too short"

    def test_unknown_profile_description(self):
        """Test description for unknown profile."""
        desc = get_profile_description("unknown_profile")
        assert desc == "Unknown profile"

    def test_deterministic_description_content(self):
        """Test deterministic profile description mentions key features."""
        desc = get_profile_description("deterministic")
        assert "no AI" in desc.lower() or "deterministic" in desc.lower()
        assert "no secrets" in desc.lower()

    def test_mock_description_content(self):
        """Test mock profile description mentions testing."""
        desc = get_profile_description("mock_assistant")
        assert "mock" in desc.lower() or "testing" in desc.lower()

    def test_cloud_description_content(self):
        """Test cloud profile description mentions Claude."""
        desc = get_profile_description("cloud_assistant")
        assert "claude" in desc.lower() or "cloud" in desc.lower()

    def test_local_model_description_content(self):
        """Test local model profile description mentions local/private."""
        desc = get_profile_description("local_model")
        assert "local" in desc.lower() or "private" in desc.lower()

    def test_service_description_content(self):
        """Test service profile description mentions service."""
        desc = get_profile_description("service_assistant")
        assert "service" in desc.lower() or "async" in desc.lower()


class TestProfilePriority:
    """Test profile detection priority and edge cases."""

    def test_service_url_takes_priority_over_direct_provider(self):
        """Test that service URL takes priority over direct provider."""
        with patch.dict(
            os.environ,
            {
                "REPOQUEST_AI_ENABLED": "true",
                "REPOQUEST_ASSISTANT_SERVICE_URL": "http://assistant:8765",
                "REPOQUEST_ASSISTANT_PROVIDER": "mock",
            },
            clear=True,
        ):
            profile = get_deployment_profile()
            # Service URL should take priority
            assert profile == "service_assistant"

    def test_service_mock_provider_detected(self):
        """Test that service mock provider is correctly detected."""
        with patch.dict(
            os.environ,
            {
                "REPOQUEST_AI_ENABLED": "true",
                "REPOQUEST_ASSISTANT_SERVICE_URL": "http://assistant:8765",
                "REPOQUEST_ASSISTANT_SERVICE_PROVIDER": "mock",
            },
            clear=True,
        ):
            profile = get_deployment_profile()
            assert profile == "mock_assistant"

    def test_empty_service_url_uses_direct_provider(self):
        """Test that empty service URL falls back to direct provider."""
        with patch.dict(
            os.environ,
            {
                "REPOQUEST_AI_ENABLED": "true",
                "REPOQUEST_ASSISTANT_SERVICE_URL": "",
                "REPOQUEST_ASSISTANT_PROVIDER": "mock",
            },
            clear=True,
        ):
            profile = get_deployment_profile()
            assert profile == "mock_assistant"

    def test_whitespace_only_values_ignored(self):
        """Test that whitespace-only values are treated as empty."""
        with patch.dict(
            os.environ,
            {
                "REPOQUEST_AI_ENABLED": "true",
                "REPOQUEST_ASSISTANT_SERVICE_URL": "   ",
                "REPOQUEST_ASSISTANT_PROVIDER": "  ",
                "CLAUDE_API_KEY": "  ",
            },
            clear=True,
        ):
            profile = get_deployment_profile()
            assert profile == "deterministic"

    def test_case_insensitive_provider_names(self):
        """Test that provider names are case-insensitive."""
        providers = [
            ("MOCK", "mock_assistant"),
            ("Mock", "mock_assistant"),
            ("LOCAL", "local_model"),
            ("Local", "local_model"),
            ("CLAUDE", "deterministic"),  # No key, so deterministic
            ("Claude", "deterministic"),
        ]
        
        for provider_value, expected_profile in providers:
            with patch.dict(
                os.environ,
                {
                    "REPOQUEST_AI_ENABLED": "true",
                    "REPOQUEST_ASSISTANT_PROVIDER": provider_value,
                },
                clear=True,
            ):
                profile = get_deployment_profile()
                assert profile == expected_profile, f"Failed for provider: {provider_value}"


class TestProfileIntegration:
    """Test profile detection in realistic scenarios."""

    def test_streamlit_cloud_deterministic_scenario(self):
        """Test typical Streamlit Cloud deterministic deployment."""
        with patch.dict(os.environ, {}, clear=True):
            profile = get_deployment_profile()
            assert profile == "deterministic"
            desc = get_profile_description(profile)
            assert "no secrets" in desc.lower()

    def test_local_development_mock_scenario(self):
        """Test typical local development with mock."""
        with patch.dict(
            os.environ,
            {
                "REPOQUEST_AI_ENABLED": "true",
                "REPOQUEST_ASSISTANT_PROVIDER": "mock",
            },
            clear=True,
        ):
            profile = get_deployment_profile()
            assert profile == "mock_assistant"

    def test_docker_compose_mock_service_scenario(self):
        """Test Docker Compose with mock service."""
        with patch.dict(
            os.environ,
            {
                "REPOQUEST_AI_ENABLED": "true",
                "REPOQUEST_ASSISTANT_SERVICE_URL": "http://assistant:8765",
                "REPOQUEST_ASSISTANT_SERVICE_PROVIDER": "mock",
            },
            clear=True,
        ):
            profile = get_deployment_profile()
            assert profile == "mock_assistant"

    def test_docker_compose_claude_service_scenario(self):
        """Test Docker Compose with Claude service."""
        with patch.dict(
            os.environ,
            {
                "REPOQUEST_AI_ENABLED": "true",
                "REPOQUEST_ASSISTANT_SERVICE_URL": "http://assistant:8765",
                "CLAUDE_API_KEY": "sk-ant-test-key",
            },
            clear=True,
        ):
            profile = get_deployment_profile()
            assert profile == "service_assistant"

    def test_docker_compose_local_model_scenario(self):
        """Test Docker Compose with local model."""
        with patch.dict(
            os.environ,
            {
                "REPOQUEST_AI_ENABLED": "true",
                "REPOQUEST_ASSISTANT_SERVICE_URL": "http://assistant:8765",
                "REPOQUEST_ASSISTANT_SERVICE_PROVIDER": "local",
                "REPOQUEST_LOCAL_MODEL_BASE_URL": "http://host.docker.internal:11434/v1",
                "REPOQUEST_LOCAL_MODEL_NAME": "llama3.1",
            },
            clear=True,
        ):
            profile = get_deployment_profile()
            # Service URL present means service_assistant, regardless of provider type
            assert profile == "service_assistant"

    def test_hosted_streamlit_with_claude_scenario(self):
        """Test hosted Streamlit with Claude secrets."""
        with patch.dict(
            os.environ,
            {
                "REPOQUEST_AI_ENABLED": "true",
                "CLAUDE_API_KEY": "sk-ant-test-key",
                "CLAUDE_MODEL": "claude-sonnet-4-20250514",
            },
            clear=True,
        ):
            profile = get_deployment_profile()
            assert profile == "cloud_assistant"
