"""Masker 프로세서 테스트."""

import pytest

from kpii.config import PipelineConfig
from kpii.models import DetectorSource, PIIEntity, PIIType
from kpii.processors.masker import Masker


@pytest.fixture
def masker(default_config):
    return Masker(default_config)


def _entity(pii_type, start, end, text, score=1.0):
    """테스트용 PIIEntity 헬퍼."""
    return PIIEntity(pii_type=pii_type, start=start, end=end, text=text, score=score)


class TestMaskPhone:
    def test_single_phone(self, masker):
        text = "전화번호는 010-1234-5678입니다"
        entities = [_entity(PIIType.PHONE, 6, 19, "010-1234-5678")]
        result = masker.process(text, entities)
        assert "[전화번호]" in result
        assert "010-1234-5678" not in result

    def test_phone_at_start(self, masker):
        text = "010-1234-5678로 연락주세요"
        entities = [_entity(PIIType.PHONE, 0, 13, "010-1234-5678")]
        result = masker.process(text, entities)
        assert result.startswith("[전화번호]")

    def test_phone_at_end(self, masker):
        text = "연락처: 010-1234-5678"
        entities = [_entity(PIIType.PHONE, 5, 18, "010-1234-5678")]
        result = masker.process(text, entities)
        assert result.endswith("[전화번호]")

    def test_two_phones(self, masker):
        text = "집 02-111-2222 핸드폰 010-3333-4444"
        entities = [
            _entity(PIIType.PHONE, 2, 13, "02-111-2222"),
            _entity(PIIType.PHONE, 18, 31, "010-3333-4444"),
        ]
        result = masker.process(text, entities)
        assert result.count("[전화번호]") == 2


class TestMaskEmail:
    def test_single_email(self, masker):
        text = "이메일은 test@example.com입니다"
        entities = [_entity(PIIType.EMAIL, 5, 21, "test@example.com")]
        result = masker.process(text, entities)
        assert "[이메일]" in result
        assert "test@example.com" not in result

    def test_email_only(self, masker):
        text = "test@example.com"
        entities = [_entity(PIIType.EMAIL, 0, 16, "test@example.com")]
        result = masker.process(text, entities)
        assert result == "[이메일]"

    def test_long_email(self, masker):
        text = "메일: very.long.email+tag@subdomain.company.co.kr"
        email = "very.long.email+tag@subdomain.company.co.kr"
        entities = [_entity(PIIType.EMAIL, 4, 4 + len(email), email)]
        result = masker.process(text, entities)
        assert "[이메일]" in result
        assert email not in result


class TestMaskCreditCard:
    def test_card_with_dashes(self, masker):
        text = "카드 4111-1111-1111-1111 결제"
        entities = [_entity(PIIType.CREDIT_CARD, 3, 22, "4111-1111-1111-1111")]
        result = masker.process(text, entities)
        assert "[신용카드번호]" in result

    def test_card_no_delimiter(self, masker):
        text = "4111111111111111"
        entities = [_entity(PIIType.CREDIT_CARD, 0, 16, "4111111111111111")]
        result = masker.process(text, entities)
        assert result == "[신용카드번호]"


class TestMaskResidentRegNo:
    def test_rrn(self, masker):
        text = "주민번호: 900101-1234567"
        entities = [_entity(PIIType.RESIDENT_REG_NO, 6, 20, "900101-1234567")]
        result = masker.process(text, entities)
        assert "[주민등록번호]" in result
        assert "900101" not in result


class TestMaskBankAccount:
    def test_bank_account(self, masker):
        text = "계좌 110-123-456789"
        entities = [_entity(PIIType.BANK_ACCOUNT, 3, 17, "110-123-456789")]
        result = masker.process(text, entities)
        assert "[계좌번호]" in result


class TestMaskPassport:
    def test_passport(self, masker):
        text = "여권번호 M12345678"
        entities = [_entity(PIIType.PASSPORT, 5, 14, "M12345678")]
        result = masker.process(text, entities)
        assert "[여권번호]" in result


class TestMaskDriversLicense:
    def test_drivers_license(self, masker):
        text = "면허 11-22-333333-44"
        entities = [_entity(PIIType.DRIVERS_LICENSE, 3, 18, "11-22-333333-44")]
        result = masker.process(text, entities)
        assert "[운전면허번호]" in result


class TestMaskName:
    def test_name(self, masker):
        text = "성함은 김민수입니다"
        entities = [_entity(PIIType.NAME, 4, 7, "김민수")]
        result = masker.process(text, entities)
        assert "[이름]" in result
        assert "김민수" not in result


