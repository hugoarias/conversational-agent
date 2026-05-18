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


def test_transcribe_with_language_param(mock_whisper_model):
    """language parameter should be forwarded to model.transcribe()."""
    segment = MagicMock()
    segment.text = " Hola mundo "
    info = MagicMock()
    info.language = "es"
    mock_whisper_model.transcribe.return_value = ([segment], info)

    svc = WhisperSTTService(language="es")
    text, language = svc.transcribe(make_silence_bytes())

    assert text == "Hola mundo"
    assert language == "es"
    _, call_kwargs = mock_whisper_model.transcribe.call_args
    assert call_kwargs.get("language") == "es"


def test_transcribe_cuda_fallback_on_lazy_dll_error():
    """CUDA DLL error on first transcribe() should fall back to CPU and retry."""
    with patch("app.services.whisper_stt.WhisperModel") as mock_cls:
        cpu_instance = MagicMock()
        segment = MagicMock()
        segment.text = "fallback text"
        info = MagicMock()
        info.language = "en"
        cpu_instance.transcribe.return_value = ([segment], info)

        cuda_instance = MagicMock()
        cuda_instance.transcribe.side_effect = OSError("cublas64_12.dll not found")

        mock_cls.side_effect = [cuda_instance, cpu_instance]

        svc = WhisperSTTService(device="cuda")
        text, language = svc.transcribe(make_silence_bytes())

    assert text == "fallback text"
    assert language == "en"
    assert svc._model is cpu_instance


def test_init_cuda_fallback():
    """CUDA error during model loading should fall back to CPU."""
    with patch("app.services.whisper_stt.WhisperModel") as mock_cls:
        cpu_instance = MagicMock()
        mock_cls.side_effect = [
            OSError("cannot load cublas64_12.dll"),
            cpu_instance,
        ]

        svc = WhisperSTTService(device="cuda")

    assert svc._model is cpu_instance
    assert mock_cls.call_count == 2
    second_call = mock_cls.call_args_list[1]
    assert second_call[1]["device"] == "cpu"


def test_init_non_cuda_error_is_reraised():
    """Non-CUDA errors during model loading should propagate."""
    with patch("app.services.whisper_stt.WhisperModel") as mock_cls:
        mock_cls.side_effect = RuntimeError("model file not found")

        with pytest.raises(RuntimeError, match="model file not found"):
            WhisperSTTService()


def test_register_nvidia_dll_dirs_non_windows():
    """On non-Windows platforms the function should be a safe no-op."""
    import sys
    with patch.object(sys, "platform", "linux"):
        from app.services.whisper_stt import _register_nvidia_dll_dirs
        _register_nvidia_dll_dirs()
