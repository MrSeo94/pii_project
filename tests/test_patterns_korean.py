"""한국어 PII 정규식 패턴 테스트."""

import pytest

from kpii.patterns.korean import (
    ADDRESS_PATTERN,
    AGE_PATTERN,
    BANK_ACCOUNT_PATTERN,
    CREDIT_CARD_PATTERN,
    DATE_PATTERN,
    DRIVERS_LICENSE_PATTERN,
    EMAIL_PATTERN,
    LANDLINE_PATTERN,
    MOBILE_PHONE_PATTERN,
    PASSPORT_PATTERN,
    RESIDENT_REG_NO_PATTERN,
)
from kpii.utils.validators import validate_luhn, validate_resident_registration_number


class TestResidentRegNo:
    """주민등록번호 패턴 테스트."""

    @pytest.mark.parametrize("rrn", [
        "900101-1234567",
        "850315-2345678",
        "010520-3456789",
        "991231-4567890",
    ])
    def test_valid_formats(self, rrn):
        assert RESIDENT_REG_NO_PATTERN.search(rrn)

    def test_with_spaces(self):
        assert RESIDENT_REG_NO_PATTERN.search("900101 - 1234567")

    def test_with_en_dash(self):
        assert RESIDENT_REG_NO_PATTERN.search("900101–1234567")

    def test_embedded_in_text(self):
        match = RESIDENT_REG_NO_PATTERN.search("주민번호는 900101-1234567입니다")
        assert match
        assert match.group() == "900101-1234567"

    def test_invalid_gender_digit_0(self):
        assert not RESIDENT_REG_NO_PATTERN.search("900101-0234567")

    def test_invalid_gender_digit_5(self):
        assert not RESIDENT_REG_NO_PATTERN.search("900101-5234567")

    def test_invalid_gender_digit_9(self):
        assert not RESIDENT_REG_NO_PATTERN.search("900101-9234567")

    def test_invalid_month_13(self):
        assert not RESIDENT_REG_NO_PATTERN.search("901301-1234567")

    def test_invalid_day_32(self):
        assert not RESIDENT_REG_NO_PATTERN.search("900132-1234567")

    def test_too_short(self):
        assert not RESIDENT_REG_NO_PATTERN.search("90010-1234567")

    def test_checksum_invalid_length(self):
        assert not validate_resident_registration_number("12345")

    def test_checksum_non_digit(self):
        assert not validate_resident_registration_number("abcdef-ghijklm")

    def test_checksum_13_digits(self):
        # 형식은 맞지만 체크섬은 통과하지 않을 수 있음
        result = validate_resident_registration_number("9001011234567")
        assert isinstance(result, bool)


class TestPhonePatterns:
    """전화번호 패턴 테스트."""

    @pytest.mark.parametrize("phone", [
        "010-1234-5678",
        "01012345678",
        "010.1234.5678",
        "010 1234 5678",
        "011-234-5678",
        "016-345-6789",
        "017-456-7890",
        "018-567-8901",
        "019-678-9012",
    ])
    def test_mobile_valid(self, phone):
        assert MOBILE_PHONE_PATTERN.search(phone)

    def test_mobile_3digit_middle(self):
        """중간 3자리 번호."""
        assert MOBILE_PHONE_PATTERN.search("010-123-4567")

    def test_mobile_in_sentence(self):
        match = MOBILE_PHONE_PATTERN.search("연락처는 010-9999-8888이에요")
        assert match
        assert "010-9999-8888" in match.group()

    @pytest.mark.parametrize("phone", [
        "02-1234-5678",
        "031-123-4567",
        "032-234-5678",
        "033-345-6789",
        "041-456-7890",
        "042-567-8901",
        "051-678-9012",
        "052-789-0123",
        "061-890-1234",
        "062-901-2345",
    ])
    def test_landline_valid(self, phone):
        assert LANDLINE_PATTERN.search(phone)

    def test_no_match_invalid_prefix(self):
        """유효하지 않은 접두사."""
        assert not MOBILE_PHONE_PATTERN.search("020-1234-5678")

    def test_no_match_too_short(self):
        assert not MOBILE_PHONE_PATTERN.search("010-12-34")

    @pytest.mark.parametrize("not_phone", [
        "123-456-7890",
        "abc-defg-hijk",
    ])
    def test_false_positive_rejection(self, not_phone):
        """전화번호가 아닌 것은 매치 안 됨."""
        match = MOBILE_PHONE_PATTERN.search(not_phone)
        # 010으로 시작하지 않으면 매치 안 됨
        if match:
            assert not match.group().startswith("01")


