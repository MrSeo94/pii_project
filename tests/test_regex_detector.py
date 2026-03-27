"""RegexDetector 테스트."""

import pytest

from kpii.config import PipelineConfig
from kpii.detectors.regex_detector import RegexDetector
from kpii.models import PIIType


@pytest.fixture
def detector(default_config):
    return RegexDetector(default_config)


class TestDetectPhone:
    def test_mobile_with_dashes(self, detector):
        entities = detector.detect("전화번호는 010-1234-5678입니다")
        phones = [e for e in entities if e.pii_type == PIIType.PHONE]
        assert len(phones) >= 1
        assert "010-1234-5678" in phones[0].text

    def test_mobile_no_dashes(self, detector):
        entities = detector.detect("연락처 01098765432")
        phones = [e for e in entities if e.pii_type == PIIType.PHONE]
        assert len(phones) >= 1

    def test_mobile_with_dots(self, detector):
        entities = detector.detect("010.1234.5678로 전화주세요")
        phones = [e for e in entities if e.pii_type == PIIType.PHONE]
        assert len(phones) >= 1

    def test_landline_seoul(self, detector):
        entities = detector.detect("서울 사무실 02-1234-5678")
        phones = [e for e in entities if e.pii_type == PIIType.PHONE]
        assert len(phones) >= 1

    def test_landline_gyeonggi(self, detector):
        entities = detector.detect("경기 031-123-4567")
        phones = [e for e in entities if e.pii_type == PIIType.PHONE]
        assert len(phones) >= 1

    def test_multiple_phones(self, detector):
        entities = detector.detect("집 02-111-2222 핸드폰 010-3333-4444")
        phones = [e for e in entities if e.pii_type == PIIType.PHONE]
        assert len(phones) >= 2

    def test_phone_entity_fields(self, detector):
        entities = detector.detect("010-1234-5678")
        phones = [e for e in entities if e.pii_type == PIIType.PHONE]
        assert phones[0].score > 0
        assert phones[0].start >= 0
        assert phones[0].end > phones[0].start


class TestDetectEmail:
    def test_basic_email(self, detector):
        entities = detector.detect("이메일은 test@example.com입니다")
        emails = [e for e in entities if e.pii_type == PIIType.EMAIL]
        assert len(emails) == 1
        assert emails[0].text == "test@example.com"

    def test_korean_domain(self, detector):
        entities = detector.detect("user@naver.com으로 보내주세요")
        emails = [e for e in entities if e.pii_type == PIIType.EMAIL]
        assert len(emails) == 1

    def test_complex_email(self, detector):
        entities = detector.detect("my.name+tag@company.co.kr")
        emails = [e for e in entities if e.pii_type == PIIType.EMAIL]
        assert len(emails) == 1

    def test_email_score(self, detector):
        entities = detector.detect("a@b.com")
        emails = [e for e in entities if e.pii_type == PIIType.EMAIL]
        assert len(emails) == 1
        assert emails[0].score >= 0.9


class TestDetectCreditCard:
    def test_visa_with_dashes(self, detector):
        entities = detector.detect("카드번호 4111-1111-1111-1111로 결제해주세요")
        cards = [e for e in entities if e.pii_type == PIIType.CREDIT_CARD]
        assert len(cards) == 1

    def test_invalid_luhn_lower_score(self, detector):
        """Luhn 검증 실패 시 낮은 score."""
        entities = detector.detect("카드 1234-5678-9012-3456")
        cards = [e for e in entities if e.pii_type == PIIType.CREDIT_CARD]
        if cards:
            assert cards[0].score < 0.9  # 체크섬 실패로 낮은 점수

    def test_card_no_delimiter(self, detector):
        entities = detector.detect("4111111111111111 결제")
        cards = [e for e in entities if e.pii_type == PIIType.CREDIT_CARD]
        assert len(cards) == 1


class TestDetectResidentRegNo:
    def test_standard_rrn(self, detector):
        entities = detector.detect("주민번호: 850315-2345678")
        rrn = [e for e in entities if e.pii_type == PIIType.RESIDENT_REG_NO]
        assert len(rrn) == 1

    def test_rrn_checksum_fail_still_detected(self, detector):
        """체크섬 실패해도 낮은 score로 탐지."""
        entities = detector.detect("주민번호는 900101-1234567이에요")
        rrn = [e for e in entities if e.pii_type == PIIType.RESIDENT_REG_NO]
        assert len(rrn) == 1
        assert rrn[0].score < 0.9  # 체크섬 실패 → 낮은 점수


