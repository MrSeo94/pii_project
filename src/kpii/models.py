"""Core data models for kpii."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class PIIType(Enum):
    """PII 유형."""

    RESIDENT_REG_NO = "주민등록번호"
    PHONE = "전화번호"
    EMAIL = "이메일"
    CREDIT_CARD = "신용카드번호"
    BANK_ACCOUNT = "계좌번호"
    PASSPORT = "여권번호"
    DRIVERS_LICENSE = "운전면허번호"
    NAME = "이름"
    AGE = "나이"
    ADDRESS = "주소"
    DATE = "날짜"


class DetectorSource(Enum):
    """탐지기 출처."""

    REGEX = "regex"
    LLM = "llm"
    DICTIONARY = "dictionary"


# 직접식별자 vs 준식별자 분류
DIRECT_IDENTIFIER_TYPES = {
    PIIType.RESIDENT_REG_NO,
    PIIType.PHONE,
    PIIType.EMAIL,
    PIIType.CREDIT_CARD,
    PIIType.BANK_ACCOUNT,
    PIIType.PASSPORT,
    PIIType.DRIVERS_LICENSE,
    PIIType.NAME,
}

QUASI_IDENTIFIER_TYPES = {
    PIIType.AGE,
    PIIType.ADDRESS,
    PIIType.DATE,
}


@dataclass(frozen=True)
class PIIEntity:
    """탐지된 PII 엔티티."""

    pii_type: PIIType
    start: int
    end: int
    text: str
    score: float = 1.0
    source: DetectorSource = DetectorSource.REGEX


@dataclass
class Message:
    """대화 메시지."""

    role: str  # "user" | "assistant" | "system"
    content: str
    metadata: dict = field(default_factory=dict)


@dataclass
class Conversation:
    """대화 전체."""

    conversation_id: str
    messages: list[Message]
    metadata: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> Conversation:
        """JSON dict에서 Conversation 생성."""
        messages = [
            Message(
                role=m["role"],
                content=m["content"],
                metadata=m.get("metadata", {}),
            )
            for m in data["messages"]
        ]
        return cls(
            conversation_id=data.get("conversation_id", ""),
            messages=messages,
            metadata=data.get("metadata", {}),
        )


@dataclass
class ProcessedMessage:
    """처리된 메시지."""

    original: Message
    processed_content: str
    entities: list[PIIEntity] = field(default_factory=list)


@dataclass
class ProcessedConversation:
    """처리된 대화 전체."""

    conversation_id: str
    messages: list[ProcessedMessage]

    @property
    def summary(self) -> dict:
        """PII 타입별 탐지 건수 요약."""
        counts: dict[str, int] = {}
        for msg in self.messages:
            for entity in msg.entities:
                key = entity.pii_type.value
                counts[key] = counts.get(key, 0) + 1
        return counts
