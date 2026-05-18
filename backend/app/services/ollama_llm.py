"""Ollama implementation of LLMService."""
import logging
import ollama
from .base import LLMService

logger = logging.getLogger(__name__)


class OllamaLLMService(LLMService):
    """Sends messages to a locally running Ollama model."""

    def __init__(self, model: str = "llama3", base_url: str = "http://localhost:11434") -> None:
        self._model = model
        self._client = ollama.Client(host=base_url)
        logger.info("OllamaLLMService initialized with model '%s'.", model)

    def chat(self, messages: list[dict]) -> str:
        """Send messages to Ollama and return the assistant's reply text."""
        response = self._client.chat(model=self._model, messages=messages)
        reply = response.message.content.strip()
        logger.debug("LLM reply: %s", reply)
        return reply
