"""AWS Bedrock implementation of LLMService using the Converse API."""
import logging
from typing import Optional
import boto3
from .base import LLMService

logger = logging.getLogger(__name__)


class BedrockLLMService(LLMService):
    """
    Sends messages to an AWS Bedrock foundation model via the Converse API.

    The Converse API provides a unified interface across all Bedrock models,
    handling provider-specific differences (Anthropic, Meta, Amazon, etc.)
    transparently.

    Authentication uses boto3's standard credential chain:
    - AWS_PROFILE env var / aws_profile config
    - Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
    - ~/.aws/credentials file
    - IAM instance role (EC2/ECS/Lambda)
    """

    def __init__(
        self,
        model_id: str,
        region: str = "us-east-1",
        aws_profile: Optional[str] = None,
    ) -> None:
        self._model_id = model_id
        session = boto3.Session(profile_name=aws_profile, region_name=region)
        self._client = session.client("bedrock-runtime")
        logger.info(
            "BedrockLLMService initialized (model=%s, region=%s, profile=%s).",
            model_id,
            region,
            aws_profile or "default chain",
        )

    def chat(self, messages: list[dict]) -> str:
        """
        Send messages to Bedrock and return the assistant's reply.

        Accepts messages in OpenAI-compatible format:
            [{"role": "system"|"user"|"assistant", "content": "..."}]

        Converts to Bedrock Converse format internally.
        """
        system_parts, conversation = self._convert_messages(messages)

        kwargs: dict = {
            "modelId": self._model_id,
            "messages": conversation,
        }
        if system_parts:
            kwargs["system"] = system_parts

        response = self._client.converse(**kwargs)
        reply = response["output"]["message"]["content"][0]["text"].strip()
        logger.debug("Bedrock reply: %s", reply)
        return reply

    @staticmethod
    def _convert_messages(messages: list[dict]) -> tuple[list[dict], list[dict]]:
        """
        Split OpenAI-format messages into Bedrock system + conversation lists.

        Returns:
            system_parts: list of {"text": "..."} dicts for system instructions
            conversation: list of Bedrock-format conversation turns
        """
        system_parts: list[dict] = []
        conversation: list[dict] = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                system_parts.append({"text": content})
            elif role in ("user", "assistant"):
                conversation.append({
                    "role": role,
                    "content": [{"text": content}],
                })

        return system_parts, conversation
