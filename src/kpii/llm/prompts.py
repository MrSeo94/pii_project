"""PII 탐지용 LLM 프롬프트 템플릿."""

from __future__ import annotations

from typing import Optional

from kpii.models import Message, PIIEntity

SYSTEM_PROMPT = """당신은 한국어 쇼핑몰 AI 상담 대화에서 개인정보를 탐지하는 전문가입니다.

주어진 텍스트에서 다음 개인정보를 찾아 JSON 배열로 응답하세요:
- 이름: 사람 이름 (상호명, 브랜드명 제외)
- 주소: 배송지, 거주지 등 위치 정보
- 나이: 나이, 생년월일 등 연령 정보
- 날짜: 특정 날짜 정보

주의사항:
- 정규식으로 이미 탐지된 항목은 제외하세요
- 상호명, 브랜드명, 상품명은 개인정보가 아닙니다
- confidence는 0.0~1.0 사이 값입니다

응답 형식 (JSON 배열만 출력):
[{"type": "이름", "text": "김민수", "confidence": 0.95}]

탐지할 항목이 없으면 빈 배열 []을 반환하세요."""


def build_detection_prompt(
    text: str,
    context: Optional[list[Message]] = None,
    already_detected: Optional[list[PIIEntity]] = None,
) -> list[dict[str, str]]:
    """LLM 탐지 프롬프트 구성."""
    messages: list[dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]

    # 대화 문맥 추가
    if context:
        context_text = "\n".join(
            f"[{m.role}]: {m.content}" for m in context[-5:]
        )
        messages.append({
            "role": "user",
            "content": f"대화 문맥:\n{context_text}",
        })

    # 이미 탐지된 항목 알려주기
    already_info = ""
    if already_detected:
        items = [f"- {e.pii_type.value}: '{e.text}'" for e in already_detected]
        already_info = f"\n\n정규식으로 이미 탐지된 항목 (제외하세요):\n" + "\n".join(items)

    messages.append({
        "role": "user",
        "content": f"다음 텍스트에서 개인정보를 탐지하세요:\n\n{text}{already_info}",
    })

    return messages
