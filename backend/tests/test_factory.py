"""Unit tests for ServiceFactory."""
import pytest
from unittest.mock import MagicMock, patch
from app.core.factory import ServiceFactory
from app.services.ollama_llm import OllamaLLMService
from app.services.bedrock_llm import BedrockLLMService


def _make_settings(**overrides):
    from app.config import Settings
    return Settings(_env_file=None, **overrides)


@patch("app.core.factory.WhisperSTTService")
@patch("app.core.factory.Pyttsx3TTSService")
@patch("app.core.factory.OllamaLLMService")
def test_create_stt_service(mock_ollama, mock_tts, mock_stt):
    settings = _make_settings()
    factory = ServiceFactory(settings)
    svc = factory.create_stt_service()

    mock_stt.assert_called_once_with(
        model_size=settings.whisper_model_size,
        device=settings.whisper_device,
        compute_type=settings.whisper_compute_type,
        language=settings.whisper_language,
    )
    assert svc is mock_stt.return_value


@patch("app.core.factory.WhisperSTTService")
@patch("app.core.factory.Pyttsx3TTSService")
@patch("app.core.factory.OllamaLLMService")
def test_create_tts_service(mock_ollama, mock_tts, mock_stt):
    settings = _make_settings()
    factory = ServiceFactory(settings)
    svc = factory.create_tts_service()

    mock_tts.assert_called_once_with(
        rate=settings.tts_rate,
        volume=settings.tts_volume,
    )
    assert svc is mock_tts.return_value


@patch("app.core.factory.WhisperSTTService")
@patch("app.core.factory.Pyttsx3TTSService")
@patch("app.core.factory.OllamaLLMService")
def test_create_llm_service_defaults_to_ollama(mock_ollama, mock_tts, mock_stt):
    settings = _make_settings()
    factory = ServiceFactory(settings)
    svc = factory.create_llm_service()

    mock_ollama.assert_called_once_with(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
    )
    assert svc is mock_ollama.return_value


@patch("app.core.factory.WhisperSTTService")
@patch("app.core.factory.Pyttsx3TTSService")
@patch("app.core.factory.OllamaLLMService")
def test_create_llm_service_explicit_ollama(mock_ollama, mock_tts, mock_stt):
    settings = _make_settings()
    factory = ServiceFactory(settings)
    svc = factory.create_llm_service(provider="ollama", model="mistral")

    mock_ollama.assert_called_once_with(
        model="mistral",
        base_url=settings.ollama_base_url,
    )
    assert svc is mock_ollama.return_value


@patch("app.core.factory.BedrockLLMService")
@patch("app.core.factory.WhisperSTTService")
@patch("app.core.factory.Pyttsx3TTSService")
@patch("app.core.factory.OllamaLLMService")
def test_create_llm_service_bedrock(mock_ollama, mock_tts, mock_stt, mock_bedrock):
    settings = _make_settings(aws_region="us-west-2")
    factory = ServiceFactory(settings)
    svc = factory.create_llm_service(provider="bedrock")

    mock_bedrock.assert_called_once_with(
        model_id=settings.bedrock_default_model,
        region=settings.aws_region,
        aws_profile=settings.aws_profile,
    )
    assert svc is mock_bedrock.return_value
    mock_ollama.assert_not_called()


@patch("app.core.factory.BedrockLLMService")
@patch("app.core.factory.WhisperSTTService")
@patch("app.core.factory.Pyttsx3TTSService")
@patch("app.core.factory.OllamaLLMService")
def test_create_llm_service_bedrock_with_model_override(mock_ollama, mock_tts, mock_stt, mock_bedrock):
    settings = _make_settings()
    factory = ServiceFactory(settings)
    custom_model = "amazon.titan-text-express-v1"
    svc = factory.create_llm_service(provider="bedrock", model=custom_model)

    mock_bedrock.assert_called_once_with(
        model_id=custom_model,
        region=settings.aws_region,
        aws_profile=settings.aws_profile,
    )
    assert svc is mock_bedrock.return_value
