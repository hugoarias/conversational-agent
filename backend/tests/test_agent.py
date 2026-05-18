"""Unit tests for ConversationAgent."""
import pytest
from unittest.mock import MagicMock
from app.core.agent import ConversationAgent
from app.models.conversation import Role


def make_agent(transcript="Hello", language="en", reply="Hi there", audio=b"audio"):
    stt = MagicMock()
    stt.transcribe.return_value = (transcript, language)
    llm = MagicMock()
    llm.chat.return_value = reply
    tts = MagicMock()
    tts.synthesize.return_value = audio
    return ConversationAgent(stt_service=stt, llm_service=llm, tts_service=tts), stt, llm, tts


def test_process_audio_full_pipeline():
    agent, stt, llm, tts = make_agent()
    meta, audio = agent.process_audio(b"raw_audio")

    stt.transcribe.assert_called_once_with(b"raw_audio")
    llm.chat.assert_called_once()
    tts.synthesize.assert_called_once_with("Hi there", "en")
    assert meta.transcript == "Hello"
    assert meta.response == "Hi there"
    assert audio == b"audio"
    assert meta.error is None


def test_process_audio_empty_transcript():
    agent, stt, llm, tts = make_agent(transcript="")
    meta, audio = agent.process_audio(b"silence")

    llm.chat.assert_not_called()
    tts.synthesize.assert_not_called()
    assert meta.audio_available is False


def test_process_audio_stores_history():
    agent, _, _, _ = make_agent(transcript="What time is it?", reply="It's noon.")
    agent.process_audio(b"audio1")

    roles = [m.role for m in agent.history.messages]
    assert Role.SYSTEM in roles
    assert Role.USER in roles
    assert Role.ASSISTANT in roles


def test_reset_clears_history():
    agent, _, _, _ = make_agent()
    agent.process_audio(b"audio1")
    agent.reset()

    assert len(agent.history.messages) == 1
    assert agent.history.messages[0].role == Role.SYSTEM


def test_process_audio_handles_exception():
    stt = MagicMock()
    stt.transcribe.side_effect = RuntimeError("STT failure")
    llm = MagicMock()
    tts = MagicMock()

    agent = ConversationAgent(stt_service=stt, llm_service=llm, tts_service=tts)
    meta, audio = agent.process_audio(b"bad_audio")

    assert meta.error == "STT failure"
    assert audio == b""


def test_non_english_language_injected_into_system_prompt():
    agent, _, llm, _ = make_agent(transcript="Hola", language="es")
    agent.process_audio(b"audio")

    messages = llm.chat.call_args[0][0]
    system_content = messages[0]["content"]
    assert "es" in system_content
    assert "CRITICAL" in system_content
