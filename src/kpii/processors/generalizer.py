"""준식별자 일반화 프로세서."""

from __future__ import annotations

import re

from kpii.config import PipelineConfig
from kpii.models import QUASI_IDENTIFIER_TYPES, PIIEntity, PIIType
from kpii.processors.base import BaseProcessor
from kpii.utils.logging import get_logger

logger = get_logger("generalizer")


class Generalizer(BaseProcessor):
    """준식별자(나이, 주소, 날짜)를 일반화."""

    def __init__(self, config: PipelineConfig) -> None:
        self._config = config

    def process(self, text: str, entities: list[PIIEntity]) -> str:
        # 준식별자만 필터링
        quasi_entities = [
            e for e in entities if e.pii_type in QUASI_IDENTIFIER_TYPES
        ]

        if not quasi_entities:
            return text

        # offset 역순 정렬
        sorted_entities = sorted(quasi_entities, key=lambda e: e.start, reverse=True)

        result = text
        for entity in sorted_entities:
            generalized = self._generalize(entity)
            if generalized and generalized != entity.text:
                result = result[:entity.start] + generalized + result[entity.end:]
                logger.debug(
                    "일반화: '%s' → '%s'", entity.text, generalized,
                )

        return result

    def _generalize(self, entity: PIIEntity) -> str:
        """엔티티 타입에 따라 일반화."""
        if entity.pii_type == PIIType.AGE:
            return self._generalize_age(entity.text)
        elif entity.pii_type == PIIType.ADDRESS:
            return self._generalize_address(entity.text)
        elif entity.pii_type == PIIType.DATE:
            return self._generalize_date(entity.text)
        return entity.text

    def _generalize_age(self, text: str) -> str:
        """나이를 연령대로 일반화.

        "25살" → "20대", "만 32세" → "30대"
        """
        match = re.search(r"(\d{1,3})", text)
        if not match:
            return text

        age = int(match.group(1))
        if age < 1 or age > 150:
            return text

        decade = (age // self._config.age_bucket_size) * self._config.age_bucket_size
        return f"{decade}대"

    def _generalize_address(self, text: str) -> str:
        """주소를 시/구 수준으로 일반화.

        "서울시 강남구 삼성동 123-45" → "서울 강남구"
        """
        # 시/도 추출
        sido_match = re.match(
            r"(서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주)"
            r"(?:특별시|광역시|특별자치시|특별자치도|도|시)?",
            text,
        )
        if not sido_match:
            return text

        sido = sido_match.group(1)

        # 시/군/구 추출
        remaining = text[sido_match.end():].strip()
        sigungu_match = re.match(r"([\w]{1,10}(?:시|군|구))", remaining)

        if sigungu_match:
            return f"{sido} {sigungu_match.group(1)}"

        return sido

    def _generalize_date(self, text: str) -> str:
        """날짜를 월 또는 년 수준으로 일반화.

        "2024년 3월 15일" → "2024년 3월"
        "2024.03.15" → "2024년 3월"
        """
        match = re.search(r"(\d{4})\s*(?:년\s*|[./-]\s*)(1[0-2]|0?[1-9])", text)
        if not match:
            return text

        year = match.group(1)
        month = int(match.group(2))

        if self._config.date_level == "년":
            return f"{year}년"

        return f"{year}년 {month}월"
