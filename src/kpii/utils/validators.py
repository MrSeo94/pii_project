"""체크섬 검증 유틸리티."""


def validate_resident_registration_number(digits: str) -> bool:
    """주민등록번호 13자리 체크섬 검증.

    가중치: 2,3,4,5,6,7,8,9,2,3,4,5
    (가중합 % 11)을 11에서 뺀 값의 끝자리 == 마지막 자리
    """
    clean = digits.replace("-", "").replace(" ", "").replace("–", "")
    if len(clean) != 13 or not clean.isdigit():
        return False

    weights = [2, 3, 4, 5, 6, 7, 8, 9, 2, 3, 4, 5]
    total = sum(int(clean[i]) * weights[i] for i in range(12))
    check = (11 - (total % 11)) % 10
    return check == int(clean[12])


def validate_luhn(number: str) -> bool:
    """Luhn 알고리즘으로 신용카드 번호 검증."""
    clean = number.replace("-", "").replace(" ", "")
    if not clean.isdigit() or len(clean) < 13:
        return False

    digits = [int(d) for d in clean]
    # 오른쪽에서 두 번째부터 매 짝수 위치 *2
    for i in range(len(digits) - 2, -1, -2):
        digits[i] *= 2
        if digits[i] > 9:
            digits[i] -= 9

    return sum(digits) % 10 == 0
