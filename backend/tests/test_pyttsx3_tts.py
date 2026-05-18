"""Unit tests for Pyttsx3TTSService."""
import os
import wave
import pytest
from unittest.mock import MagicMock, patch, call
from app.services.pyttsx3_tts import Pyttsx3TTSService, _find_voice_for_language


def make_minimal_wav() -> bytes:
    """Create a minimal valid WAV file in memory."""
    import io
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(22050)
        wf.writeframes(b"\x00\x00" * 100)
    return buf.getvalue()


def _make_mock_engine(voices=None):
    engine = MagicMock()
    engine.getProperty.side_effect = lambda prop: voices if prop == "voices" else None
    return engine


@patch("app.services.pyttsx3_tts.pyttsx3.init")
@patch("app.services.pyttsx3_tts.os.unlink")
@patch("builtins.open", create=True)
@patch("app.services.pyttsx3_tts.tempfile.NamedTemporaryFile")
def test_synthesize_returns_bytes(mock_tmpfile, mock_open, mock_unlink, mock_init):
    wav_bytes = make_minimal_wav()
    mock_tmpfile.return_value.__enter__.return_value.name = "fake.wav"
    mock_open.return_value.__enter__.return_value.read.return_value = wav_bytes

    mock_engine = MagicMock()
    mock_engine.getProperty.return_value = []  # no voices
    mock_init.return_value = mock_engine

    svc = Pyttsx3TTSService()
    result = svc.synthesize("Hello")

    assert result == wav_bytes
    mock_engine.save_to_file.assert_called_once_with("Hello", "fake.wav")
    mock_engine.runAndWait.assert_called_once()


def test_find_voice_matches_windows_sapi5_locale():
    voice_es = MagicMock()
    voice_es.id = r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_ES-ES_HELENA_11_0"
    voice_es.languages = []
    voice_en = MagicMock()
    voice_en.id = r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_ZIRA_11_0"
    voice_en.languages = []

    engine = _make_mock_engine(voices=[voice_en, voice_es])
    result = _find_voice_for_language(engine, "es")
    assert result == voice_es.id


def test_find_voice_returns_none_when_no_match():
    voice_en = MagicMock()
    voice_en.id = r"HKEY_LOCAL_MACHINE\...\TTS_MS_EN-US_ZIRA_11_0"
    voice_en.languages = []

    engine = _make_mock_engine(voices=[voice_en])
    result = _find_voice_for_language(engine, "fr")
    assert result is None


@patch("app.services.pyttsx3_tts.pyttsx3.init")
@patch("app.services.pyttsx3_tts.os.unlink")
@patch("builtins.open", create=True)
@patch("app.services.pyttsx3_tts.tempfile.NamedTemporaryFile")
def test_synthesize_sets_voice_for_language(mock_tmpfile, mock_open, mock_unlink, mock_init):
    wav_bytes = make_minimal_wav()
    mock_tmpfile.return_value.__enter__.return_value.name = "fake.wav"
    mock_open.return_value.__enter__.return_value.read.return_value = wav_bytes

    voice_es = MagicMock()
    voice_es.id = r"HKEY_LOCAL_MACHINE\...\TTS_MS_ES-ES_HELENA_11_0"
    voice_es.languages = []

    mock_engine = MagicMock()
    mock_engine.getProperty.side_effect = lambda p: [voice_es] if p == "voices" else None
    mock_init.return_value = mock_engine

    svc = Pyttsx3TTSService()
    svc.synthesize("Hola mundo", language="es")

    set_calls = [c for c in mock_engine.setProperty.call_args_list if c[0][0] == "voice"]
    assert len(set_calls) == 1
    assert set_calls[0][0][1] == voice_es.id


def test_find_voice_matches_macos_bytes_language():
    """macOS voices expose language as bytes in the `languages` list."""
    voice_fr = MagicMock()
    voice_fr.id = "com.apple.speech.synthesis.voice.thomas"
    voice_fr.languages = [b"fr_FR"]

    engine = _make_mock_engine(voices=[voice_fr])
    result = _find_voice_for_language(engine, "fr")
    assert result == voice_fr.id


def test_find_voice_matches_macos_str_language():
    """macOS voices may also expose language as a plain string."""
    voice_de = MagicMock()
    voice_de.id = "com.apple.speech.synthesis.voice.anna"
    voice_de.languages = ["de_DE"]

    engine = _make_mock_engine(voices=[voice_de])
    result = _find_voice_for_language(engine, "de")
    assert result == voice_de.id


@patch("app.services.pyttsx3_tts.pyttsx3.init")
@patch("app.services.pyttsx3_tts.os.unlink")
@patch("builtins.open", create=True)
@patch("app.services.pyttsx3_tts.tempfile.NamedTemporaryFile")
def test_synthesize_no_match_uses_default_voice(mock_tmpfile, mock_open, mock_unlink, mock_init):
    """When no voice matches the language, default voice is used (no setProperty('voice'))."""
    wav_bytes = make_minimal_wav()
    mock_tmpfile.return_value.__enter__.return_value.name = "fake.wav"
    mock_open.return_value.__enter__.return_value.read.return_value = wav_bytes

    voice_en = MagicMock()
    voice_en.id = r"HKEY_LOCAL_MACHINE\...\TTS_MS_EN-US_ZIRA_11_0"
    voice_en.languages = []

    mock_engine = MagicMock()
    mock_engine.getProperty.side_effect = lambda p: [voice_en] if p == "voices" else None
    mock_init.return_value = mock_engine

    svc = Pyttsx3TTSService()
    svc.synthesize("Bonjour le monde", language="fr")

    set_voice_calls = [c for c in mock_engine.setProperty.call_args_list if c[0][0] == "voice"]
    assert len(set_voice_calls) == 0
