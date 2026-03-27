"""프로세서 베이스 클래스."""

from __future__ import annotations

from abc import ABC, abstractmethod

from kpii.models import PIIEntity


class BaseProcessor(ABC):
    """PII 처리기 추상 클래스."""

    @abstractmethod
    def process(self, text: str, entities: list[PIIEntity]) -> str:
        """텍스트에서 PII를 처리(마스킹/일반화)하여 반환.

        Args:
            text: 원본 텍스트
            entities: 탐지된 PIIEntity 리스트

        Returns:
            처리된 텍스트
        """
        ...
