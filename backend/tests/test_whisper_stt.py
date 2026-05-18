"""Unit tests for WhisperSTTService."""
import numpy as np
import pytest
from unittest.mock import MagicMock, patch
from app.services.whisper_stt import WhisperSTTService


@pytest.fixture
def mock_whisper_model():
    with patch("app.services.whisper_stt.WhisperModel") as mock_cls:
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        yield mock_instance


def make_silence_bytes(num_samples: int = 16000) -> bytes:
    return (np.zeros(num_samples, dtype=np.int16)).tobytes()


def test_transcribe_returns_string(mock_whisper_model):
    segment = MagicMock()
    segment.text = " Hello world "
    info = MagicMock()
    info.language = "en"
    mock_whisper_model.transcribe.return_value = ([segment], info)

    svc = WhisperSTTService()
    text, language = svc.transcribe(make_silence_bytes())

    assert text == "Hello world"
    assert language == "en"


def test_transcribe_empty_segments(mock_whisper_model):
    info = MagicMock()
    info.language = "fr"
    mock_whisper_model.transcribe.return_value = ([], info)

    svc = WhisperSTTService()
    text, language = svc.transcribe(make_silence_bytes())

    assert text == ""
    assert language == "fr"


def test_bytes_to_float32_conversion():
    # int16 max value → float32 ~1.0
    samples = np.array([32767, -32768, 0], dtype=np.int16)
    result = WhisperSTTService._bytes_to_float32(samples.tobytes())
    assert abs(result[0] - 1.0) < 0.001
    assert abs(result[1] - (-1.0)) < 0.001
    assert result[2] == 0.0
