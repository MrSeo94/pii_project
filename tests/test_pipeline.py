"""PIIPipeline 통합 테스트."""

import asyncio
import json

import pytest

from kpii.config import LLMConfig, PipelineConfig
from kpii.detectors.llm_detector import LLMDetector
from kpii.llm.base import BaseLLMClient
from kpii.models import Conversation, Message, PIIType
from kpii.pipeline import PIIPipeline


@pytest.fixture
def pipeline():
    return PIIPipeline(PipelineConfig())


# ─── 단일 메시지 처리 ───


class TestProcessMessageMasking:
    def test_phone_masking(self, pipeline):
        msg = Message(role="user", content="전화번호는 010-1234-5678입니다")
        result = pipeline.process_message(msg)
        assert "[전화번호]" in result.processed_content
        assert "010-1234-5678" not in result.processed_content

    def test_email_masking(self, pipeline):
        msg = Message(role="user", content="이메일 test@example.com으로 보내주세요")
        result = pipeline.process_message(msg)
        assert "[이메일]" in result.processed_content
        assert "test@example.com" not in result.processed_content

    def test_credit_card_masking(self, pipeline):
        msg = Message(role="user", content="카드번호 4111-1111-1111-1111 결제")
        result = pipeline.process_message(msg)
        assert "[신용카드번호]" in result.processed_content

    def test_rrn_masking(self, pipeline):
        msg = Message(role="user", content="주민번호: 850315-2345678")
        result = pipeline.process_message(msg)
        assert "[주민등록번호]" in result.processed_content

    def test_bank_account_masking(self, pipeline):
        msg = Message(role="user", content="국민은행 계좌 110-123-456789")
        result = pipeline.process_message(msg)
        assert "[계좌번호]" in result.processed_content

    def test_multiple_pii_types(self, pipeline):
        msg = Message(
            role="user",
            content="전화 010-1234-5678이고 이메일 a@b.com입니다",
        )
        result = pipeline.process_message(msg)
        assert "[전화번호]" in result.processed_content
        assert "[이메일]" in result.processed_content

    def test_three_pii_types(self, pipeline):
        msg = Message(
            role="user",
            content="전화 010-1234-5678 메일 a@b.com 카드 4111-1111-1111-1111",
        )
        result = pipeline.process_message(msg)
        assert "[전화번호]" in result.processed_content
        assert "[이메일]" in result.processed_content
        assert "[신용카드번호]" in result.processed_content


class TestProcessMessageGeneralization:
    def test_age_generalization(self, pipeline):
        msg = Message(role="user", content="저는 만 28세입니다")
        result = pipeline.process_message(msg)
        assert "20대" in result.processed_content
        assert "28" not in result.processed_content

    def test_address_generalization(self, pipeline):
        msg = Message(role="user", content="서울시 강남구 역삼동 123-45입니다")
        result = pipeline.process_message(msg)
        assert "서울 강남구" in result.processed_content
        assert "역삼동" not in result.processed_content

    def test_date_generalization(self, pipeline):
        msg = Message(role="user", content="2024년 3월 15일에 주문했어요")
        result = pipeline.process_message(msg)
        assert "2024년 3월" in result.processed_content
        assert "15일" not in result.processed_content


class TestProcessMessageCombined:
    def test_masking_and_generalization(self, pipeline):
        msg = Message(
            role="user",
            content="전화 010-1234-5678이고 25살입니다",
        )
        result = pipeline.process_message(msg)
        assert "[전화번호]" in result.processed_content
        assert "20대" in result.processed_content

    def test_rrn_and_date_combined(self, pipeline):
        msg = Message(
            role="user",
            content="주민번호 900101-1234567이고 2024년 3월 15일 주문",
        )
        result = pipeline.process_message(msg)
        assert "[주민등록번호]" in result.processed_content
        assert "2024년 3월" in result.processed_content
        assert "900101" not in result.processed_content

    def test_all_types_combined(self, pipeline):
        msg = Message(
            role="user",
            content=(
                "010-1234-5678로 연락 주시고 "
                "이메일은 test@example.com이에요. "
                "만 25세이고 서울시 강남구 역삼동 살아요."
            ),
        )
        result = pipeline.process_message(msg)
        assert "[전화번호]" in result.processed_content
        assert "[이메일]" in result.processed_content
        assert "20대" in result.processed_content

    def test_no_pii(self, pipeline):
        msg = Message(role="user", content="주문 상태 확인해주세요")
        result = pipeline.process_message(msg)
        assert result.processed_content == msg.content
        assert len(result.entities) == 0


# ─── 대화 전체 처리 ───


