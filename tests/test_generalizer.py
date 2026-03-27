"""Generalizer 프로세서 테스트."""

import pytest

from kpii.config import PipelineConfig
from kpii.models import PIIEntity, PIIType
from kpii.processors.generalizer import Generalizer


@pytest.fixture
def generalizer(default_config):
    return Generalizer(default_config)


def _entity(pii_type, start, end, text):
    return PIIEntity(pii_type=pii_type, start=start, end=end, text=text)


# ─── 나이 일반화 ───


class TestGeneralizeAge:
    def test_20s(self, generalizer):
        text = "25살"
        entities = [_entity(PIIType.AGE, 0, 3, "25살")]
        assert "20대" in generalizer.process(text, entities)

    def test_30s_se(self, generalizer):
        text = "만 32세"
        entities = [_entity(PIIType.AGE, 0, 5, "만 32세")]
        assert "30대" in generalizer.process(text, entities)

    def test_teenager(self, generalizer):
        text = "15살"
        entities = [_entity(PIIType.AGE, 0, 3, "15살")]
        assert "10대" in generalizer.process(text, entities)

    def test_child_under_10(self, generalizer):
        text = "7살"
        entities = [_entity(PIIType.AGE, 0, 2, "7살")]
        assert "0대" in generalizer.process(text, entities)

    def test_60s(self, generalizer):
        text = "만 65세"
        entities = [_entity(PIIType.AGE, 0, 5, "만 65세")]
        assert "60대" in generalizer.process(text, entities)

    def test_100(self, generalizer):
        text = "100세"
        entities = [_entity(PIIType.AGE, 0, 4, "100세")]
        assert "100대" in generalizer.process(text, entities)

    def test_exact_decade_boundary(self, generalizer):
        text = "30살"
        entities = [_entity(PIIType.AGE, 0, 3, "30살")]
        assert "30대" in generalizer.process(text, entities)

    def test_age_in_sentence(self, generalizer):
        text = "저는 만 28세입니다"
        entities = [_entity(PIIType.AGE, 3, 8, "만 28세")]
        result = generalizer.process(text, entities)
        assert "20대" in result
        assert "28" not in result

    def test_custom_bucket_size_5(self):
        config = PipelineConfig(age_bucket_size=5)
        gen = Generalizer(config)
        text = "23살"
        entities = [_entity(PIIType.AGE, 0, 3, "23살")]
        assert "20대" in gen.process(text, entities)

    def test_custom_bucket_size_5_boundary(self):
        config = PipelineConfig(age_bucket_size=5)
        gen = Generalizer(config)
        text = "27살"
        entities = [_entity(PIIType.AGE, 0, 3, "27살")]
        assert "25대" in gen.process(text, entities)

    def test_1se(self, generalizer):
        text = "만 1세"
        entities = [_entity(PIIType.AGE, 0, 4, "만 1세")]
        assert "0대" in generalizer.process(text, entities)

    def test_49sal(self, generalizer):
        text = "49살"
        entities = [_entity(PIIType.AGE, 0, 3, "49살")]
        assert "40대" in generalizer.process(text, entities)


# ─── 주소 일반화 ───


class TestGeneralizeAddress:
    def test_seoul_gangnam(self, generalizer):
        text = "서울시 강남구 삼성동 123-45"
        entities = [_entity(PIIType.ADDRESS, 0, len(text), text)]
        result = generalizer.process(text, entities)
        assert "서울 강남구" in result
        assert "삼성동" not in result

    def test_gyeonggi_seongnam(self, generalizer):
        text = "경기도 성남시 분당구 정자동"
        entities = [_entity(PIIType.ADDRESS, 0, len(text), text)]
        result = generalizer.process(text, entities)
        assert "경기" in result

    def test_busan(self, generalizer):
        text = "부산시 해운대구 우동"
        entities = [_entity(PIIType.ADDRESS, 0, len(text), text)]
        result = generalizer.process(text, entities)
        assert "부산 해운대구" in result
        assert "우동" not in result

    def test_daegu(self, generalizer):
        text = "대구시 수성구 범어동 55"
        entities = [_entity(PIIType.ADDRESS, 0, len(text), text)]
        result = generalizer.process(text, entities)
        assert "대구 수성구" in result
        assert "범어동" not in result

    def test_incheon(self, generalizer):
        text = "인천시 남동구 구월동"
        entities = [_entity(PIIType.ADDRESS, 0, len(text), text)]
        result = generalizer.process(text, entities)
        assert "인천 남동구" in result

    def test_gwangju(self, generalizer):
        text = "광주시 서구 치평동"
        entities = [_entity(PIIType.ADDRESS, 0, len(text), text)]
        result = generalizer.process(text, entities)
        assert "광주 서구" in result

    def test_daejeon(self, generalizer):
        text = "대전시 유성구 봉명동"
        entities = [_entity(PIIType.ADDRESS, 0, len(text), text)]
        result = generalizer.process(text, entities)
        assert "대전 유성구" in result

    def test_ulsan(self, generalizer):
        text = "울산시 남구 삼산동"
        entities = [_entity(PIIType.ADDRESS, 0, len(text), text)]
        result = generalizer.process(text, entities)
        assert "울산 남구" in result

    def test_seoul_with_suffix(self, generalizer):
        text = "서울특별시 종로구 혜화동"
        entities = [_entity(PIIType.ADDRESS, 0, len(text), text)]
        result = generalizer.process(text, entities)
        assert "서울 종로구" in result
        assert "혜화동" not in result

    def test_busan_gwangyeoksi(self, generalizer):
        text = "부산광역시 중구 남포동"
        entities = [_entity(PIIType.ADDRESS, 0, len(text), text)]
        result = generalizer.process(text, entities)
        assert "부산 중구" in result

    def test_gyeonggi_gun(self, generalizer):
        text = "경기도 양평군 옥천면"
        entities = [_entity(PIIType.ADDRESS, 0, len(text), text)]
        result = generalizer.process(text, entities)
        assert "경기 양평군" in result

    def test_address_in_sentence(self, generalizer):
        text = "서울시 강남구 역삼동 789-12"
        entities = [_entity(PIIType.ADDRESS, 0, len(text), text)]
        result = generalizer.process(text, entities)
        assert "789-12" not in result

    def test_sido_only_fallback(self, generalizer):
        """시/군/구 없으면 시/도만 반환."""
        text = "제주"
        entities = [_entity(PIIType.ADDRESS, 0, 2, "제주")]
        result = generalizer.process(text, entities)
        assert "제주" in result


