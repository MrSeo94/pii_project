"""PII 처리 파이프라인 오케스트레이터."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Optional

from kpii.config import PipelineConfig
from kpii.detectors.base import BaseDetector
from kpii.detectors.regex_detector import RegexDetector
from kpii.models import (
    Conversation,
    Message,
    PIIEntity,
    ProcessedConversation,
    ProcessedMessage,
)
from kpii.processors.base import BaseProcessor
from kpii.processors.generalizer import Generalizer
from kpii.processors.masker import Masker
from kpii.utils.logging import get_logger

logger = get_logger("pipeline")


class PIIPipeline:
    """PII 탐지→중복제거→처리 파이프라인.

    배치(process_conversation) 및 스트리밍(process_stream) 모두 지원.
    """

    def __init__(self, config: Optional[PipelineConfig] = None) -> None:
        self._config = config or PipelineConfig()
        self._detectors: list[BaseDetector] = []
        self._processors: list[BaseProcessor] = []

        self._build_pipeline()
        logger.debug(
            "PIIPipeline 초기화: detectors=%d, processors=%d",
            len(self._detectors),
            len(self._processors),
        )

    def _build_pipeline(self) -> None:
        """설정에 따라 탐지기/처리기 구성."""
        # Detectors
        if self._config.enable_regex:
            self._detectors.append(RegexDetector(self._config))

        if self._config.enable_llm:
            self._init_llm_detector()

        # Processors: 마스킹 먼저, 일반화 다음
        self._processors.append(Masker(self._config))
        self._processors.append(Generalizer(self._config))

    def _init_llm_detector(self) -> None:
        """LLM 탐지기 초기화 (lazy import)."""
        try:
            from kpii.detectors.llm_detector import LLMDetector
            from kpii.llm.openai_client import OpenAIClient

            if self._config.llm_config is None:
                logger.warning("LLM 활성화되었으나 llm_config 없음, 건너뜀")
                return

            client = OpenAIClient(self._config.llm_config)
            self._detectors.append(LLMDetector(self._config, client))
        except ImportError:
            logger.warning("openai 패키지 미설치. pip install kpii[llm]")

    def process_message(
        self,
        message: Message,
        context: Optional[list[Message]] = None,
    ) -> ProcessedMessage:
        """단일 메시지 처리."""
        entities = self._detect_all(message.content, context)
        entities = self._deduplicate(entities)
        processed_content = self._apply_processors(message.content, entities)

        return ProcessedMessage(
            original=message,
            processed_content=processed_content,
            entities=entities,
        )

    def process_conversation(self, conversation: Conversation) -> ProcessedConversation:
        """배치: 대화 전체 처리."""
        results: list[ProcessedMessage] = []

        for i, msg in enumerate(conversation.messages):
            context = conversation.messages[:i]
            processed = self.process_message(msg, context)
            results.append(processed)

        result = ProcessedConversation(
            conversation_id=conversation.conversation_id,
            messages=results,
        )
        logger.debug("대화 처리 완료: %s, 요약=%s", conversation.conversation_id, result.summary)
        return result

    async def process_stream(
        self,
        message_stream: AsyncIterator[Message],
    ) -> AsyncIterator[ProcessedMessage]:
        """스트리밍: 메시지가 도착할 때마다 처리."""
        context_window: list[Message] = []

        async for msg in message_stream:
            context_window.append(msg)
            # 최근 10개 메시지만 문맥으로 유지
            context = context_window[-10:]

            processed = self.process_message(msg, context)
            yield processed

    def _detect_all(
        self,
        text: str,
        context: Optional[list[Message]],
    ) -> list[PIIEntity]:
        """모든 탐지기 실행 후 결과 합산."""
        all_entities: list[PIIEntity] = []

        for detector in self._detectors:
            try:
                entities = detector.detect(text, context)
                all_entities.extend(entities)
            except Exception:
                logger.exception("탐지기 실행 실패: %s", type(detector).__name__)

        return all_entities

    def _deduplicate(self, entities: list[PIIEntity]) -> list[PIIEntity]:
        """겹치는 span 해소: 높은 score 우선, 같으면 긴 span 우선."""
        if not entities:
            return []

        # score 내림차순, 길이 내림차순 정렬
        sorted_entities = sorted(
            entities,
            key=lambda e: (-e.score, -(e.end - e.start)),
        )

        result: list[PIIEntity] = []
        for entity in sorted_entities:
            if not any(self._overlaps(entity, existing) for existing in result):
                result.append(entity)

        return sorted(result, key=lambda e: e.start)

    @staticmethod
    def _overlaps(a: PIIEntity, b: PIIEntity) -> bool:
        """두 엔티티의 span이 겹치는지 확인."""
        return a.start < b.end and b.start < a.end

    def _apply_processors(self, text: str, entities: list[PIIEntity]) -> str:
        """모든 엔티티를 offset 역순으로 한 번에 처리.

        마스킹과 일반화를 순차 적용하면 offset이 틀어지므로,
        각 엔티티의 교체 텍스트를 미리 계산한 후 역순으로 한 번에 적용.
        """
        if not entities:
            return text

        # 각 엔티티의 교체 텍스트 미리 계산
        replacements: list[tuple[int, int, str]] = []
        for entity in entities:
            replaced = None
            for processor in self._processors:
                result = processor.process(entity.text, [
                    PIIEntity(
                        pii_type=entity.pii_type,
                        start=0,
                        end=len(entity.text),
                        text=entity.text,
                        score=entity.score,
                        source=entity.source,
                    )
                ])
                if result != entity.text:
                    replaced = result
                    break
            if replaced is not None:
                replacements.append((entity.start, entity.end, replaced))

        # offset 역순 정렬 후 적용
        replacements.sort(key=lambda r: r[0], reverse=True)
        result = text
        for start, end, replacement in replacements:
            result = result[:start] + replacement + result[end:]

        return result
