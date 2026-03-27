"""LLM 클라이언트 추상 클래스."""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseLLMClient(ABC):
    """LLM 클라이언트 인터페이스."""

    @abstractmethod
    def chat(self, messages: list[dict[str, str]]) -> str:
        """메시지를 보내고 응답 텍스트 반환.

        Args:
            messages: [{"role": "system"|"user", "content": "..."}]

        Returns:
            LLM 응답 텍스트
        """
        ...
