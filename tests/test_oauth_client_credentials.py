"""Tests for OAuth client_credentials grant support."""

from unittest.mock import patch, MagicMock

import pytest

from servicenow_mcp.utils.config import OAuthConfig, AuthConfig, AuthType
from servicenow_mcp.auth.auth_manager import AuthManager


class TestOAuthConfigModel:
    """OAuthConfig should accept username/password as optional."""

    def test_client_credentials_without_user_pass(self):
        """client_id + client_secret alone is valid (client_credentials grant)."""
        config = OAuthConfig(
            client_id="my_client",
            client_secret="my_secret",
        )
        assert config.client_id == "my_client"
        assert config.client_secret == "my_secret"
        assert config.username is None
        assert config.password is None

    def test_password_grant_with_all_fields(self):
        """All 4 fields = password grant (backward compatible)."""
        config = OAuthConfig(
            client_id="my_client",
            client_secret="my_secret",
            username="user",
            password="pass",
        )
        assert config.username == "user"
        assert config.password == "pass"


class TestAuthManagerClientCredentials:
    """AuthManager should use client_credentials when no username/password."""

    @patch("servicenow_mcp.auth.auth_manager.requests.post")
    def test_uses_client_credentials_grant(self, mock_post):
        """When username/password absent, grant_type=client_credentials."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test_token_cc",
            "token_type": "Bearer",
        }
        mock_post.return_value = mock_response

        auth_config = AuthConfig(
            type=AuthType.OAUTH,
            oauth=OAuthConfig(client_id="cid", client_secret="csec"),
        )
        manager = AuthManager(auth_config, "https://instance.service-now.com")
        headers = manager.get_headers()

        # Should have obtained token
        assert manager.token == "test_token_cc"
        assert "Bearer test_token_cc" in headers["Authorization"]
        # Verify grant_type=client_credentials was sent
        call_data = mock_post.call_args[1]["data"]
        assert call_data["grant_type"] == "client_credentials"
        assert "username" not in call_data
        assert "password" not in call_data

    @patch("servicenow_mcp.auth.auth_manager.requests.post")
    def test_uses_password_grant_when_user_provided(self, mock_post):
        """When username/password present, grant_type=password (backward compat)."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test_token_pw",
            "token_type": "Bearer",
        }
        mock_post.return_value = mock_response

        auth_config = AuthConfig(
            type=AuthType.OAUTH,
            oauth=OAuthConfig(
                client_id="cid",
                client_secret="csec",
                username="user",
                password="pass",
            ),
        )
        manager = AuthManager(auth_config, "https://instance.service-now.com")
        headers = manager.get_headers()

        assert manager.token == "test_token_pw"
        call_data = mock_post.call_args[1]["data"]
        assert call_data["grant_type"] == "password"
        assert call_data["username"] == "user"
        assert call_data["password"] == "pass"


class TestCliValidation:
    """CLI should accept OAuth without username/password."""

    def test_oauth_without_user_pass_does_not_raise(self):
        """OAuth with only client_id+secret should not raise ValueError."""
        from servicenow_mcp.cli import create_config
        import argparse

        args = argparse.Namespace(
            instance_url="https://test.service-now.com",
            debug=False,
            timeout=30,
            auth_type="oauth",
            client_id="cid",
            client_secret="csec",
            username=None,
            password=None,
            token_url=None,
            api_key=None,
            api_key_header="X-ServiceNow-API-Key",
        )
        config = create_config(args)
        assert config.auth.type == AuthType.OAUTH
        assert config.auth.oauth.client_id == "cid"