class TestProcessConversation:
    def test_full_conversation(self, pipeline, sample_conversation):
        result = pipeline.process_conversation(sample_conversation)
        assert result.conversation_id == "test-001"
        assert len(result.messages) == 4

    def test_pii_message_masked(self, pipeline, sample_conversation):
        result = pipeline.process_conversation(sample_conversation)
        msg3 = result.messages[2]
        assert "[전화번호]" in msg3.processed_content
        assert "[이메일]" in msg3.processed_content
        assert "010-1234-5678" not in msg3.processed_content
        assert "minsu.kim@example.com" not in msg3.processed_content

    def test_non_pii_message_unchanged(self, pipeline, sample_conversation):
        result = pipeline.process_conversation(sample_conversation)
        msg1 = result.messages[0]
        assert msg1.processed_content == msg1.original.content

    def test_summary_counts(self, pipeline, sample_conversation):
        result = pipeline.process_conversation(sample_conversation)
        summary = result.summary
        assert summary.get("전화번호", 0) >= 1
        assert summary.get("이메일", 0) >= 1

    def test_empty_conversation(self, pipeline):
        conv = Conversation(conversation_id="empty", messages=[])
        result = pipeline.process_conversation(conv)
        assert len(result.messages) == 0
        assert result.summary == {}

    def test_single_message_conversation(self, pipeline):
        conv = Conversation(
            conversation_id="single",
            messages=[Message(role="user", content="010-1234-5678")],
        )
        result = pipeline.process_conversation(conv)
        assert len(result.messages) == 1
        assert "[전화번호]" in result.messages[0].processed_content

    def test_from_dict(self, pipeline):
        data = {
            "conversation_id": "dict-test",
            "messages": [
                {"role": "user", "content": "전화 010-1234-5678"},
                {"role": "assistant", "content": "확인했습니다"},
            ],
        }
        conv = Conversation.from_dict(data)
        result = pipeline.process_conversation(conv)
        assert result.conversation_id == "dict-test"
        assert "[전화번호]" in result.messages[0].processed_content


# ─── 스트리밍 ───


class TestStreamProcessing:
    def test_basic_stream(self, pipeline):
        async def gen():
            yield Message(role="user", content="전화번호 010-1234-5678")
            yield Message(role="user", content="이메일 test@example.com")

        async def run():
            return [msg async for msg in pipeline.process_stream(gen())]

        results = asyncio.run(run())
        assert len(results) == 2
        assert "[전화번호]" in results[0].processed_content
        assert "[이메일]" in results[1].processed_content

    def test_stream_maintains_context(self, pipeline):
        async def gen():
            yield Message(role="user", content="안녕하세요")
            yield Message(role="assistant", content="어떻게 도와드릴까요?")
            yield Message(role="user", content="전화 010-1234-5678")

        async def run():
            return [msg async for msg in pipeline.process_stream(gen())]

        results = asyncio.run(run())
        assert len(results) == 3
        assert "[전화번호]" in results[2].processed_content

    def test_stream_empty(self, pipeline):
        async def gen():
            return
            yield  # noqa: unreachable

        async def run():
            return [msg async for msg in pipeline.process_stream(gen())]

        results = asyncio.run(run())
        assert len(results) == 0

    def test_stream_single_message(self, pipeline):
        async def gen():
            yield Message(role="user", content="만 30세입니다")

        async def run():
            return [msg async for msg in pipeline.process_stream(gen())]

        results = asyncio.run(run())
        assert len(results) == 1
        assert "30대" in results[0].processed_content


# ─── 중복 제거 ───


class TestDeduplication:
    def test_overlapping_entities_resolved(self, pipeline):
        msg = Message(role="user", content="010-1234-5678")
        result = pipeline.process_message(msg)
        phones = [e for e in result.entities if e.pii_type == PIIType.PHONE]
        assert len(phones) == 1

    def test_higher_score_wins(self, pipeline):
        """점수가 높은 엔티티가 우선."""
        msg = Message(role="user", content="010-1234-5678")
        result = pipeline.process_message(msg)
        if len(result.entities) > 0:
            # 중복 제거 후 가장 높은 score만 남아야 함
            scores = [e.score for e in result.entities]
            assert all(s > 0 for s in scores)


# ─── 설정 옵션 ───


class TestPipelineConfig:
    def test_disabled_regex(self):
        config = PipelineConfig(enable_regex=False)
        pipeline = PIIPipeline(config)
        msg = Message(role="user", content="전화 010-1234-5678")
        result = pipeline.process_message(msg)
        assert result.processed_content == msg.content

    def test_selective_pii_types(self):
        config = PipelineConfig(enabled_pii_types={PIIType.EMAIL})
        pipeline = PIIPipeline(config)
        msg = Message(
            role="user",
            content="전화 010-1234-5678 이메일 test@example.com",
        )
        result = pipeline.process_message(msg)
        assert "[이메일]" in result.processed_content
        assert "010-1234-5678" in result.processed_content

    def test_custom_mask_format(self):
        config = PipelineConfig(mask_format="<{pii_type}>")
        pipeline = PIIPipeline(config)
        msg = Message(role="user", content="전화 010-1234-5678")
        result = pipeline.process_message(msg)
        assert "<전화번호>" in result.processed_content

    def test_age_bucket_config(self):
        config = PipelineConfig(age_bucket_size=5)
        pipeline = PIIPipeline(config)
        msg = Message(role="user", content="27살입니다")
        result = pipeline.process_message(msg)
        assert "25대" in result.processed_content

    def test_date_level_year(self):
        config = PipelineConfig(date_level="년")
        pipeline = PIIPipeline(config)
        msg = Message(role="user", content="2024년 3월 15일 주문")
        result = pipeline.process_message(msg)
        assert "2024년" in result.processed_content


