"""직접식별자 마스킹 프로세서."""

from __future__ import annotations

from kpii.config import PipelineConfig
from kpii.models import DIRECT_IDENTIFIER_TYPES, PIIEntity
from kpii.processors.base import BaseProcessor
from kpii.utils.logging import get_logger

logger = get_logger("masker")


class Masker(BaseProcessor):
    """직접식별자를 [TYPE] 형태로 마스킹."""

    def __init__(self, config: PipelineConfig) -> None:
        self._config = config

    def process(self, text: str, entities: list[PIIEntity]) -> str:
        # 직접식별자만 필터링
        direct_entities = [
            e for e in entities if e.pii_type in DIRECT_IDENTIFIER_TYPES
        ]

        if not direct_entities:
            return text

        # offset 역순 정렬 (뒤에서부터 교체하여 위치 보존)
        sorted_entities = sorted(direct_entities, key=lambda e: e.start, reverse=True)

        result = text
        for entity in sorted_entities:
            mask = self._config.mask_format.format(pii_type=entity.pii_type.value)
            result = result[:entity.start] + mask + result[entity.end:]
            logger.debug(
                "마스킹: '%s' → '%s' (위치 %d-%d)",
                entity.text, mask, entity.start, entity.end,
            )

        return result
