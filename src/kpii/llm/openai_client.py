"""OpenAI LLM 클라이언트 구현."""

from __future__ import annotations

from kpii.config import LLMConfig
from kpii.llm.base import BaseLLMClient
from kpii.utils.logging import get_logger

logger = get_logger("openai_client")


class OpenAIClient(BaseLLMClient):
    """OpenAI API 클라이언트."""

    def __init__(self, config: LLMConfig) -> None:
        self._config = config
        try:
            from openai import OpenAI

            self._client = OpenAI(
                api_key=config.api_key,
                timeout=config.timeout,
            )
        except ImportError:
            raise ImportError(
                "openai 패키지가 필요합니다. pip install kpii[llm]"
            )

        logger.debug("OpenAI 클라이언트 초기화: model=%s", config.model)

    def chat(self, messages: list[dict[str, str]]) -> str:
        """OpenAI Chat API 호출."""
        response = self._client.chat.completions.create(
            model=self._config.model,
            messages=messages,  # type: ignore[arg-type]
            temperature=self._config.temperature,
            max_tokens=self._config.max_tokens,
        )

        content = response.choices[0].message.content or ""
        logger.debug("OpenAI 응답 수신: %d자", len(content))
        return content
