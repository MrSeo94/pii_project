"""LLMDetector 테스트 (모킹)."""

import json

import pytest

from kpii.config import LLMConfig, PipelineConfig
from kpii.detectors.llm_detector import LLMDetector
from kpii.llm.base import BaseLLMClient
from kpii.models import DetectorSource, Message, PIIEntity, PIIType


class MockLLMClient(BaseLLMClient):
    """테스트용 목 LLM 클라이언트."""

    def __init__(self, response: str = "[]"):
        self._response = response
        self.call_count = 0
        self.last_messages = None

    def chat(self, messages: list[dict[str, str]]) -> str:
        self.call_count += 1
        self.last_messages = messages
        return self._response


@pytest.fixture
def config():
    return PipelineConfig(enable_llm=True, llm_config=LLMConfig())


def _mock(response_items: list[dict]) -> MockLLMClient:
    return MockLLMClient(json.dumps(response_items, ensure_ascii=False))


# ─── 이름 탐지 ───


class TestDetectName:
    def test_single_name(self, config):
        client = _mock([{"type": "이름", "text": "김민수", "confidence": 0.95}])
        detector = LLMDetector(config, client)
        entities = detector.detect("저는 김민수입니다")
        assert len(entities) == 1
        assert entities[0].pii_type == PIIType.NAME
        assert entities[0].text == "김민수"
        assert entities[0].score == 0.95

    def test_two_names(self, config):
        client = _mock([
            {"type": "이름", "text": "김민수", "confidence": 0.9},
            {"type": "이름", "text": "이영희", "confidence": 0.85},
        ])
        detector = LLMDetector(config, client)
        entities = detector.detect("김민수님과 이영희님의 주문입니다")
        names = [e for e in entities if e.pii_type == PIIType.NAME]
        assert len(names) == 2

    def test_name_position(self, config):
        client = _mock([{"type": "이름", "text": "박철수", "confidence": 0.9}])
        detector = LLMDetector(config, client)
        entities = detector.detect("주문자: 박철수님")
        assert entities[0].start == 5
        assert entities[0].end == 8

    def test_name_source_is_llm(self, config):
        client = _mock([{"type": "이름", "text": "홍길동", "confidence": 0.9}])
        detector = LLMDetector(config, client)
        entities = detector.detect("홍길동 고객님")
        assert entities[0].source == DetectorSource.LLM

    def test_full_name_4char(self, config):
        client = _mock([{"type": "이름", "text": "남궁민수", "confidence": 0.8}])
        detector = LLMDetector(config, client)
        entities = detector.detect("남궁민수님 안녕하세요")
        assert entities[0].text == "남궁민수"


# ─── 주소 탐지 ───


class TestDetectAddress:
    def test_informal_address(self, config):
        client = _mock([{"type": "주소", "text": "강남역 근처", "confidence": 0.7}])
        detector = LLMDetector(config, client)
        entities = detector.detect("강남역 근처로 보내주세요")
        assert len(entities) == 1
        assert entities[0].pii_type == PIIType.ADDRESS

    def test_delivery_address(self, config):
        client = _mock([{"type": "주소", "text": "해운대 센텀시티 아파트", "confidence": 0.85}])
        detector = LLMDetector(config, client)
        entities = detector.detect("배송지는 해운대 센텀시티 아파트입니다")
        assert entities[0].pii_type == PIIType.ADDRESS


# ─── 복합 탐지 ───


class TestDetectMultiple:
    def test_name_and_address(self, config):
        client = _mock([
            {"type": "이름", "text": "이영희", "confidence": 0.9},
            {"type": "주소", "text": "강남역 근처", "confidence": 0.7},
        ])
        detector = LLMDetector(config, client)
        entities = detector.detect("이영희입니다. 강남역 근처로 보내주세요")
        assert len(entities) == 2
        types = {e.pii_type for e in entities}
        assert PIIType.NAME in types
        assert PIIType.ADDRESS in types

    def test_name_age_address(self, config):
        client = _mock([
            {"type": "이름", "text": "최수진", "confidence": 0.9},
            {"type": "나이", "text": "25살", "confidence": 0.8},
            {"type": "주소", "text": "판교역 근처", "confidence": 0.7},
        ])
        detector = LLMDetector(config, client)
        entities = detector.detect("최수진이고 25살이에요 판교역 근처 살아요")
        assert len(entities) == 3


# ─── 빈/무효 응답 처리 ───


class TestEmptyAndInvalidResponses:
    def test_empty_array(self, config):
        client = MockLLMClient("[]")
        detector = LLMDetector(config, client)
        assert detector.detect("안녕하세요") == []

    def test_invalid_json(self, config):
        client = MockLLMClient("이것은 유효하지 않은 JSON")
        detector = LLMDetector(config, client)
        assert detector.detect("테스트") == []

    def test_partial_json(self, config):
        client = MockLLMClient('[{"type": "이름"')
        detector = LLMDetector(config, client)
        assert detector.detect("테스트") == []

    def test_empty_string_response(self, config):
        client = MockLLMClient("")
        detector = LLMDetector(config, client)
        assert detector.detect("테스트") == []

    def test_null_response(self, config):
        client = MockLLMClient("null")
        detector = LLMDetector(config, client)
        assert detector.detect("테스트") == []

    def test_markdown_code_block(self, config):
        client = MockLLMClient(
            '```json\n[{"type": "이름", "text": "박철수", "confidence": 0.9}]\n```'
        )
        detector = LLMDetector(config, client)
        entities = detector.detect("박철수님 안녕하세요")
        assert len(entities) == 1

    def test_markdown_no_lang(self, config):
        client = MockLLMClient(
            '```\n[{"type": "이름", "text": "김영수", "confidence": 0.9}]\n```'
        )
        detector = LLMDetector(config, client)
        entities = detector.detect("김영수님 주문 확인")
        assert len(entities) == 1


