"""Unit tests for application configuration (Settings validators)."""
import pytest
from pydantic import ValidationError


def _make_settings(**overrides):
    """Create a Settings instance with env overrides, bypassing .env file."""
    from app.config import Settings
    return Settings(_env_file=None, **overrides)


def test_default_device_is_cpu():
    s = _make_settings()
    assert s.whisper_device == "cpu"


def test_gpu_alias_maps_to_cuda():
    s = _make_settings(whisper_device="gpu")
    assert s.whisper_device == "cuda"


def test_cuda_accepted():
    s = _make_settings(whisper_device="cuda")
    assert s.whisper_device == "cuda"


def test_auto_accepted():
    s = _make_settings(whisper_device="auto")
    assert s.whisper_device == "auto"


def test_invalid_device_raises():
    with pytest.raises((ValidationError, ValueError)):
        _make_settings(whisper_device="tpu")


def test_cuda_device_upgrades_compute_type_to_float16():
    s = _make_settings(whisper_device="cuda")
    assert s.whisper_compute_type == "float16"


def test_cuda_with_explicit_int8_is_upgraded():
    s = _make_settings(whisper_device="cuda", whisper_compute_type="int8")
    assert s.whisper_compute_type == "float16"


def test_cpu_retains_int8_compute_type():
    s = _make_settings(whisper_device="cpu")
    assert s.whisper_compute_type == "int8"


def test_cuda_with_explicit_float16_stays_float16():
    s = _make_settings(whisper_device="cuda", whisper_compute_type="float16")
    assert s.whisper_compute_type == "float16"


def test_default_ollama_model():
    s = _make_settings()
    assert s.ollama_model == "llama3"


def test_default_tts_rate():
    s = _make_settings()
    assert s.tts_rate == 180


def test_whisper_language_default_is_none():
    s = _make_settings()
    assert s.whisper_language is None


def test_whisper_language_can_be_set():
    s = _make_settings(whisper_language="es")
    assert s.whisper_language == "es"


def test_gpu_alias_case_insensitive():
    s = _make_settings(whisper_device="GPU")
    assert s.whisper_device == "cuda"
