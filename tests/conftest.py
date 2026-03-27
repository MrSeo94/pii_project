"""공유 테스트 픽스처."""

import pytest

from kpii.config import PipelineConfig
from kpii.models import Conversation, Message


@pytest.fixture
def default_config():
    return PipelineConfig()


@pytest.fixture
def sample_conversation():
    """쇼핑몰 AI 대화 샘플."""
    return Conversation(
        conversation_id="test-001",
        messages=[
            Message(
                role="user",
                content="안녕하세요, 주문한 상품 배송 확인하고 싶습니다.",
            ),
            Message(
                role="assistant",
                content="안녕하세요! 주문 확인을 위해 성함과 연락처를 알려주시겠어요?",
            ),
            Message(
                role="user",
                content=(
                    "김민수이고, 전화번호는 010-1234-5678이에요. "
                    "배송지는 서울시 강남구 삼성동 123-45이고, "
                    "이메일은 minsu.kim@example.com입니다."
                ),
            ),
            Message(
                role="assistant",
                content="확인되었습니다. 3월 15일에 발송된 택배가 배송 중입니다.",
            ),
        ],
    )


@pytest.fixture
def pii_rich_text():
    """다양한 PII가 포함된 텍스트."""
    return (
        "제 주민번호는 900101-1234567이고, "
        "카드번호는 4111-1111-1111-1111입니다. "
        "연락처는 010-9876-5432이고 "
        "이메일은 test@example.com이에요. "
        "나이는 만 34세이고 "
        "주소는 서울시 강남구 역삼동 789-12입니다."
    )