# ─── 날짜 일반화 ───


class TestGeneralizeDate:
    def test_korean_date(self, generalizer):
        text = "2024년 3월 15일"
        entities = [_entity(PIIType.DATE, 0, len(text), text)]
        result = generalizer.process(text, entities)
        assert "2024년 3월" in result
        assert "15일" not in result

    def test_dot_date(self, generalizer):
        text = "2024.03.15"
        entities = [_entity(PIIType.DATE, 0, len(text), text)]
        result = generalizer.process(text, entities)
        assert "2024년 3월" in result

    def test_dash_date(self, generalizer):
        text = "2024-12-25"
        entities = [_entity(PIIType.DATE, 0, len(text), text)]
        result = generalizer.process(text, entities)
        assert "2024년 12월" in result

    def test_january(self, generalizer):
        text = "2024년 1월 1일"
        entities = [_entity(PIIType.DATE, 0, len(text), text)]
        result = generalizer.process(text, entities)
        assert "2024년 1월" in result

    def test_december(self, generalizer):
        text = "2023년 12월 31일"
        entities = [_entity(PIIType.DATE, 0, len(text), text)]
        result = generalizer.process(text, entities)
        assert "2023년 12월" in result

    def test_year_level(self):
        config = PipelineConfig(date_level="년")
        gen = Generalizer(config)
        text = "2024년 3월 15일"
        entities = [_entity(PIIType.DATE, 0, len(text), text)]
        result = gen.process(text, entities)
        assert result == "2024년"

    def test_year_level_dot_format(self):
        config = PipelineConfig(date_level="년")
        gen = Generalizer(config)
        text = "2024.06.15"
        entities = [_entity(PIIType.DATE, 0, len(text), text)]
        result = gen.process(text, entities)
        assert result == "2024년"

    def test_date_in_sentence(self, generalizer):
        text = "2024년 3월 15일"
        entities = [_entity(PIIType.DATE, 0, len(text), text)]
        result = generalizer.process(text, entities)
        assert "2024년 3월" == result

    def test_old_date(self, generalizer):
        text = "1990.01.15"
        entities = [_entity(PIIType.DATE, 0, len(text), text)]
        result = generalizer.process(text, entities)
        assert "1990년 1월" in result

    def test_future_date(self, generalizer):
        text = "2030년 6월 1일"
        entities = [_entity(PIIType.DATE, 0, len(text), text)]
        result = generalizer.process(text, entities)
        assert "2030년 6월" in result


# ─── 직접식별자 무시 ───


class TestSkipDirectIdentifiers:
    def test_skip_phone(self, generalizer):
        text = "전화 010-1234-5678"
        entities = [_entity(PIIType.PHONE, 3, 16, "010-1234-5678")]
        assert generalizer.process(text, entities) == text

    def test_skip_email(self, generalizer):
        text = "test@example.com"
        entities = [_entity(PIIType.EMAIL, 0, 16, "test@example.com")]
        assert generalizer.process(text, entities) == text

    def test_skip_credit_card(self, generalizer):
        text = "4111-1111-1111-1111"
        entities = [_entity(PIIType.CREDIT_CARD, 0, 19, text)]
        assert generalizer.process(text, entities) == text

    def test_skip_rrn(self, generalizer):
        text = "900101-1234567"
        entities = [_entity(PIIType.RESIDENT_REG_NO, 0, 14, text)]
        assert generalizer.process(text, entities) == text

    def test_skip_all_direct_types(self, generalizer):
        """모든 직접식별자 타입이 무시되는지."""
        for pii_type in [
            PIIType.PHONE, PIIType.EMAIL, PIIType.CREDIT_CARD,
            PIIType.RESIDENT_REG_NO, PIIType.BANK_ACCOUNT,
            PIIType.PASSPORT, PIIType.DRIVERS_LICENSE, PIIType.NAME,
        ]:
            text = "테스트"
            entities = [_entity(pii_type, 0, 3, "테스트")]
            assert generalizer.process(text, entities) == text


# ─── 엣지 케이스 ───


class TestGeneralizerEdgeCases:
    def test_no_entities(self, generalizer):
        assert generalizer.process("안녕하세요", []) == "안녕하세요"

    def test_empty_text(self, generalizer):
        assert generalizer.process("", []) == ""

    def test_multiple_quasi_identifiers(self, generalizer):
        text = "25살 서울시 강남구 삼성동"
        entities = [
            _entity(PIIType.AGE, 0, 3, "25살"),
            _entity(PIIType.ADDRESS, 4, len(text), "서울시 강남구 삼성동"),
        ]
        result = generalizer.process(text, entities)
        assert "20대" in result
        assert "서울 강남구" in result
        assert "삼성동" not in result
