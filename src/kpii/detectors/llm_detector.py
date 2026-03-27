"""LLM 기반 문맥 인식 PII 탐지기."""

from __future__ import annotations

import json
from typing import Optional

from kpii.config import PipelineConfig
from kpii.detectors.base import BaseDetector
from kpii.llm.base import BaseLLMClient
from kpii.llm.prompts import build_detection_prompt
from kpii.models import DetectorSource, Message, PIIEntity, PIIType
from kpii.utils.logging import get_logger

logger = get_logger("llm_detector")

# LLM 응답의 type 필드 → PIIType 매핑
_TYPE_MAP: dict[str, PIIType] = {
    "이름": PIIType.NAME,
    "주소": PIIType.ADDRESS,
    "나이": PIIType.AGE,
    "날짜": PIIType.DATE,
    "전화번호": PIIType.PHONE,
    "이메일": PIIType.EMAIL,
    "주민등록번호": PIIType.RESIDENT_REG_NO,
    "신용카드번호": PIIType.CREDIT_CARD,
    "계좌번호": PIIType.BANK_ACCOUNT,
    "여권번호": PIIType.PASSPORT,
    "운전면허번호": PIIType.DRIVERS_LICENSE,
}


class LLMDetector(BaseDetector):
    """LLM 기반 문맥 인식 PII 탐지기.

    정규식으로 탐지하기 어려운 한국 인명, 비정형 주소 등을 탐지.
    """

    def __init__(self, config: PipelineConfig, llm_client: BaseLLMClient) -> None:
        self._config = config
        self._client = llm_client
        logger.debug("LLMDetector 초기화")

    def detect(
        self,
        text: str,
        context: Optional[list[Message]] = None,
        already_detected: Optional[list[PIIEntity]] = None,
    ) -> list[PIIEntity]:
        """LLM으로 PII 탐지.

        Args:
            text: 탐지 대상 텍스트
            context: 주변 대화 메시지
            already_detected: regex로 이미 탐지된 엔티티 (중복 방지)
        """
        prompt = build_detection_prompt(text, context, already_detected)

        try:
            response = self._client.chat(prompt)
        except Exception:
            logger.exception("LLM 호출 실패")
            return []

        return self._parse_response(response, text)

    def _parse_response(self, response: str, original_text: str) -> list[PIIEntity]:
        """LLM JSON 응답을 PIIEntity 리스트로 파싱."""
        try:
            # LLM이 markdown 코드블록으로 감쌀 수 있으므로 정리
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]
                cleaned = cleaned.rsplit("```", 1)[0]

            items = json.loads(cleaned)
            if not isinstance(items, list):
                return []
        except (json.JSONDecodeError, IndexError, TypeError):
            logger.warning("LLM 응답 파싱 실패: %s", response[:200])
            return []

        entities: list[PIIEntity] = []
        for item in items:
            pii_type = _TYPE_MAP.get(item.get("type", ""))
            if pii_type is None:
                continue

            if not self._config.is_pii_type_enabled(pii_type):
                continue

            matched_text = item.get("text", "")
            confidence = float(item.get("confidence", 0.8))

            # 원본 텍스트에서 위치 찾기
            start = original_text.find(matched_text)
            if start == -1:
                logger.debug("LLM 탐지 텍스트를 원문에서 찾을 수 없음: %s", matched_text)
                continue

            end = start + len(matched_text)

            entities.append(
                PIIEntity(
                    pii_type=pii_type,
                    start=start,
                    end=end,
                    text=matched_text,
                    score=confidence,
                    source=DetectorSource.LLM,
                )
            )

        logger.debug("LLMDetector: %d개 엔티티 탐지", len(entities))
        return entities