class TestDetectBankAccount:
    def test_with_context_keyword(self, detector):
        entities = detector.detect("국민은행 계좌 110-123-456789로 입금해주세요")
        accounts = [e for e in entities if e.pii_type == PIIType.BANK_ACCOUNT]
        assert len(accounts) >= 1

    def test_with_transfer_keyword(self, detector):
        entities = detector.detect("송금 부탁합니다 352-1234-5678-13")
        accounts = [e for e in entities if e.pii_type == PIIType.BANK_ACCOUNT]
        assert len(accounts) >= 1

    def test_with_bank_name_keyword(self, detector):
        entities = detector.detect("신한 110-123-456789")
        accounts = [e for e in entities if e.pii_type == PIIType.BANK_ACCOUNT]
        assert len(accounts) >= 1

    def test_no_context_no_detect(self, detector):
        entities = detector.detect("번호는 110-123-456789입니다")
        accounts = [e for e in entities if e.pii_type == PIIType.BANK_ACCOUNT]
        assert len(accounts) == 0

    def test_far_keyword_no_detect(self, detector):
        """키워드가 너무 멀면 탐지 안 됨."""
        entities = detector.detect(
            "계좌로 보내주세요. " + "x" * 100 + " 110-123-456789"
        )
        accounts = [e for e in entities if e.pii_type == PIIType.BANK_ACCOUNT]
        assert len(accounts) == 0


class TestDetectQuasiIdentifiers:
    def test_age(self, detector):
        entities = detector.detect("나이는 만 25세입니다")
        ages = [e for e in entities if e.pii_type == PIIType.AGE]
        assert len(ages) == 1

    def test_date(self, detector):
        entities = detector.detect("2024년 3월 15일에 주문")
        dates = [e for e in entities if e.pii_type == PIIType.DATE]
        assert len(dates) == 1

    def test_address(self, detector):
        entities = detector.detect("서울시 강남구 삼성동 123입니다")
        addrs = [e for e in entities if e.pii_type == PIIType.ADDRESS]
        assert len(addrs) >= 1


class TestDetectorConfig:
    def test_disabled_pii_type(self, default_config):
        config = PipelineConfig(enabled_pii_types={PIIType.EMAIL})
        detector = RegexDetector(config)
        entities = detector.detect("전화 010-1234-5678 이메일 test@example.com")
        types_found = {e.pii_type for e in entities}
        assert PIIType.PHONE not in types_found
        assert PIIType.EMAIL in types_found

    def test_only_phone_enabled(self):
        config = PipelineConfig(enabled_pii_types={PIIType.PHONE})
        detector = RegexDetector(config)
        entities = detector.detect("전화 010-1234-5678 이메일 test@example.com")
        types_found = {e.pii_type for e in entities}
        assert PIIType.PHONE in types_found
        assert PIIType.EMAIL not in types_found

    def test_all_types_enabled_by_default(self, detector):
        text = "010-1234-5678 test@example.com 만 25세"
        entities = detector.detect(text)
        types_found = {e.pii_type for e in entities}
        assert PIIType.PHONE in types_found
        assert PIIType.EMAIL in types_found
        assert PIIType.AGE in types_found

    def test_custom_context_window(self):
        config = PipelineConfig(context_window_chars=5)
        detector = RegexDetector(config)
        # 키워드가 가까이 있으면 탐지
        entities = detector.detect("계좌 110-123-456789")
        accounts = [e for e in entities if e.pii_type == PIIType.BANK_ACCOUNT]
        assert len(accounts) >= 1


class TestEdgeCases:
    def test_empty_text(self, detector):
        assert detector.detect("") == []

    def test_no_pii(self, detector):
        entities = detector.detect("오늘 날씨가 좋네요. 택배 언제 올까요?")
        direct = [
            e for e in entities
            if e.pii_type in {PIIType.PHONE, PIIType.EMAIL, PIIType.CREDIT_CARD}
        ]
        assert len(direct) == 0

    def test_unicode_text(self, detector):
        """유니코드 특수문자 포함 텍스트."""
        entities = detector.detect("이모지🎉 포함 010-1234-5678")
        phones = [e for e in entities if e.pii_type == PIIType.PHONE]
        assert len(phones) >= 1

    def test_multiline_text(self, detector):
        text = "전화: 010-1234-5678\n이메일: test@example.com"
        entities = detector.detect(text)
        types_found = {e.pii_type for e in entities}
        assert PIIType.PHONE in types_found
        assert PIIType.EMAIL in types_found

    def test_repeated_pii(self, detector):
        text = "010-1234-5678 다시 말씀드리면 010-1234-5678"
        entities = detector.detect(text)
        phones = [e for e in entities if e.pii_type == PIIType.PHONE]
        assert len(phones) == 2

    def test_adjacent_pii(self, detector):
        text = "010-1234-5678/test@example.com"
        entities = detector.detect(text)
        assert len(entities) >= 2
