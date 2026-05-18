"""faster-whisper implementation of STTService."""
import logging
import os
import site
import sys
from pathlib import Path

import numpy as np
from faster_whisper import WhisperModel
from .base import STTService

logger = logging.getLogger(__name__)

_CUDA_ERROR_KEYWORDS = ("dll", "cuda", "cublas", "cudnn", "ctranslate2", "cannot be loaded", "not found")

_CUDA_FALLBACK_MSG = (
    "CUDA runtime libraries missing (%s). "
    "Falling back to CPU for this session. "
    "To enable GPU acceleration, run: pip install nvidia-cublas-cu12 nvidia-cudnn-cu12"
)


def _register_nvidia_dll_dirs() -> None:
    """
    On Windows, register the nvidia pip-package DLL directories so that
    ctranslate2 can locate cublas64_12.dll and cudnn*.dll at runtime.

    Linux handles this automatically via LD_LIBRARY_PATH; Windows does not,
    so we use os.add_dll_directory() to extend the Windows DLL search path.
    """
    if sys.platform != "win32":
        return
    for site_dir in site.getsitepackages():
        nvidia_root = Path(site_dir) / "nvidia"
        if not nvidia_root.is_dir():
            continue
        for pkg_dir in nvidia_root.iterdir():
            bin_dir = pkg_dir / "bin"
            if bin_dir.is_dir():
                try:
                    os.add_dll_directory(str(bin_dir))
                    logger.debug("Registered DLL directory: %s", bin_dir)
                except OSError:
                    pass


# Register once when the module is imported, before any WhisperModel is created.
_register_nvidia_dll_dirs()


class WhisperSTTService(STTService):
    """Transcribes audio using a local faster-whisper model."""

    def __init__(self, model_size: str = "base", device: str = "cpu", compute_type: str = "int8",
                 language: str | None = None) -> None:
        logger.info("Loading Whisper model '%s' on %s (language=%s)...", model_size, device, language or "auto")
        self._model_size = model_size
        self._language = language  # None → Whisper auto-detects per utterance
        try:
            self._model = WhisperModel(model_size, device=device, compute_type=compute_type)
        except Exception as exc:
            if device != "cpu" and self._is_cuda_error(exc):
                logger.warning(_CUDA_FALLBACK_MSG, exc)
                self._model = WhisperModel(model_size, device="cpu", compute_type="int8")
            else:
                raise
        logger.info("Whisper model loaded.")

    def transcribe(self, audio_bytes: bytes) -> tuple[str, str | None]:
        """Transcribe WAV audio bytes to text using Whisper.

        Returns:
            (transcript_text, detected_language_code) — language is None when Whisper
            cannot determine it (e.g. completely silent input).
        """
        audio_array = self._bytes_to_float32(audio_bytes)
        try:
            segments, info = self._model.transcribe(audio_array, language=self._language)
            transcript = " ".join(segment.text.strip() for segment in segments)
            detected_language: str | None = getattr(info, "language", None)
        except Exception as exc:
            if self._is_cuda_error(exc):
                # ctranslate2 loads CUDA DLLs lazily; the error may surface on the
                # first inference call rather than at model creation time.
                logger.warning(_CUDA_FALLBACK_MSG, exc)
                self._model = WhisperModel(self._model_size, device="cpu", compute_type="int8")
                segments, info = self._model.transcribe(audio_array, language=self._language)
                transcript = " ".join(segment.text.strip() for segment in segments)
                detected_language = getattr(info, "language", None)
            else:
                raise
        logger.debug("Transcript: %s (language=%s)", transcript, detected_language)
        return transcript.strip(), detected_language

    @staticmethod
    def _is_cuda_error(exc: Exception) -> bool:
        lower = str(exc).lower()
        return any(kw in lower for kw in _CUDA_ERROR_KEYWORDS)

    @staticmethod
    def _bytes_to_float32(audio_bytes: bytes) -> np.ndarray:
        """Convert raw PCM int16 bytes to float32 numpy array."""
        audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)
        return audio_int16.astype(np.float32) / 32768.0
