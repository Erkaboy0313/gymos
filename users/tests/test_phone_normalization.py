import pytest
from users.services import normalize_uz_phone

@pytest.mark.parametrize("raw,expected", [
    ("+998901234567", "+998901234567"),
    ("998901234567", "+998901234567"),
    ("90 123 45 67", "+998901234567"),
    ("901234567", "+998901234567"),
    ("0 90 123 45 67", "+998901234567"),
])
def test_normalize_uz_phone_ok(raw, expected):
    assert normalize_uz_phone(raw) == expected

@pytest.mark.parametrize("raw", ["", "123", "+997901234567", "+99890123456", "abcd"])
def test_normalize_uz_phone_invalid(raw):
    with pytest.raises(ValueError):
        normalize_uz_phone(raw)