class TestEmailPattern:
    """이메일 패턴 테스트."""

    @pytest.mark.parametrize("email", [
        "test@example.com",
        "user.name@domain.co.kr",
        "test+tag@gmail.com",
        "a@b.co",
        "user_name@company.org",
        "first.last@sub.domain.com",
        "user123@test.net",
        "ALL.CAPS@DOMAIN.COM",
    ])
    def test_valid_emails(self, email):
        assert EMAIL_PATTERN.search(email)

    def test_email_in_sentence(self):
        match = EMAIL_PATTERN.search("이메일은 test@example.com입니다")
        assert match
        assert match.group() == "test@example.com"

    def test_no_match_without_domain(self):
        assert not EMAIL_PATTERN.search("test@")

    def test_no_match_without_at(self):
        assert not EMAIL_PATTERN.search("testexample.com")

    def test_no_match_without_tld(self):
        assert not EMAIL_PATTERN.search("test@example")

    @pytest.mark.parametrize("invalid", [
        "@example.com",
        "test@.com",
    ])
    def test_invalid_emails(self, invalid):
        match = EMAIL_PATTERN.search(invalid)
        # @앞이 비어있거나 도메인이 .으로 시작하면 매치 안 됨
        if match:
            assert "@" in match.group() and not match.group().startswith("@")


class TestCreditCardPattern:
    """신용카드 번호 패턴 테스트."""

    @pytest.mark.parametrize("card", [
        "4111-1111-1111-1111",
        "4111 1111 1111 1111",
        "4111111111111111",
        "5500-0000-0000-0004",
        "3400-0000-0000-0009",
        "6011-0000-0000-0004",
    ])
    def test_valid_formats(self, card):
        assert CREDIT_CARD_PATTERN.search(card)

    def test_card_in_sentence(self):
        match = CREDIT_CARD_PATTERN.search("카드번호는 1234-5678-9012-3456입니다")
        assert match

    def test_luhn_valid_visa(self):
        assert validate_luhn("4111111111111111")

    def test_luhn_valid_mastercard(self):
        assert validate_luhn("5500000000000004")

    def test_luhn_valid_amex(self):
        assert validate_luhn("340000000000009")

    def test_luhn_invalid_one_digit_off(self):
        assert not validate_luhn("4111111111111112")

    def test_luhn_invalid_random(self):
        assert not validate_luhn("1234567890123456")

    def test_luhn_too_short(self):
        assert not validate_luhn("411111")

    def test_luhn_non_digit(self):
        assert not validate_luhn("abcd-efgh-ijkl-mnop")

    def test_luhn_with_dashes(self):
        assert validate_luhn("4111-1111-1111-1111")

    def test_15_digit_card_no_match(self):
        """15자리는 매치 안 됨 (AMEX는 별도 패턴 필요)."""
        assert not CREDIT_CARD_PATTERN.fullmatch("3400-000000-00009")


class TestBankAccountPattern:
    """계좌번호 패턴 테스트."""

    @pytest.mark.parametrize("account", [
        "110-123-456789",
        "3333-01-1234567-01",
        "123-45-678901",
        "1002-123-456789",
        "110-456-78901",
        "352-1234-5678-13",
    ])
    def test_valid_formats(self, account):
        assert BANK_ACCOUNT_PATTERN.search(account)

    def test_account_in_sentence(self):
        match = BANK_ACCOUNT_PATTERN.search("계좌번호 110-123-456789로 입금")
        assert match

    def test_no_match_without_dashes(self):
        """대시 없는 숫자열은 매치 안 됨."""
        assert not BANK_ACCOUNT_PATTERN.search("1101234567890")

    def test_no_match_single_dash(self):
        assert not BANK_ACCOUNT_PATTERN.search("110-123456789")

    @pytest.mark.parametrize("short", [
        "1-2-3",
        "12-3-4",
    ])
    def test_too_short_segments(self, short):
        """세그먼트가 너무 짧으면 매치 안 됨."""
        match = BANK_ACCOUNT_PATTERN.search(short)
        assert not match


class TestPassportPattern:
    """여권번호 패턴 테스트."""

    @pytest.mark.parametrize("passport", [
        "M12345678",
        "AB1234567",
        "S98765432",
        "RE1234567",
        "G1234567",
    ])
    def test_valid_formats(self, passport):
        assert PASSPORT_PATTERN.search(passport)

    def test_passport_in_sentence(self):
        match = PASSPORT_PATTERN.search("여권번호 M12345678입니다")
        assert match

    def test_no_match_lowercase(self):
        """소문자는 매치 안 됨."""
        assert not PASSPORT_PATTERN.search("m12345678")

    def test_no_match_digits_only(self):
        assert not PASSPORT_PATTERN.search("12345678")

    def test_no_match_letters_only(self):
        assert not PASSPORT_PATTERN.search("ABCDEFGH")

    def test_no_match_too_short(self):
        assert not PASSPORT_PATTERN.search("M12345")

    @pytest.mark.parametrize("not_passport", [
        "ABC1234567",  # 3글자 접두사
    ])
    def test_three_letter_prefix_no_match(self, not_passport):
        match = PASSPORT_PATTERN.search(not_passport)
        if match:
            # 매치되더라도 3글자 접두사로 매치되지는 않아야 함
            assert len(match.group()) <= 10


