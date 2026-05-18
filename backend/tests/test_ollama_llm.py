"""Unit tests for OllamaLLMService."""
import pytest
from unittest.mock import MagicMock, patch
from app.services.ollama_llm import OllamaLLMService


@pytest.fixture
def mock_ollama_client():
    with patch("app.services.ollama_llm.ollama.Client") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        yield mock_client


def test_chat_returns_reply(mock_ollama_client):
    mock_message = MagicMock()
    mock_message.content = "  Hello, how can I help?  "
    mock_ollama_client.chat.return_value = MagicMock(message=mock_message)

    svc = OllamaLLMService()
    result = svc.chat([{"role": "user", "content": "Hi"}])

    assert result == "Hello, how can I help?"


def test_chat_passes_messages(mock_ollama_client):
    mock_message = MagicMock()
    mock_message.content = "reply"
    mock_ollama_client.chat.return_value = MagicMock(message=mock_message)

    messages = [{"role": "user", "content": "test"}]
    svc = OllamaLLMService(model="llama3")
    svc.chat(messages)

    mock_ollama_client.chat.assert_called_once_with(model="llama3", messages=messages)
