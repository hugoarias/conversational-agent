"""Application configuration using Pydantic Settings."""
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, model_validator


_VALID_DEVICES = {"cpu", "cuda", "auto"}
# "gpu" is a common alias users try; map it to the correct faster-whisper value.
_DEVICE_ALIASES = {"gpu": "cuda"}

_GPU_COMPUTE_DEFAULT = "float16"
_CPU_COMPUTE_DEFAULT = "int8"


class Settings(BaseSettings):
    """Central configuration loaded from environment variables or .env file."""

    # LLM — Local (Ollama)
    ollama_model: str = Field(default="llama3", description="Ollama model name")
    ollama_base_url: str = Field(default="http://localhost:11434", description="Ollama base URL")

    # LLM — AWS Bedrock
    aws_profile: Optional[str] = Field(default=None, description="AWS named profile (~/.aws/credentials)")
    aws_region: str = Field(default="us-east-1", description="AWS region for Bedrock")
    bedrock_default_model: str = Field(
        default="anthropic.claude-3-haiku-20240307-v1:0",
        description="Default Bedrock model ID when none is specified per-session",
    )

    # STT
    whisper_model_size: str = Field(default="base", description="Whisper model size: tiny, base, small, medium, large")
    whisper_device: str = Field(default="cpu", description="Device: cpu | cuda | auto  ('gpu' is accepted as an alias for 'cuda')")
    whisper_compute_type: str = Field(default=_CPU_COMPUTE_DEFAULT, description="Compute type: int8 (CPU) | float16 (GPU/CUDA)")
    whisper_language: Optional[str] = Field(
        default=None,
        description="Whisper transcription language (e.g. 'en', 'es', 'fr'). None = auto-detect per utterance.",
    )

    # TTS
    tts_rate: int = Field(default=180, description="TTS speech rate (words per minute)")
    tts_volume: float = Field(default=1.0, description="TTS volume (0.0 to 1.0)")

    # Server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    cors_origins: list[str] = Field(default=["http://localhost:5173", "http://localhost:4173"])

    @field_validator("whisper_device", mode="before")
    @classmethod
    def normalise_device(cls, v: str) -> str:
        """Map 'gpu' → 'cuda'; validate against faster-whisper supported values."""
        normalised = _DEVICE_ALIASES.get(v.lower(), v.lower())
        if normalised not in _VALID_DEVICES:
            raise ValueError(
                f"Unsupported WHISPER_DEVICE '{v}'. "
                f"Valid values: {', '.join(sorted(_VALID_DEVICES))} (or 'gpu' as an alias for 'cuda')."
            )
        return normalised

    @model_validator(mode="after")
    def auto_compute_type_for_gpu(self) -> "Settings":
        """When using CUDA and compute_type is still the CPU default, upgrade to float16."""
        if self.whisper_device == "cuda" and self.whisper_compute_type == _CPU_COMPUTE_DEFAULT:
            object.__setattr__(self, "whisper_compute_type", _GPU_COMPUTE_DEFAULT)
        return self

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
