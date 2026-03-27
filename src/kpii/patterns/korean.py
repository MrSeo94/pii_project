"""한국어 PII 정규식 패턴 정의."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Optional

from kpii.models import PIIType


@dataclass
class PIIPattern:
    """PII 탐지 패턴."""

    pii_type: PIIType
    pattern: re.Pattern
    validator: Optional[Callable[[str], bool]] = None
    context_keywords: Optional[list[str]] = None  # 근접 키워드 (모호한 패턴용)
    score: float = 1.0


# ──────────────────────────────────────────────
# 주민등록번호: 6자리-7자리 (뒷자리 1~4로 시작)
# ──────────────────────────────────────────────
RESIDENT_REG_NO_PATTERN = re.compile(
    r"\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])"  # 생년월일 6자리
    r"\s*[-–]\s*"
    r"[1-4]\d{6}"  # 성별코드 + 6자리
)

# ──────────────────────────────────────────────
# 전화번호: 휴대폰 + 유선
# ──────────────────────────────────────────────
# 휴대폰: 010-1234-5678, 01012345678, 010.1234.5678
MOBILE_PHONE_PATTERN = re.compile(
    r"01[016789]"
    r"[-.\s)]?\s*"
    r"\d{3,4}"
    r"[-.\s]?\s*"
    r"\d{4}"
)

# 유선전화: 02-1234-5678, 031-123-4567
LANDLINE_PATTERN = re.compile(
    r"0[2-6][0-9]{0,2}"
    r"[-.\s)]?\s*"
    r"\d{3,4}"
    r"[-.\s]?\s*"
    r"\d{4}"
)

# ──────────────────────────────────────────────
# 이메일
# ──────────────────────────────────────────────
EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
)

# ──────────────────────────────────────────────
# 신용카드번호: 16자리 (4-4-4-4)
# ──────────────────────────────────────────────
CREDIT_CARD_PATTERN = re.compile(
    r"\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}"
)

# ──────────────────────────────────────────────
# 계좌번호: 10~14자리, 문맥 키워드 필요
# ──────────────────────────────────────────────
BANK_ACCOUNT_PATTERN = re.compile(
    r"\d{3,4}[-]\d{2,6}[-]\d{2,6}(?:[-]\d{1,3})?"
)

BANK_CONTEXT_KEYWORDS = [
    "계좌", "입금", "송금", "이체", "통장", "은행",
    "국민", "신한", "우리", "하나", "농협", "기업",
    "카카오뱅크", "토스뱅크", "케이뱅크",
]

# ──────────────────────────────────────────────
# 여권번호: 알파벳 1~2자 + 숫자 7~8자리
# ──────────────────────────────────────────────
PASSPORT_PATTERN = re.compile(
    r"[A-Z]{1,2}\d{7,8}"
)

PASSPORT_CONTEXT_KEYWORDS = ["여권", "passport", "패스포트"]

# ──────────────────────────────────────────────
# 운전면허번호: 지역(2)-년도(2)-번호(6)-체크(2)
# ──────────────────────────────────────────────
DRIVERS_LICENSE_PATTERN = re.compile(
    r"\d{2}\s*[-]\s*\d{2}\s*[-]\s*\d{6}\s*[-]\s*\d{2}"
)

DRIVERS_LICENSE_CONTEXT_KEYWORDS = ["면허", "운전", "license"]

# ──────────────────────────────────────────────
# 준식별자: 나이
# ──────────────────────────────────────────────
AGE_PATTERN = re.compile(
    r"(?:만\s*)?"
    r"(\d{1,3})\s*"
    r"(?:살|세)"
)

# ──────────────────────────────────────────────
# 준식별자: 날짜 (한국어 형식)
# ──────────────────────────────────────────────
DATE_PATTERN = re.compile(
    r"(\d{4})\s*(?:년\s*|[./-]\s*)"
    r"(0?[1-9]|1[0-2])\s*(?:월\s*|[./-]\s*)"
    r"(3[01]|[12]\d|0?[1-9])\s*일?"
)

# ──────────────────────────────────────────────
# 준식별자: 주소 (한국어 주소 패턴)
# ──────────────────────────────────────────────
# 시/도 + 시/군/구 + 상세주소
ADDRESS_PATTERN = re.compile(
    r"(?:서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주)"
    r"(?:특별시|광역시|특별자치시|특별자치도|도|시)?\s*"
    r"(?:"
    r"(?:[\w]{1,10}(?:시|군|구)\s*)*[\w]{1,10}(?:읍|면|동|로|길)[^,.!?\n]*?"  # 시/군/구 + 동/읍/면/로/길
    r"|"
    r"[\w]{1,10}(?:시|군|구)(?:\s*[\w]{1,10}(?:시|군|구))*"  # 시/군/구만 (동 없이)
    r")"
    r"(?=\s*[,.]|\s*이고|\s*입니다|\s*인데|\s*으로|\s*에서|\s*까지|\s*$)"
)


def get_all_patterns() -> list[PIIPattern]:
    """모든 PII 패턴 반환."""
    from kpii.utils.validators import validate_luhn, validate_resident_registration_number

    return [
        # 직접식별자
        PIIPattern(
            pii_type=PIIType.RESIDENT_REG_NO,
            pattern=RESIDENT_REG_NO_PATTERN,
            validator=validate_resident_registration_number,
            score=0.95,
        ),
        PIIPattern(
            pii_type=PIIType.PHONE,
            pattern=MOBILE_PHONE_PATTERN,
            score=0.95,
        ),
        PIIPattern(
            pii_type=PIIType.PHONE,
            pattern=LANDLINE_PATTERN,
            score=0.85,
        ),
        PIIPattern(
            pii_type=PIIType.EMAIL,
            pattern=EMAIL_PATTERN,
            score=0.99,
        ),
        PIIPattern(
            pii_type=PIIType.CREDIT_CARD,
            pattern=CREDIT_CARD_PATTERN,
            validator=validate_luhn,
            score=0.90,
        ),
        PIIPattern(
            pii_type=PIIType.BANK_ACCOUNT,
            pattern=BANK_ACCOUNT_PATTERN,
            context_keywords=BANK_CONTEXT_KEYWORDS,
            score=0.80,
        ),
        PIIPattern(
            pii_type=PIIType.PASSPORT,
            pattern=PASSPORT_PATTERN,
            context_keywords=PASSPORT_CONTEXT_KEYWORDS,
            score=0.80,
        ),
        PIIPattern(
            pii_type=PIIType.DRIVERS_LICENSE,
            pattern=DRIVERS_LICENSE_PATTERN,
            context_keywords=DRIVERS_LICENSE_CONTEXT_KEYWORDS,
            score=0.85,
        ),
        # 준식별자
        PIIPattern(
            pii_type=PIIType.AGE,
            pattern=AGE_PATTERN,
            score=0.90,
        ),
        PIIPattern(
            pii_type=PIIType.DATE,
            pattern=DATE_PATTERN,
            score=0.85,
        ),
        PIIPattern(
            pii_type=PIIType.ADDRESS,
            pattern=ADDRESS_PATTERN,
            score=0.75,
        ),
    ]
