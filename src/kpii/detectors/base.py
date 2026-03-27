"""탐지기 베이스 클래스."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from kpii.models import Message, PIIEntity


class BaseDetector(ABC):
    """PII 탐지기 추상 클래스."""

    @abstractmethod
    def detect(
        self,
        text: str,
        context: Optional[list[Message]] = None,
    ) -> list[PIIEntity]:
        """텍스트에서 PII 엔티티를 탐지하여 반환.

        Args:
            text: 탐지 대상 텍스트
            context: 주변 대화 메시지 (LLM 탐지기에서 활용)

        Returns:
            탐지된 PIIEntity 리스트
        """
        ...
