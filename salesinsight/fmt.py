"""Indonesian number formatting."""

from __future__ import annotations

import math

BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
BULAN_PANJANG = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]


def _id_decimal(x: float, digits: int) -> str:
    s = f"{x:,.{digits}f}"  # 1,234.5
    return s.replace(",", "_").replace(".", ",").replace("_", ".")  # 1.234,5


def rupiah(n: float) -> str:
    """Full amount: Rp1.234.500"""
    sign = "−" if n < 0 else ""
    return f"{sign}Rp{_id_decimal(abs(n), 0)}"


def rupiah_short(n: float) -> str:
    """Compact amount: Rp1,73 M / Rp845,2 jt / Rp940 rb"""
    sign = "−" if n < 0 else ""
    a = abs(n)
    if a >= 1e9:
        return f"{sign}Rp{_id_decimal(a / 1e9, 2)} M"
    if a >= 1e6:
        return f"{sign}Rp{_id_decimal(a / 1e6, 1)} jt"
    if a >= 1e3:
        return f"{sign}Rp{_id_decimal(a / 1e3, 0)} rb"
    return f"{sign}Rp{_id_decimal(a, 0)}"


def pct(x: float | None, signed: bool = True) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "–"
    s = _id_decimal(abs(x) * 100, 0 if abs(x) >= 0.1 else 1)
    if not signed:
        return f"{s}%"
    return f"{'+' if x > 0 else '−' if x < 0 else '±'}{s}%"


def month_name(period, long: bool = False) -> str:
    names = BULAN_PANJANG if long else BULAN
    return f"{names[period.month - 1]} {period.year}"


def num(n: float) -> str:
    """Thousands with dots: 1.888"""
    return _id_decimal(n, 0)


def date_id(ts) -> str:
    return f"{ts.day:02d} {BULAN[ts.month - 1]} {ts.year}"