# ─── 텍스트 매칭 실패 ───


class TestTextNotFound:
    def test_text_not_in_original(self, config):
        client = _mock([{"type": "이름", "text": "존재안함", "confidence": 0.9}])
        detector = LLMDetector(config, client)
        assert detector.detect("안녕하세요") == []

    def test_partial_match_not_found(self, config):
        client = _mock([{"type": "이름", "text": "김민수님", "confidence": 0.9}])
        detector = LLMDetector(config, client)
        entities = detector.detect("김민수 고객님")
        # "김민수님"은 원문에 없으므로 탐지 안 됨
        assert len(entities) == 0

    def test_one_found_one_not(self, config):
        client = _mock([
            {"type": "이름", "text": "김민수", "confidence": 0.9},
            {"type": "이름", "text": "없는이름", "confidence": 0.8},
        ])
        detector = LLMDetector(config, client)
        entities = detector.detect("김민수입니다")
        assert len(entities) == 1
        assert entities[0].text == "김민수"


# ─── 타입 매핑 ───


class TestTypeMapping:
    @pytest.mark.parametrize("llm_type,expected_pii_type", [
        ("이름", PIIType.NAME),
        ("주소", PIIType.ADDRESS),
        ("나이", PIIType.AGE),
        ("날짜", PIIType.DATE),
        ("전화번호", PIIType.PHONE),
        ("이메일", PIIType.EMAIL),
    ])
    def test_type_maps_correctly(self, config, llm_type, expected_pii_type):
        client = _mock([{"type": llm_type, "text": "테스트", "confidence": 0.9}])
        detector = LLMDetector(config, client)
        entities = detector.detect("테스트 문장")
        assert len(entities) == 1
        assert entities[0].pii_type == expected_pii_type

    def test_unknown_type_ignored(self, config):
        client = _mock([{"type": "알수없는타입", "text": "뭔가", "confidence": 0.9}])
        detector = LLMDetector(config, client)
        assert detector.detect("뭔가 있음") == []


# ─── 에러 처리 ───


class TestErrorHandling:
    def test_connection_error(self, config):
        class ErrorClient(BaseLLMClient):
            def chat(self, messages):
                raise ConnectionError("API 오류")

        detector = LLMDetector(config, ErrorClient())
        assert detector.detect("테스트") == []

    def test_timeout_error(self, config):
        class TimeoutClient(BaseLLMClient):
            def chat(self, messages):
                raise TimeoutError("시간 초과")

        detector = LLMDetector(config, TimeoutClient())
        assert detector.detect("테스트") == []

    def test_generic_exception(self, config):
        class GenericErrorClient(BaseLLMClient):
            def chat(self, messages):
                raise RuntimeError("알 수 없는 오류")

        detector = LLMDetector(config, GenericErrorClient())
        assert detector.detect("테스트") == []


# ─── 문맥 전달 ───


class TestContextPassing:
    def test_context_included_in_prompt(self, config):
        client = MockLLMClient("[]")
        detector = LLMDetector(config, client)
        context = [
            Message(role="user", content="주문 확인해주세요"),
            Message(role="assistant", content="성함을 알려주세요"),
        ]
        detector.detect("김민수입니다", context=context)
        # 프롬프트에 문맥이 포함되었는지 확인
        assert client.call_count == 1
        prompt_text = " ".join(m["content"] for m in client.last_messages)
        assert "주문 확인" in prompt_text

    def test_already_detected_passed(self, config):
        client = MockLLMClient("[]")
        detector = LLMDetector(config, client)
        already = [PIIEntity(PIIType.PHONE, 0, 13, "010-1234-5678")]
        detector.detect("010-1234-5678 김민수", already_detected=already)
        prompt_text = " ".join(m["content"] for m in client.last_messages)
        assert "010-1234-5678" in prompt_text

    def test_no_context(self, config):
        client = MockLLMClient("[]")
        detector = LLMDetector(config, client)
        detector.detect("테스트")
        assert client.call_count == 1


# ─── PII 타입 필터링 ───


class TestPIITypeFiltering:
    def test_disabled_type_filtered(self):
        config = PipelineConfig(
            enable_llm=True,
            llm_config=LLMConfig(),
            enabled_pii_types={PIIType.PHONE},  # 이름 비활성화
        )
        client = _mock([{"type": "이름", "text": "김민수", "confidence": 0.9}])
        detector = LLMDetector(config, client)
        entities = detector.detect("김민수입니다")
        assert len(entities) == 0

    def test_enabled_type_passes(self):
        config = PipelineConfig(
            enable_llm=True,
            llm_config=LLMConfig(),
            enabled_pii_types={PIIType.NAME},
        )
        client = _mock([{"type": "이름", "text": "김민수", "confidence": 0.9}])
        detector = LLMDetector(config, client)
        entities = detector.detect("김민수입니다")
        assert len(entities) == 1
