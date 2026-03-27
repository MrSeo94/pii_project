"""Configuration for kpii pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from kpii.models import PIIType


@dataclass
class LLMConfig:
    """LLM 클라이언트 설정."""

    provider: str = "openai"
    model: str = "gpt-4o-mini"
    api_key: Optional[str] = None  # None이면 환경변수 사용
    temperature: float = 0.0
    max_tokens: int = 1024
    timeout: float = 10.0


@dataclass
class PipelineConfig:
    """파이프라인 설정."""

    # 탐지기 활성화
    enable_regex: bool = True
    enable_llm: bool = False
    enable_dictionary: bool = False  # 미래 확장용

    # LLM 설정
    llm_config: Optional[LLMConfig] = None

    # 마스킹 포맷
    mask_format: str = "[{pii_type}]"  # e.g., "[전화번호]"

    # 활성화할 PII 타입 (None이면 전체)
    enabled_pii_types: Optional[set[PIIType]] = None

    # 준식별자 일반화 설정
    age_bucket_size: int = 10  # 10 → 20대, 30대...
    address_level: str = "시/구"
    date_level: str = "월"  # "월" or "년"

    # 로깅
    log_level: str = "DEBUG"

    # 문맥 키워드 게이팅: 계좌번호 등 모호한 패턴에 필요한 근접 키워드
    context_window_chars: int = 30

    def is_pii_type_enabled(self, pii_type: PIIType) -> bool:
        """해당 PII 타입이 활성화되어 있는지 확인."""
        if self.enabled_pii_types is None:
            return True
        return pii_type in self.enabled_pii_types