class TestMaskMultipleTypes:
    def test_phone_and_email(self, masker):
        text = "전화 010-1234-5678 이메일 test@example.com"
        entities = [
            _entity(PIIType.PHONE, 3, 16, "010-1234-5678"),
            _entity(PIIType.EMAIL, 20, 36, "test@example.com"),
        ]
        result = masker.process(text, entities)
        assert "[전화번호]" in result
        assert "[이메일]" in result

    def test_three_types(self, masker):
        text = "전화 010-1111-2222 메일 a@b.com 카드 4111-1111-1111-1111"
        entities = [
            _entity(PIIType.PHONE, 3, 16, "010-1111-2222"),
            _entity(PIIType.EMAIL, 20, 27, "a@b.com"),
            _entity(PIIType.CREDIT_CARD, 31, 50, "4111-1111-1111-1111"),
        ]
        result = masker.process(text, entities)
        assert "[전화번호]" in result
        assert "[이메일]" in result
        assert "[신용카드번호]" in result

    def test_all_direct_types(self, masker):
        """모든 직접식별자 타입이 마스킹되는지."""
        for pii_type in [
            PIIType.PHONE, PIIType.EMAIL, PIIType.CREDIT_CARD,
            PIIType.RESIDENT_REG_NO, PIIType.BANK_ACCOUNT,
            PIIType.PASSPORT, PIIType.DRIVERS_LICENSE, PIIType.NAME,
        ]:
            entities = [_entity(pii_type, 0, 5, "12345")]
            result = masker.process("12345", entities)
            assert f"[{pii_type.value}]" in result


class TestMaskSkipsQuasiIdentifiers:
    def test_skip_age(self, masker):
        text = "나이는 25살입니다"
        entities = [_entity(PIIType.AGE, 4, 7, "25살")]
        assert masker.process(text, entities) == text

    def test_skip_address(self, masker):
        text = "서울시 강남구"
        entities = [_entity(PIIType.ADDRESS, 0, 7, "서울시 강남구")]
        assert masker.process(text, entities) == text

    def test_skip_date(self, masker):
        text = "2024년 3월 15일"
        entities = [_entity(PIIType.DATE, 0, 12, "2024년 3월 15일")]
        assert masker.process(text, entities) == text


class TestMaskEdgeCases:
    def test_no_entities(self, masker):
        assert masker.process("안녕하세요", []) == "안녕하세요"

    def test_empty_text(self, masker):
        assert masker.process("", []) == ""

    def test_custom_mask_format(self):
        config = PipelineConfig(mask_format="***{pii_type}***")
        masker = Masker(config)
        text = "전화 010-1234-5678"
        entities = [_entity(PIIType.PHONE, 3, 16, "010-1234-5678")]
        result = masker.process(text, entities)
        assert "***전화번호***" in result

    def test_mask_format_brackets(self):
        config = PipelineConfig(mask_format="<{pii_type}>")
        masker = Masker(config)
        entities = [_entity(PIIType.EMAIL, 0, 5, "a@b.c")]
        result = masker.process("a@b.c", entities)
        assert result == "<이메일>"

    def test_entity_at_exact_boundaries(self, masker):
        """텍스트 전체가 하나의 엔티티."""
        text = "010-1234-5678"
        entities = [_entity(PIIType.PHONE, 0, 13, text)]
        result = masker.process(text, entities)
        assert result == "[전화번호]"

    def test_preserves_surrounding_text(self, masker):
        text = "앞 010-1234-5678 뒤"
        entities = [_entity(PIIType.PHONE, 2, 15, "010-1234-5678")]
        result = masker.process(text, entities)
        assert result.startswith("앞 ")
        assert result.endswith(" 뒤")

    def test_unicode_surrounding(self, masker):
        text = "🎉010-1234-5678🎂"
        entities = [_entity(PIIType.PHONE, 1, 14, "010-1234-5678")]
        result = masker.process(text, entities)
        assert "[전화번호]" in result

    def test_newline_in_text(self, masker):
        text = "전화:\n010-1234-5678"
        entities = [_entity(PIIType.PHONE, 4, 17, "010-1234-5678")]
        result = masker.process(text, entities)
        assert "[전화번호]" in result
        assert "\n" in result

    def test_mask_with_hash_format(self):
        config = PipelineConfig(mask_format="#{pii_type}#")
        masker = Masker(config)
        entities = [_entity(PIIType.PHONE, 0, 5, "12345")]
        assert masker.process("12345", entities) == "#전화번호#"

    def test_consecutive_entities(self, masker):
        text = "010-1234-5678test@a.com"
        entities = [
            _entity(PIIType.PHONE, 0, 13, "010-1234-5678"),
            _entity(PIIType.EMAIL, 13, 23, "test@a.com"),
        ]
        result = masker.process(text, entities)
        assert "[전화번호]" in result
        assert "[이메일]" in result
