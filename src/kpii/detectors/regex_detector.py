"""정규식 기반 PII 탐지기."""

from __future__ import annotations

from typing import Optional

from kpii.config import PipelineConfig
from kpii.detectors.base import BaseDetector
from kpii.models import DetectorSource, Message, PIIEntity
from kpii.patterns.korean import PIIPattern, get_all_patterns
from kpii.utils.logging import get_logger

logger = get_logger("regex_detector")


class RegexDetector(BaseDetector):
    """정규식 + 체크섬 기반 한국어 PII 탐지기."""

    def __init__(self, config: PipelineConfig) -> None:
        self._config = config
        self._patterns = [
            p for p in get_all_patterns()
            if config.is_pii_type_enabled(p.pii_type)
        ]
        logger.debug("RegexDetector 초기화: %d개 패턴 로드", len(self._patterns))

    def detect(
        self,
        text: str,
        context: Optional[list[Message]] = None,
    ) -> list[PIIEntity]:
        entities: list[PIIEntity] = []

        for pii_pattern in self._patterns:
            found = self._detect_pattern(text, pii_pattern)
            entities.extend(found)

        logger.debug("RegexDetector: %d개 엔티티 탐지", len(entities))
        return entities

    def _detect_pattern(self, text: str, pii_pattern: PIIPattern) -> list[PIIEntity]:
        """단일 패턴으로 탐지."""
        results: list[PIIEntity] = []

        for match in pii_pattern.pattern.finditer(text):
            matched_text = match.group()
            start, end = match.start(), match.end()

            # 체크섬 검증: 실패 시 score 감소하여 포함 (형식은 매칭됨)
            score = pii_pattern.score
            if pii_pattern.validator and not pii_pattern.validator(matched_text):
                score = max(0.3, pii_pattern.score - 0.4)
                logger.debug(
                    "체크섬 실패 (낮은 score로 포함): %s (%s) score=%.2f",
                    pii_pattern.pii_type.value, matched_text, score,
                )

            # 문맥 키워드 게이팅
            if pii_pattern.context_keywords:
                if not self._check_context_keywords(
                    text, start, end, pii_pattern.context_keywords
                ):
                    logger.debug(
                        "문맥 키워드 없음: %s (%s)", pii_pattern.pii_type.value, matched_text
                    )
                    continue

            entity = PIIEntity(
                pii_type=pii_pattern.pii_type,
                start=start,
                end=end,
                text=matched_text,
                score=score,
                source=DetectorSource.REGEX,
            )
            results.append(entity)

        return results

    def _check_context_keywords(
        self,
        text: str,
        start: int,
        end: int,
        keywords: list[str],
    ) -> bool:
        """매치 주변에 문맥 키워드가 존재하는지 확인."""
        window = self._config.context_window_chars
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        context_text = text[context_start:context_end].lower()

        return any(kw.lower() in context_text for kw in keywords)
