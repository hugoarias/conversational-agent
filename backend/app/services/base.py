"""Abstract base classes for all AI services (Strategy Pattern)."""
from abc import ABC, abstractmethod


class STTService(ABC):
    """Abstract speech-to-text service."""

    @abstractmethod
    def transcribe(self, audio_bytes: bytes) -> tuple[str, str | None]:
        """
        Transcribe raw audio bytes to text.

        Returns:
            A tuple of (transcript_text, detected_language_code).
            language_code follows BCP-47 (e.g. 'en', 'es', 'fr').
            May be None if the implementation does not detect language.
        """


class LLMService(ABC):
    """Abstract large language model service."""

    @abstractmethod
    def chat(self, messages: list[dict]) -> str:
        """Send a list of messages and return the assistant's text reply."""


class TTSService(ABC):
    """Abstract text-to-speech service."""

    @abstractmethod
    def synthesize(self, text: str, language: str | None = None) -> bytes:
        """
        Synthesize text to speech and return WAV audio bytes.

        Args:
            text:     The text to speak.
            language: BCP-47 language code hint (e.g. 'es', 'fr').
                      Implementations may use this to select an appropriate voice.
                      None means use the default voice.
        """
