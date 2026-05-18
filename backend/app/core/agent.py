"""ConversationAgent — facade that orchestrates STT → LLM → TTS."""
import logging
from dataclasses import dataclass, field
from ..models.conversation import AgentResponse, ConversationHistory, Role
from ..services.base import LLMService, STTService, TTSService

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a helpful, concise voice assistant. "
    "Keep responses short and conversational — ideally 1-3 sentences. "
    "Avoid markdown, bullet points, or long lists."
)

_LANGUAGE_INSTRUCTION = (
    " CRITICAL: The user is speaking {language}. "
    "You MUST reply in {language} only. Do NOT use English or any other language."
)


@dataclass
class ConversationAgent:
    """
    Facade that wires together STT, LLM, and TTS services.

    Each instance maintains its own conversation history, making it
    suitable for a single user/WebSocket session.
    """
    stt_service: STTService
    llm_service: LLMService
    tts_service: TTSService
    history: ConversationHistory = field(default_factory=ConversationHistory)
    _detected_language: str | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self.history.add(Role.SYSTEM, SYSTEM_PROMPT)

    def process_audio(self, audio_bytes: bytes) -> tuple[AgentResponse, bytes]:
        """
        Full pipeline: audio bytes → transcript → LLM reply → TTS audio.

        Returns:
            A tuple of (AgentResponse metadata, WAV audio bytes).
        """
        try:
            transcript, language = self.stt_service.transcribe(audio_bytes)
            if language:
                self._detected_language = language
            logger.info("Transcript: %s (language=%s)", transcript, language)

            if not transcript:
                return AgentResponse(
                    transcript="",
                    response="I didn't catch that. Could you repeat?",
                    audio_available=False,
                ), b""

            self.history.add(Role.USER, transcript)
            messages = self._build_messages()
            reply = self.llm_service.chat(messages)
            self.history.add(Role.ASSISTANT, reply)
            logger.info("Reply: %s", reply)

            audio_bytes_out = self.tts_service.synthesize(reply, self._detected_language)
            return AgentResponse(transcript=transcript, response=reply), audio_bytes_out

        except Exception as exc:
            logger.exception("Error in ConversationAgent.process_audio")
            return AgentResponse(
                transcript="",
                response="",
                audio_available=False,
                error=str(exc),
            ), b""

    def _build_messages(self) -> list[dict]:
        """
        Return the message list for the LLM, injecting a language instruction
        into the system prompt when a non-English language has been detected.
        """
        messages = self.history.to_ollama_format()
        if self._detected_language and self._detected_language != "en":
            lang_note = _LANGUAGE_INSTRUCTION.format(language=self._detected_language)
            # Amend the system message in this call only (not stored in history).
            messages[0] = {**messages[0], "content": messages[0]["content"] + lang_note}
        return messages

    def reset(self) -> None:
        """Clear conversation history and re-inject system prompt."""
        self.history.clear()
        self.history.add(Role.SYSTEM, SYSTEM_PROMPT)
        self._detected_language = None