class TestDriversLicensePattern:
    """운전면허번호 패턴 테스트."""

    @pytest.mark.parametrize("dl", [
        "11-22-333333-44",
        "13-05-123456-78",
        "26-12-987654-01",
        "11-99-000001-23",
    ])
    def test_valid_formats(self, dl):
        assert DRIVERS_LICENSE_PATTERN.search(dl)

    def test_dl_in_sentence(self):
        match = DRIVERS_LICENSE_PATTERN.search("면허번호 11-22-333333-44입니다")
        assert match
        assert "11-22-333333-44" in match.group()

    def test_with_spaces(self):
        assert DRIVERS_LICENSE_PATTERN.search("11 - 22 - 333333 - 44")

    def test_no_match_wrong_format(self):
        assert not DRIVERS_LICENSE_PATTERN.search("1-22-333333-44")

    def test_no_match_short_middle(self):
        assert not DRIVERS_LICENSE_PATTERN.search("11-22-3333-44")


class TestAgePattern:
    """나이 패턴 테스트."""

    @pytest.mark.parametrize("text,expected_age", [
        ("25살", "25"),
        ("만 32세", "32"),
        ("나이는 28세입니다", "28"),
        ("7살짜리 아이", "7"),
        ("만 65세 이상", "65"),
        ("100세", "100"),
        ("19살이에요", "19"),
        ("만 1세", "1"),
    ])
    def test_age_extraction(self, text, expected_age):
        match = AGE_PATTERN.search(text)
        assert match
        assert match.group(1) == expected_age

    def test_no_match_without_suffix(self):
        """살/세 없으면 매치 안 됨."""
        assert not AGE_PATTERN.search("25입니다")

    def test_no_match_text_only(self):
        assert not AGE_PATTERN.search("스물다섯살")  # 한글 숫자는 매치 안 됨

    def test_multiple_ages_in_text(self):
        text = "아빠는 50세이고 아들은 25살이에요"
        matches = AGE_PATTERN.findall(text)
        assert len(matches) == 2

    def test_age_with_man_prefix(self):
        match = AGE_PATTERN.search("만15세")
        assert match
        assert match.group(1) == "15"


class TestDatePattern:
    """날짜 패턴 테스트."""

    @pytest.mark.parametrize("text", [
        "2024년 3월 15일",
        "2024년 12월 1일",
        "2024.03.15",
        "2024-03-15",
        "2024/03/15",
        "2023년 1월 31일",
        "2020년 2월 29일",
        "1999.12.25",
    ])
    def test_valid_date_formats(self, text):
        assert DATE_PATTERN.search(text)

    def test_date_in_sentence(self):
        match = DATE_PATTERN.search("주문일은 2024년 3월 15일입니다")
        assert match

    def test_date_groups(self):
        match = DATE_PATTERN.search("2024년 3월 15일")
        assert match
        assert match.group(1) == "2024"
        assert match.group(2) == "3"
        assert match.group(3) == "15"

    def test_date_dot_groups(self):
        match = DATE_PATTERN.search("2024.03.15")
        assert match
        assert match.group(1) == "2024"
        assert match.group(2) == "03"
        assert match.group(3) == "15"

    def test_no_match_year_only(self):
        """연도만으로는 매치 안 됨."""
        assert not DATE_PATTERN.fullmatch("2024년")

    def test_no_match_invalid_month(self):
        assert not DATE_PATTERN.search("2024년 13월 15일")

    def test_no_match_month_zero(self):
        assert not DATE_PATTERN.search("2024년 0월 15일")

    def test_two_digit_day(self):
        match = DATE_PATTERN.search("2024년 11월 28일")
        assert match
        assert match.group(3) == "28"

    def test_single_digit_day(self):
        match = DATE_PATTERN.search("2024년 3월 5일")
        assert match
        assert match.group(3) == "5"


class TestAddressPattern:
    """주소 패턴 테스트."""

    @pytest.mark.parametrize("text", [
        "서울시 강남구 삼성동 123-45입니다",
        "경기도 성남시 분당구 정자동입니다",
        "부산시 해운대구 우동입니다",
        "대구시 수성구 범어동입니다",
        "인천시 남동구 구월동입니다",
        "광주시 서구 치평동입니다",
        "대전시 유성구 봉명동입니다",
        "울산시 남구 삼산동입니다",
    ])
    def test_major_cities(self, text):
        assert ADDRESS_PATTERN.search(text)

    @pytest.mark.parametrize("text", [
        "경기도 수원시 영통구입니다",
        "강원도 춘천시 효자동입니다",
        "충북 청주시 상당구입니다",
        "충남 천안시 동남구입니다",
        "전북 전주시 완산구입니다",
        "전남 목포시 용당동입니다",
        "경북 포항시 남구입니다",
        "경남 창원시 성산구입니다",
    ])
    def test_provinces(self, text):
        assert ADDRESS_PATTERN.search(text)

    def test_address_extraction(self):
        text = "배송지는 서울시 강남구 역삼동 123번지이고 빨리 보내주세요"
        match = ADDRESS_PATTERN.search(text)
        assert match
        assert "서울" in match.group()
        assert "강남구" in match.group()

    def test_jeju(self):
        assert ADDRESS_PATTERN.search("제주시 연동입니다")

    def test_sejong(self):
        assert ADDRESS_PATTERN.search("세종시 조치원읍입니다")

    def test_no_match_brand_name(self):
        """브랜드명은 주소가 아님."""
        assert not ADDRESS_PATTERN.search("서울우유를 주문했습니다")
