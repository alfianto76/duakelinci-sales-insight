"""Aggregations and the weakest-outlet ranking.

All numbers shown in the dashboard and sent to Telegram come from here, never
from the language model.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .fmt import month_name, pct, rupiah_short


@dataclass
class Period:
    current: pd.Period
    previous: pd.Period | None

    @classmethod
    def latest(cls, df: pd.DataFrame) -> "Period":
        months = sorted(df["month"].unique())
        if not months:
            raise ValueError("Tidak ada data untuk filter ini.")
        cur = months[-1]
        prev = cur - 1
        return cls(cur, prev if prev in months else None)


def _month_sum(df: pd.DataFrame, keys: list[str], month: pd.Period | None) -> pd.Series:
    if month is None:
        return pd.Series(dtype="int64")
    return df[df["month"] == month].groupby(keys)["net_sales_idr"].sum()


def by_dimension(df: pd.DataFrame, dim: str, period: Period) -> pd.DataFrame:
    """Net sales per region/brand for the current and previous month."""
    cur = _month_sum(df, [dim], period.current)
    prev = _month_sum(df, [dim], period.previous)
    out = pd.DataFrame({"current": cur, "previous": prev}).fillna(0).astype("int64")
    out["total"] = df.groupby(dim)["net_sales_idr"].sum()
    out["change"] = (out["current"] - out["previous"]) / out["previous"].where(out["previous"] != 0)
    out["share"] = out["current"] / out["current"].sum() if out["current"].sum() else 0
    return out.sort_values("current", ascending=False).rename_axis(dim).reset_index()


def monthly_totals(df: pd.DataFrame) -> pd.Series:
    return df.groupby("month")["net_sales_idr"].sum().sort_index()


def movers(df: pd.DataFrame, dim: str, period: Period, n: int = 3) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Largest rupiah gains and drops between the previous and current month."""
    cur = _month_sum(df, [dim], period.current)
    prev = _month_sum(df, [dim], period.previous)
    t = pd.DataFrame({"current": cur, "previous": prev}).fillna(0)
    t["delta"] = t["current"] - t["previous"]
    t = t.rename_axis(dim).reset_index()
    return t.nlargest(n, "delta"), t.nsmallest(n, "delta")


def weakest_outlets(df: pd.DataFrame, period: Period, n: int = 5) -> pd.DataFrame:
    """Rank outlets by how far below their peers they sold in the current month.

    Why peers: a Grosir sells ~10x a Warung, so ranking by raw rupiah would just list
    the smallest warungs every month. Instead each outlet is compared with the median
    outlet of the same type (Grosir / Minimarket / Toko Kelontong / Warung):

        peer_index = outlet net sales this month / median for its outlet type

    Outlets that bought last month but nothing this month score 0 and rank first.
    Ties are broken by the biggest month-on-month drop.
    """
    keys = ["outlet_id"]
    info = df.groupby("outlet_id").agg(
        outlet_label=("outlet_label", "first"),
        outlet_name=("outlet_name", "first"),
        outlet_type=("outlet_type", "first"),
        region=("region", "first"),
        branch=("branch", "first"),
        salesman=("salesman", lambda s: s.mode().iat[0]),
        last_order=("date", "max"),
    )
    active = df["month"] == period.current
    if period.previous is not None:
        active |= df["month"] == period.previous
    outlets = info.loc[df.loc[active, "outlet_id"].unique()].copy()

    outlets["current"] = _month_sum(df, keys, period.current).reindex(outlets.index).fillna(0)
    outlets["previous"] = _month_sum(df, keys, period.previous).reindex(outlets.index).fillna(0)
    outlets["orders"] = (
        df[df["month"] == period.current].groupby("outlet_id")["invoice_no"].nunique()
        .reindex(outlets.index).fillna(0).astype(int)
    )
    outlets["peer_median"] = outlets.groupby("outlet_type")["current"].transform("median")
    outlets["peer_index"] = outlets["current"] / outlets["peer_median"].where(outlets["peer_median"] > 0)
    outlets["change"] = (outlets["current"] - outlets["previous"]) / outlets["previous"].where(
        outlets["previous"] > 0
    )
    outlets["reason"] = outlets.apply(lambda r: _reason(r, period), axis=1)
    ranked = outlets.sort_values(["peer_index", "change"], ascending=[True, True], na_position="last")
    return ranked.head(n).reset_index()


def _reason(r: pd.Series, period: Period) -> str:
    cur = month_name(period.current)
    parts = [
        f"{cur}: {rupiah_short(r['current'])}, {pct(r['peer_index'], signed=False)} dari median "
        f"{r['outlet_type']} ({rupiah_short(r['peer_median'])})"
    ]
    if period.previous is not None:
        if r["previous"] > 0:
            parts.append(f"{pct(r['change'])} vs {month_name(period.previous)}")
        else:
            parts.append(f"outlet baru, belum ada order di {month_name(period.previous)}")
    return "; ".join(parts)
