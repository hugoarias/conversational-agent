"""REST endpoint for listing available LLM models (Ollama + AWS Bedrock)."""
import logging
from typing import Literal
from fastapi import APIRouter
from pydantic import BaseModel
import ollama
import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


class ModelInfo(BaseModel):
    """Metadata for a single available model."""
    id: str
    name: str
    provider: Literal["ollama", "bedrock"]


class ModelsResponse(BaseModel):
    models: list[ModelInfo]


@router.get("/api/models", response_model=ModelsResponse)
async def list_models() -> ModelsResponse:
    """
    Return all available LLM models from local Ollama and AWS Bedrock.

    Both sources are queried independently; failures are logged and
    result in an empty list for that provider — the endpoint never fails.
    """
    models: list[ModelInfo] = []
    models.extend(_fetch_ollama_models())
    models.extend(_fetch_bedrock_models())
    return ModelsResponse(models=models)


def _fetch_ollama_models() -> list[ModelInfo]:
    """Query the local Ollama daemon for installed models."""
    try:
        client = ollama.Client(host=settings.ollama_base_url)
        response = client.list()
        return [
            ModelInfo(
                id=m.model,
                name=m.model,
                provider="ollama",
            )
            for m in response.models
        ]
    except Exception as exc:
        logger.warning("Could not fetch Ollama models: %s", exc)
        return []


def _fetch_bedrock_models() -> list[ModelInfo]:
    """Query AWS Bedrock for available on-demand foundation models."""
    try:
        session = boto3.Session(
            profile_name=settings.aws_profile,
            region_name=settings.aws_region,
        )
        client = session.client("bedrock")
        paginator = client.get_paginator("list_foundation_models")
        models: list[ModelInfo] = []
        for page in paginator.paginate(byInferenceType="ON_DEMAND"):
            for m in page.get("modelSummaries", []):
                # Only include text-output models that support the Converse API
                output_types = m.get("outputModalities", [])
                if "TEXT" not in output_types:
                    continue
                model_id = m["modelId"]
                model_name = m.get("modelName", model_id)
                provider_name = m.get("providerName", "")
                display = f"{model_name} ({provider_name})" if provider_name else model_name
                models.append(ModelInfo(id=model_id, name=display, provider="bedrock"))
        return models
    except NoCredentialsError:
        logger.warning("AWS credentials not configured — Bedrock models unavailable.")
        return []
    except (BotoCoreError, ClientError) as exc:
        logger.warning("Could not fetch Bedrock models: %s", exc)
        return []
    except Exception as exc:
        logger.warning("Unexpected error fetching Bedrock models: %s", exc)
        return []
