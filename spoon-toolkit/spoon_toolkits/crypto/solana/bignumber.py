from decimal import Decimal, getcontext
from typing import Union

getcontext().prec = 10

class BigNumber(Decimal):
    def __new__(cls, value: Union[str, float, int, Decimal, "BigNumber"]) -> "BigNumber":
        return super().__new__(cls, str(value))

    def plus(self, other: Union[str, float, int, Decimal, "BigNumber"]) -> "BigNumber":
        return BigNumber(self + Decimal(str(other)))

    def minus(self, other: Union[str, float, int, Decimal, "BigNumber"]) -> "BigNumber":
        return BigNumber(self - Decimal(str(other)))

    def multiplied_by(self, other: Union[str, float, int, Decimal, "BigNumber"]) -> "BigNumber":
        return BigNumber(self * Decimal(str(other)))

    def divided_by(self, other: Union[str, float, int, Decimal, "BigNumber"]) -> "BigNumber":
        return BigNumber(self / Decimal(str(other)))

    def pow(self, exponent: int) -> "BigNumber":
        return BigNumber(self ** Decimal(exponent))

    def to_number(self) -> float:
        return float(self)

    def to_string(self) -> str:
        return format(self, "f")

BN = BigNumber


def toBN(value: Union[str, float, int, Decimal, BigNumber]) -> BigNumber:
    """Convert a value to a BigNumber (Decimal) object."""
    return BigNumber(value)
