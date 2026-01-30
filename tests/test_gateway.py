"""Tests for Clawdbot gateway adapter."""

from unittest.mock import MagicMock, patch

from hey_clever.adapters.clawdbot_gateway import ClawdbotGateway
from hey_clever.config.settings import GatewayConfig


def _make_gateway(
    url: str = "http://localhost:18789", token: str = "test-token"
) -> ClawdbotGateway:
    return ClawdbotGateway(GatewayConfig(url=url, token=token))


class TestClawdbotGateway:
    @patch("hey_clever.adapters.clawdbot_gateway.requests.post")
    def test_send_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"choices": [{"message": {"content": "Hello there!"}}]}
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        gw = _make_gateway()
        result = gw.send("hi")
        assert result == "Hello there!"

        url_arg = mock_post.call_args[0][0]
        assert "v1/chat/completions" in url_arg

    @patch("hey_clever.adapters.clawdbot_gateway.requests.post")
    def test_send_includes_auth_header(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"choices": [{"message": {"content": "ok"}}]}
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        gw = _make_gateway(token="secret-123")
        gw.send("test")

        headers = mock_post.call_args[1].get("headers") or mock_post.call_args.kwargs.get("headers")
        assert headers["Authorization"] == "Bearer secret-123"
        assert headers["x-clawdbot-agent-id"] == "main"

    @patch("hey_clever.adapters.clawdbot_gateway.requests.post")
    def test_send_failure_returns_error_message(self, mock_post):
        mock_post.side_effect = Exception("connection refused")
        gw = _make_gateway()
        result = gw.send("hi")
        assert "sorry" in result.lower() or "couldn't" in result.lower()

    @patch("hey_clever.adapters.clawdbot_gateway.requests.post")
    def test_send_with_context(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"choices": [{"message": {"content": "context reply"}}]}
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        gw = _make_gateway()
        ctx = [{"role": "system", "content": "You are helpful."}]
        result = gw.send("hi", context=ctx)
        assert result == "context reply"

        payload = mock_post.call_args[1]["json"]
        assert len(payload["messages"]) == 2
        assert payload["messages"][0]["role"] == "system"
