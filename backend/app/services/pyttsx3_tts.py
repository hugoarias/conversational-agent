"""pyttsx3 implementation of TTSService."""
import logging
import tempfile
import os
import pyttsx3
from .base import TTSService

logger = logging.getLogger(__name__)


def _find_voice_for_language(engine: pyttsx3.Engine, language: str) -> str | None:
    """
    Scan available pyttsx3 voices and return the ID of the first voice that
    matches the given BCP-47 language code (e.g. 'es', 'fr', 'de').

    Windows SAPI5 voice IDs look like:
        HKEY_LOCAL_MACHINE\\...\\TTS_MS_ES-ES_HELENA_11_0
    macOS voices expose a `languages` list with locale bytes.
    """
    lang_upper = language.upper()
    voices = engine.getProperty("voices")
    for voice in voices:
        vid = voice.id.upper()
        # Windows: locale appears as _ES-ES_ or _ES_ pattern in the registry path
        if f"_{lang_upper}-" in vid or f"_{lang_upper}_" in vid:
            return voice.id
        # macOS: check the languages attribute
        for lang_code in getattr(voice, "languages", []) or []:
            if isinstance(lang_code, bytes):
                lang_code = lang_code.decode("ascii", errors="ignore")
            if isinstance(lang_code, str) and lang_code.lower().startswith(language.lower()):
                return voice.id
    return None


class Pyttsx3TTSService(TTSService):
    """Synthesizes speech locally using pyttsx3 (Windows SAPI5)."""

    def __init__(self, rate: int = 180, volume: float = 1.0) -> None:
        self._rate = rate
        self._volume = volume
        logger.info("Pyttsx3TTSService initialized (rate=%d, volume=%.1f).", rate, volume)

    def synthesize(self, text: str, language: str | None = None) -> bytes:
        """Convert text to WAV audio bytes using pyttsx3.

        If `language` is provided, attempts to select a matching installed voice.
        Falls back to the system default voice if no match is found.
        """
        engine = pyttsx3.init()
        engine.setProperty("rate", self._rate)
        engine.setProperty("volume", self._volume)

        if language:
            voice_id = _find_voice_for_language(engine, language)
            if voice_id:
                engine.setProperty("voice", voice_id)
                logger.debug("TTS: selected voice %s for language '%s'.", voice_id, language)
            else:
                logger.warning(
                    "TTS: no installed voice found for language '%s'. "
                    "Using default voice. Install the voice pack via "
                    "Settings → Time & Language → Speech → Manage voices.",
                    language,
                )

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            engine.save_to_file(text, tmp_path)
            engine.runAndWait()
            engine.stop()

            with open(tmp_path, "rb") as f:
                audio_bytes = f.read()
        finally:
            os.unlink(tmp_path)

        logger.debug("TTS synthesized %d bytes for text: %s", len(audio_bytes), text[:50])
        return audio_bytes
