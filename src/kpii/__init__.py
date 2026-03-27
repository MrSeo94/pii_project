"""kpii - 한국어 PII 탐지 및 비식별화 패키지."""

from __future__ import annotations

from typing import Optional

from kpii.config import LLMConfig, PipelineConfig
from kpii.models import (
    Conversation,
    Message,
    PIIEntity,
    PIIType,
    ProcessedConversation,
    ProcessedMessage,
)
from kpii.pipeline import PIIPipeline

__version__ = "0.1.0"

__all__ = [
    "create_pipeline",
    "PIIPipeline",
    "PipelineConfig",
    "LLMConfig",
    "Conversation",
    "Message",
    "PIIEntity",
    "PIIType",
    "ProcessedConversation",
    "ProcessedMessage",
]


def create_pipeline(
    *,
    enable_llm: bool = False,
    llm_api_key: Optional[str] = None,
    llm_model: str = "gpt-4o-mini",
    **kwargs,
) -> PIIPipeline:
    """편의 팩토리: 파이프라인 생성.

    Args:
        enable_llm: LLM 탐지기 활성화 여부
        llm_api_key: OpenAI API 키 (None이면 환경변수)
        llm_model: LLM 모델명
        **kwargs: PipelineConfig 추가 설정

    Returns:
        설정된 PIIPipeline 인스턴스

    Examples:
        >>> from kpii import create_pipeline, Conversation, Message
        >>> pipeline = create_pipeline()
        >>> conv = Conversation(
        ...     conversation_id="test",
        ...     messages=[Message(role="user", content="전화번호는 010-1234-5678입니다")]
        ... )
        >>> result = pipeline.process_conversation(conv)
        >>> print(result.messages[0].processed_content)
        전화번호는 [전화번호]입니다
    """
    llm_config = None
    if enable_llm:
        llm_config = LLMConfig(
            api_key=llm_api_key,
            model=llm_model,
        )

    config = PipelineConfig(
        enable_llm=enable_llm,
        llm_config=llm_config,
        **kwargs,
    )

    return PIIPipeline(config)
