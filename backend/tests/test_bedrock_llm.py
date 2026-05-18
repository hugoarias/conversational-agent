"""Unit tests for BedrockLLMService."""
import pytest
from unittest.mock import MagicMock, patch
from app.services.bedrock_llm import BedrockLLMService


@pytest.fixture
def mock_boto_session():
    """Patch boto3.Session so no real AWS calls are made."""
    with patch("app.services.bedrock_llm.boto3.Session") as mock_session_cls:
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session_cls.return_value = mock_session
        yield mock_client


def make_bedrock_response(text: str) -> dict:
    return {"output": {"message": {"content": [{"text": text}]}}}


# ── _convert_messages ──────────────────────────────────────────────────────

def test_convert_messages_separates_system():
    messages = [
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "Hello"},
    ]
    system_parts, conversation = BedrockLLMService._convert_messages(messages)
    assert system_parts == [{"text": "You are helpful."}]
    assert conversation == [{"role": "user", "content": [{"text": "Hello"}]}]


def test_convert_messages_multi_turn():
    messages = [
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hello!"},
        {"role": "user", "content": "How are you?"},
    ]
    _, conversation = BedrockLLMService._convert_messages(messages)
    assert len(conversation) == 3
    assert conversation[1]["role"] == "assistant"
    assert conversation[1]["content"] == [{"text": "Hello!"}]


def test_convert_messages_no_system():
    messages = [{"role": "user", "content": "Test"}]
    system_parts, conversation = BedrockLLMService._convert_messages(messages)
    assert system_parts == []
    assert len(conversation) == 1


# ── chat ───────────────────────────────────────────────────────────────────

def test_chat_returns_reply(mock_boto_session):
    mock_boto_session.converse.return_value = make_bedrock_response("  Hello there!  ")

    svc = BedrockLLMService(model_id="anthropic.claude-3-haiku-20240307-v1:0")
    result = svc.chat([{"role": "user", "content": "Hi"}])

    assert result == "Hello there!"


def test_chat_passes_model_id(mock_boto_session):
    mock_boto_session.converse.return_value = make_bedrock_response("reply")
    model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"

    svc = BedrockLLMService(model_id=model_id)
    svc.chat([{"role": "user", "content": "test"}])

    call_kwargs = mock_boto_session.converse.call_args.kwargs
    assert call_kwargs["modelId"] == model_id


def test_chat_includes_system(mock_boto_session):
    mock_boto_session.converse.return_value = make_bedrock_response("ok")

    svc = BedrockLLMService(model_id="amazon.titan-text-express-v1")
    svc.chat([
        {"role": "system", "content": "Be concise."},
        {"role": "user", "content": "Hello"},
    ])

    call_kwargs = mock_boto_session.converse.call_args.kwargs
    assert call_kwargs["system"] == [{"text": "Be concise."}]


def test_chat_no_system_omits_key(mock_boto_session):
    mock_boto_session.converse.return_value = make_bedrock_response("ok")

    svc = BedrockLLMService(model_id="amazon.titan-text-express-v1")
    svc.chat([{"role": "user", "content": "Hello"}])

    call_kwargs = mock_boto_session.converse.call_args.kwargs
    assert "system" not in call_kwargs
