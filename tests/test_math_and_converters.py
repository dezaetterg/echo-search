import pytest

from providers.calculator import CalculatorProvider
from providers.currency import CurrencyProvider
from providers.timezone import TimezoneProvider
from providers.units import UnitProvider


class DummyHistory:
    def get_score_bonus(self, key, query=""):
        return 0.0

    def record_launch(self, key):
        pass


@pytest.fixture
def history():
    return DummyHistory()


# ---------------------------------------------------------
# Calculator Tests
# ---------------------------------------------------------


def test_calculator_basic_arithmetic(history):
    calc = CalculatorProvider(history)

    # Precedence & basic math
    res = calc.search("2 + 2 * 2")
    assert len(res) == 1
    assert res[0].title == "6"

    res = calc.search("25 * 4")
    assert len(res) == 1
    assert res[0].title == "100"

    res = calc.search("100 - 37")
    assert len(res) == 1
    assert res[0].title == "63"

    res = calc.search("84 / 4")
    assert len(res) == 1
    assert res[0].title == "21" or res[0].title == "21.0"


def test_calculator_functions(history):
    calc = CalculatorProvider(history)

    # Sqrt
    res = calc.search("sqrt(144)")
    assert len(res) == 1
    assert "12" in res[0].title

    # Exponentiation
    res = calc.search("2**8")
    assert len(res) == 1
    assert res[0].title == "256"

    # Trigonometry
    res = calc.search("sin(0)")
    assert len(res) == 1
    assert res[0].title == "0" or res[0].title == "0.0"


def test_calculator_error_handling(history):
    calc = CalculatorProvider(history)

    # Division by zero must not raise an unhandled exception
    res = calc.search("10 / 0")
    assert len(res) == 0 or "Error" in res[0].title or "ZeroDivision" in res[0].title

    # Malformed expressions must safely return empty or error result
    res = calc.search("2 +* 5")
    assert len(res) == 0 or "Error" in res[0].title

    # Normal text should not trigger calculator
    res = calc.search("apple orange banana")
    assert len(res) == 0


# ---------------------------------------------------------
# Units Conversion Tests
# ---------------------------------------------------------


def test_units_distance(history):
    units = UnitProvider(history)

    res = units.search("10 km to mi")
    assert len(res) >= 1
    assert "mi" in res[0].title.lower() or "миль" in res[0].title.lower()

    res = units.search("100 m to ft")
    assert len(res) >= 1
    assert "ft" in res[0].title.lower() or "фут" in res[0].title.lower()


def test_units_temperature(history):
    units = UnitProvider(history)

    res = units.search("32 c to f")
    assert len(res) >= 1
    assert "89.6" in res[0].title

    res = units.search("100 f to c")
    assert len(res) >= 1
    assert "37.7" in res[0].title or "37.8" in res[0].title


def test_units_digital_storage(history):
    units = UnitProvider(history)

    res = units.search("1024 mb to gb")
    assert len(res) >= 1
    assert "1" in res[0].title and "gb" in res[0].title.lower()


# ---------------------------------------------------------
# Currency Conversion Tests
# ---------------------------------------------------------


def test_currency_conversion(history):
    curr = CurrencyProvider(history)

    res = curr.search("100 usd in rub")
    assert len(res) >= 1
    assert "₽" in res[0].title or "rub" in res[0].title.lower()

    res = curr.search("50 eur to usd")
    assert len(res) >= 1
    assert "$" in res[0].title or "usd" in res[0].title.lower()


# ---------------------------------------------------------
# Timezone Tests
# ---------------------------------------------------------


def test_timezone_lookups(history):
    tz = TimezoneProvider(history)

    res = tz.search("время в москве")
    assert len(res) >= 1
    assert "Москва" in res[0].title

    res = tz.search("новокузнецк")
    assert len(res) >= 1
    assert "Новокузнецк" in res[0].title

    res = tz.search("токио")
    assert len(res) >= 1
    assert "Токио" in res[0].title
