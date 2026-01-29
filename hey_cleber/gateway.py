"""Clawdbot gateway client."""

from __future__ import annotations

import logging

import requests

from .config import AppConfig

log = logging.getLogger("hey-cleber.gateway")


def send_to_clawdbot(message: str, config: AppConfig) -> str:
    """Send a message to Clawdbot via the OpenAI-compatible endpoint.

    Args:
        message: The user's transcribed speech.
        config: Application configuration.

    Returns:
        The assistant's response text.
    """
    url = f"{config.gateway_url}/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.gateway_token}",
        "x-clawdbot-agent-id": "main",
    }
    payload = {
        "model": "clawdbot:main",
        "user": "voice-cleber",
        "messages": [
            {
                "role": "user",
                "content": (
                    "[Voice input from microphone — respond concisely for TTS playback. "
                    "Match the user's language (English or Portuguese).]\n\n"
                    + message
                ),
            },
        ],
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        log.error("Gateway request failed: %s", e)
        return "Sorry, I couldn't process that request."