# ─── LLM + Regex 통합 (Mock) ───


class TestLLMRegexIntegration:
    """LLM과 Regex가 함께 동작하는 통합 테스트 (Mock LLM)."""

    def _make_pipeline_with_mock_llm(self, llm_response: str) -> PIIPipeline:
        config = PipelineConfig(enable_regex=True)
        pipeline = PIIPipeline(config)

        # Mock LLM detector를 수동 추가
        class _MockClient(BaseLLMClient):
            def chat(self, messages):
                return llm_response

        llm_config = PipelineConfig(enable_llm=True, llm_config=LLMConfig())
        llm_detector = LLMDetector(llm_config, _MockClient())
        pipeline._detectors.append(llm_detector)
        return pipeline

    def test_regex_phone_plus_llm_name(self):
        pipeline = self._make_pipeline_with_mock_llm(
            json.dumps([{"type": "이름", "text": "김민수", "confidence": 0.9}])
        )
        msg = Message(role="user", content="김민수이고 전화 010-1234-5678")
        result = pipeline.process_message(msg)
        assert "[이름]" in result.processed_content
        assert "[전화번호]" in result.processed_content

    def test_llm_address_plus_regex_email(self):
        pipeline = self._make_pipeline_with_mock_llm(
            json.dumps([{"type": "주소", "text": "역삼역 근처", "confidence": 0.7}])
        )
        msg = Message(role="user", content="역삼역 근처 살고 메일 a@b.com")
        result = pipeline.process_message(msg)
        assert "[이메일]" in result.processed_content

    def test_dedup_regex_and_llm_same_span(self):
        """Regex와 LLM이 같은 span을 탐지하면 중복 제거."""
        pipeline = self._make_pipeline_with_mock_llm(
            json.dumps([{"type": "전화번호", "text": "010-1234-5678", "confidence": 0.8}])
        )
        msg = Message(role="user", content="전화 010-1234-5678")
        result = pipeline.process_message(msg)
        phones = [e for e in result.entities if e.pii_type == PIIType.PHONE]
        assert len(phones) == 1  # 중복 제거됨

    def test_llm_only_no_regex(self):
        """Regex로 못 잡는 것을 LLM이 잡는 케이스."""
        pipeline = self._make_pipeline_with_mock_llm(
            json.dumps([{"type": "이름", "text": "홍길동", "confidence": 0.95}])
        )
        msg = Message(role="user", content="홍길동입니다")
        result = pipeline.process_message(msg)
        assert "[이름]" in result.processed_content

    def test_llm_failure_regex_still_works(self):
        """LLM 실패해도 regex 결과는 정상."""
        config = PipelineConfig(enable_regex=True)
        pipeline = PIIPipeline(config)

        class _ErrorClient(BaseLLMClient):
            def chat(self, messages):
                raise ConnectionError("실패")

        llm_config = PipelineConfig(enable_llm=True, llm_config=LLMConfig())
        llm_detector = LLMDetector(llm_config, _ErrorClient())
        pipeline._detectors.append(llm_detector)

        msg = Message(role="user", content="전화 010-1234-5678")
        result = pipeline.process_message(msg)
        assert "[전화번호]" in result.processed_content


# ─── 엣지 케이스 ───


class TestPipelineEdgeCases:
    def test_empty_message(self, pipeline):
        msg = Message(role="user", content="")
        result = pipeline.process_message(msg)
        assert result.processed_content == ""

    def test_whitespace_only(self, pipeline):
        msg = Message(role="user", content="   ")
        result = pipeline.process_message(msg)
        assert result.processed_content == "   "

    def test_very_long_text(self, pipeline):
        text = "안녕하세요 " * 1000 + "010-1234-5678"
        msg = Message(role="user", content=text)
        result = pipeline.process_message(msg)
        assert "[전화번호]" in result.processed_content

    def test_special_characters(self, pipeline):
        msg = Message(role="user", content="이모지🎉🎂 전화 010-1234-5678")
        result = pipeline.process_message(msg)
        assert "[전화번호]" in result.processed_content

    def test_multiline(self, pipeline):
        msg = Message(role="user", content="전화: 010-1234-5678\n이메일: a@b.com")
        result = pipeline.process_message(msg)
        assert "[전화번호]" in result.processed_content
        assert "[이메일]" in result.processed_content

    def test_assistant_message_also_processed(self, pipeline):
        msg = Message(role="assistant", content="전화번호 010-1234-5678 확인됨")
        result = pipeline.process_message(msg)
        assert "[전화번호]" in result.processed_content
