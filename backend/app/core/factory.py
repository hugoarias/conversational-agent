"""Factory for creating AI service instances from application config."""
import logging
from typing import Literal, Optional
from ..config import Settings
from ..services.base import STTService, LLMService, TTSService
from ..services.whisper_stt import WhisperSTTService
from ..services.ollama_llm import OllamaLLMService
from ..services.bedrock_llm import BedrockLLMService
from ..services.pyttsx3_tts import Pyttsx3TTSService

logger = logging.getLogger(__name__)

LLMProvider = Literal["ollama", "bedrock"]


class ServiceFactory:
    """Creates concrete service implementations based on application settings."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def create_stt_service(self) -> STTService:
        """Create and return the configured STT service."""
        logger.info("Creating WhisperSTTService.")
        return WhisperSTTService(
            model_size=self._settings.whisper_model_size,
            device=self._settings.whisper_device,
            compute_type=self._settings.whisper_compute_type,
            language=self._settings.whisper_language,
        )

    def create_llm_service(
        self,
        provider: Optional[LLMProvider] = None,
        model: Optional[str] = None,
    ) -> LLMService:
        """
        Create and return an LLM service.

        Args:
            provider: Override the provider ('ollama' or 'bedrock').
                      Defaults to 'ollama' when not specified.
            model:    Override the model identifier.
                      Defaults to the configured default for the chosen provider.
        """
        resolved_provider: LLMProvider = provider or "ollama"

        if resolved_provider == "bedrock":
            resolved_model = model or self._settings.bedrock_default_model
            logger.info("Creating BedrockLLMService (model=%s).", resolved_model)
            return BedrockLLMService(
                model_id=resolved_model,
                region=self._settings.aws_region,
                aws_profile=self._settings.aws_profile,
            )

        resolved_model = model or self._settings.ollama_model
        logger.info("Creating OllamaLLMService (model=%s).", resolved_model)
        return OllamaLLMService(
            model=resolved_model,
            base_url=self._settings.ollama_base_url,
        )

    def create_tts_service(self) -> TTSService:
        """Create and return the configured TTS service."""
        logger.info("Creating Pyttsx3TTSService.")
        return Pyttsx3TTSService(
            rate=self._settings.tts_rate,
            volume=self._settings.tts_volume,
        )
