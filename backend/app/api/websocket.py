"""WebSocket endpoint for real-time audio conversation."""
import logging
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from ..core.agent import ConversationAgent
from ..core.factory import ServiceFactory, LLMProvider
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter()
_factory = ServiceFactory(settings)


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    provider: Optional[LLMProvider] = Query(default=None, description="LLM provider: 'ollama' or 'bedrock'"),
    model: Optional[str] = Query(default=None, description="Model identifier override"),
) -> None:
    """
    Handle a single WebSocket session.

    Query params:
    - provider: 'ollama' (default) or 'bedrock'
    - model:    model name/ID override (e.g. 'llama3' or 'anthropic.claude-3-haiku-...')

    Protocol:
    - Client sends: raw audio bytes (PCM int16 WAV)
    - Server sends: JSON metadata (AgentResponse), then audio bytes
    """
    await websocket.accept()
    logger.info("WebSocket accepted (provider=%s, model=%s).", provider, model)

    agent = ConversationAgent(
        stt_service=_factory.create_stt_service(),
        llm_service=_factory.create_llm_service(provider=provider, model=model),
        tts_service=_factory.create_tts_service(),
    )

    try:
        while True:
            audio_bytes = await websocket.receive_bytes()
            logger.debug("Received %d audio bytes.", len(audio_bytes))

            response_meta, audio_out = agent.process_audio(audio_bytes)

            await websocket.send_json(response_meta.model_dump())

            if response_meta.audio_available and audio_out:
                await websocket.send_bytes(audio_out)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected.")
    except Exception:
        logger.exception("Unexpected error in WebSocket handler.")
        await websocket.close(code=1011)
