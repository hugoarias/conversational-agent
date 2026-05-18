"""Tests for GET /api/models endpoint and GET /health endpoint."""
import pytest
from unittest.mock import MagicMock, patch, call
from fastapi.testclient import TestClient
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError
from app.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# GET /api/models
# ---------------------------------------------------------------------------

def _make_ollama_model(name: str):
    m = MagicMock()
    m.model = name
    return m


@patch("app.api.models.ollama.Client")
@patch("app.api.models.boto3.Session")
def test_list_models_returns_ollama_and_bedrock(mock_session, mock_ollama_client):
    # Ollama mock
    mock_ollama_instance = MagicMock()
    mock_ollama_instance.list.return_value.models = [
        _make_ollama_model("llama3"),
        _make_ollama_model("mistral"),
    ]
    mock_ollama_client.return_value = mock_ollama_instance

    # Bedrock mock
    mock_bedrock_client = MagicMock()
    mock_paginator = MagicMock()
    mock_paginator.paginate.return_value = [
        {
            "modelSummaries": [
                {
                    "modelId": "anthropic.claude-3-haiku",
                    "modelName": "Claude 3 Haiku",
                    "providerName": "Anthropic",
                    "outputModalities": ["TEXT"],
                },
                {
                    "modelId": "stability.stable-diffusion-xl",
                    "modelName": "SDXL",
                    "providerName": "Stability",
                    "outputModalities": ["IMAGE"],  # should be excluded
                },
            ]
        }
    ]
    mock_bedrock_client.get_paginator.return_value = mock_paginator
    mock_session.return_value.client.return_value = mock_bedrock_client

    response = client.get("/api/models")
    assert response.status_code == 200
    data = response.json()

    ids = {m["id"] for m in data["models"]}
    assert "llama3" in ids
    assert "mistral" in ids
    assert "anthropic.claude-3-haiku" in ids
    # Image-only model must be excluded
    assert "stability.stable-diffusion-xl" not in ids

    providers = {m["provider"] for m in data["models"]}
    assert "ollama" in providers
    assert "bedrock" in providers


@patch("app.api.models.ollama.Client")
@patch("app.api.models.boto3.Session")
def test_list_models_ollama_error_returns_empty_ollama_list(mock_session, mock_ollama_client):
    mock_ollama_client.return_value.list.side_effect = Exception("connection refused")

    # Bedrock returns nothing
    mock_bedrock_client = MagicMock()
    mock_paginator = MagicMock()
    mock_paginator.paginate.return_value = [{"modelSummaries": []}]
    mock_bedrock_client.get_paginator.return_value = mock_paginator
    mock_session.return_value.client.return_value = mock_bedrock_client

    response = client.get("/api/models")
    assert response.status_code == 200
    data = response.json()
    assert all(m["provider"] != "ollama" for m in data["models"])


@patch("app.api.models.ollama.Client")
@patch("app.api.models.boto3.Session")
def test_list_models_no_credentials_returns_empty_bedrock(mock_session, mock_ollama_client):
    mock_ollama_client.return_value.list.return_value.models = []
    mock_session.return_value.client.side_effect = NoCredentialsError()

    response = client.get("/api/models")
    assert response.status_code == 200
    data = response.json()
    assert all(m["provider"] != "bedrock" for m in data["models"])


@patch("app.api.models.ollama.Client")
@patch("app.api.models.boto3.Session")
def test_list_models_boto_error_returns_empty_bedrock(mock_session, mock_ollama_client):
    mock_ollama_client.return_value.list.return_value.models = []
    mock_session.return_value.client.side_effect = BotoCoreError()

    response = client.get("/api/models")
    assert response.status_code == 200
    data = response.json()
    assert all(m["provider"] != "bedrock" for m in data["models"])


@patch("app.api.models.ollama.Client")
@patch("app.api.models.boto3.Session")
def test_list_models_bedrock_unexpected_error_returns_empty(mock_session, mock_ollama_client):
    mock_ollama_client.return_value.list.return_value.models = []
    mock_session.return_value.client.side_effect = RuntimeError("unexpected")

    response = client.get("/api/models")
    assert response.status_code == 200
    data = response.json()
    assert all(m["provider"] != "bedrock" for m in data["models"])


@patch("app.api.models.ollama.Client")
@patch("app.api.models.boto3.Session")
def test_list_models_model_without_provider_name(mock_session, mock_ollama_client):
    """Model with no providerName should display modelName alone."""
    mock_ollama_client.return_value.list.return_value.models = []

    mock_bedrock_client = MagicMock()
    mock_paginator = MagicMock()
    mock_paginator.paginate.return_value = [
        {
            "modelSummaries": [
                {
                    "modelId": "some.model",
                    "modelName": "Some Model",
                    "outputModalities": ["TEXT"],
                    # no providerName key
                },
            ]
        }
    ]
    mock_bedrock_client.get_paginator.return_value = mock_paginator
    mock_session.return_value.client.return_value = mock_bedrock_client

    response = client.get("/api/models")
    assert response.status_code == 200
    model = next(m for m in response.json()["models"] if m["id"] == "some.model")
    assert model["name"] == "Some Model"
