from openai import OpenAI

from config import LMStudioConfig
from core.models import LLMRequest, LLMResponse


class LLMClient:
    """LM Studio client."""

    def __init__(self, config: LMStudioConfig) -> None:
        self._client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout,
        )
        self._model = config.model

    def generate(self, request: LLMRequest) -> LLMResponse:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": message.role.value,
                    "content": message.content,
                }
                for message in request.messages
            ],
        )

        content = response.choices[0].message.content or ""

        return LLMResponse(content=content)