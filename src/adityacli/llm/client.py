from openai import OpenAI
from openai import OpenAIError

from adityacli.config import LMStudioConfig
from adityacli.core.models import Message
from adityacli.exceptions import ConnectionError, LLMError


class LLMClient:
    """LM Studio client."""

    def __init__(self, config: LMStudioConfig) -> None:
        self._client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout,
        )
        self._model = config.model

    def generate(self, messages: list[Message]) -> str:
        """
        Generate a response from the language model.
        """

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {
                        "role": message.role.value,
                        "content": message.content,
                    }
                    for message in messages
                ],
            )
        except OpenAIError as exc:
            raise ConnectionError(str(exc)) from exc
        except Exception as exc:
            raise LLMError(str(exc)) from exc

        content = response.choices[0].message.content

        if content is None:
            return ""

        return content