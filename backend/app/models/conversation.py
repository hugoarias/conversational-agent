"""Pydantic models for conversation data structures."""
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class Role(str, Enum):
    """Role of a message participant."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """A single conversation message."""
    role: Role
    content: str


class ConversationHistory(BaseModel):
    """Ordered list of messages forming a conversation."""
    messages: list[Message] = Field(default_factory=list)

    def add(self, role: Role, content: str) -> None:
        """Append a new message to the history."""
        self.messages.append(Message(role=role, content=content))

    def to_ollama_format(self) -> list[dict]:
        """Convert to the format expected by the Ollama SDK."""
        return [{"role": m.role.value, "content": m.content} for m in self.messages]

    def clear(self) -> None:
        """Reset the conversation history."""
        self.messages.clear()


class AgentResponse(BaseModel):
    """Response payload sent back to the frontend over WebSocket."""
    transcript: str = Field(description="STT transcript of the user's speech")
    response: str = Field(description="LLM text response")
    audio_available: bool = Field(default=True, description="Whether audio bytes follow")
    error: Optional[str] = Field(default=None, description="Error message if something failed")
