"""Load sales.csv and clean it.

Every cleaning step is counted in a DataQuality report, so the dashboard and the
README can say exactly what was changed and why.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from .fmt import rupiah

REQUIRED_COLUMNS = [
    "date", "invoice_no", "region", "branch", "outlet_id", "outlet_name",
    "outlet_type", "salesman", "brand", "sku", "qty_carton",
    "price_per_carton_idr", "gross_sales_idr", "discount_idr", "net_sales_idr",
]
NUMERIC_COLUMNS = [
    "qty_carton", "price_per_carton_idr", "gross_sales_idr", "discount_idr", "net_sales_idr",
]

# Spelling variants seen in the export, keyed by a lower-cased, space-collapsed form.
REGION_ALIASES = {
    "jabodetabek": "Jabodetabek",
    "jabar": "Jawa Barat",
    "jawa barat": "Jawa Barat",
    "jateng": "Jawa Tengah",
    "jawa tengah": "Jawa Tengah",
    "jatim": "Jawa Timur",
    "jawa timur": "Jawa Timur",
    "kalimantan": "Kalimantan",
    "sumatera": "Sumatera",
    "sumatra": "Sumatera",
}

UNASSIGNED_SALESMAN = "(tidak diisi)"


@dataclass
class DataQuality:
    rows_raw: int = 0
    rows_clean: int = 0
    duplicate_rows_removed: int = 0
    region_values_fixed: int = 0
    region_variants: dict[str, str] = field(default_factory=dict)
    unknown_regions: list[str] = field(default_factory=list)
    names_trimmed: int = 0
    blank_salesman: int = 0
    return_rows: int = 0
    return_value_idr: int = 0
    amount_mismatches: int = 0
    shared_outlet_names: dict[str, list[str]] = field(default_factory=dict)

    def notes(self) -> list[str]:
        """Plain-language lines for the dashboard and the summary."""
        out = []
        if self.duplicate_rows_removed:
            out.append(f"{self.duplicate_rows_removed} baris duplikat persis dibuang (dihitung sekali saja).")
        if self.region_values_fixed:
            variants = ", ".join(f"'{k}' → {v}" for k, v in sorted(self.region_variants.items()))
            out.append(f"{self.region_values_fixed} baris punya penulisan region tidak seragam, disatukan: {variants}.")
        if self.unknown_regions:
            out.append(f"Region tidak dikenal dibiarkan apa adanya: {', '.join(self.unknown_regions)}.")
        if self.names_trimmed:
            out.append(f"{self.names_trimmed} nama outlet punya spasi berlebih, dirapikan.")
        if self.shared_outlet_names:
            out.append(
                f"{len(self.shared_outlet_names)} nama outlet dipakai oleh lebih dari satu outlet_id "
                "(outlet berbeda di cabang berbeda), jadi semua hitungan memakai outlet_id."
            )
        if self.blank_salesman:
            out.append(f"{self.blank_salesman} baris tanpa nama salesman, ditandai '{UNASSIGNED_SALESMAN}'.")
        if self.return_rows:
            out.append(
                f"{self.return_rows} baris retur (qty negatif, {rupiah(self.return_value_idr)}) "
                "tetap dihitung sebagai pengurang penjualan bersih."
            )
        if self.amount_mismatches:
            out.append(f"{self.amount_mismatches} baris dengan gross/net yang tidak cocok dengan qty × harga − diskon.")
        return out


def _normalise_region(value: str) -> str | None:
    key = " ".join(str(value).split()).lower()
    return REGION_ALIASES.get(key)


def load_sales(path: str | Path) -> tuple[pd.DataFrame, DataQuality]:
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    return clean_sales(df)


def clean_sales(raw: pd.DataFrame) -> tuple[pd.DataFrame, DataQuality]:
    missing = [c for c in REQUIRED_COLUMNS if c not in raw.columns]
    if missing:
        raise ValueError(f"Kolom wajib tidak ada di CSV: {', '.join(missing)}")

    q = DataQuality(rows_raw=len(raw))
    df = raw[REQUIRED_COLUMNS].copy()

    # 1. Exact duplicates: same invoice, same SKU, same everything -> a double entry.
    before = len(df)
    df = df.drop_duplicates()
    q.duplicate_rows_removed = before - len(df)

    # 2. Trim whitespace in every text column; count outlet names that changed.
    text_cols = [c for c in REQUIRED_COLUMNS if c not in NUMERIC_COLUMNS]
    q.names_trimmed = int((df["outlet_name"] != df["outlet_name"].str.strip()).sum())
    for c in text_cols:
        df[c] = df[c].astype(str).str.strip()

    # 3. Regions: one spelling per region.
    canon = df["region"].map(_normalise_region)
    unknown = df.loc[canon.isna(), "region"]
    q.unknown_regions = sorted(unknown.unique().tolist())
    changed = canon.notna() & (canon != df["region"])
    q.region_values_fixed = int(changed.sum())
    q.region_variants = {
        orig: new for orig, new in zip(df.loc[changed, "region"], canon[changed])
    }
    df["region"] = canon.fillna(df["region"])

    # 4. Blank salesman.
    blank = df["salesman"] == ""
    q.blank_salesman = int(blank.sum())
    df.loc[blank, "salesman"] = UNASSIGNED_SALESMAN

    # 5. Types.
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")
    for c in NUMERIC_COLUMNS:
        df[c] = pd.to_numeric(df[c]).astype("int64")
    df["month"] = df["date"].dt.to_period("M")

    # 6. Returns stay in (they reduce net sales) but are reported.
    returns = df["qty_carton"] < 0
    q.return_rows = int(returns.sum())
    q.return_value_idr = int(df.loc[returns, "net_sales_idr"].sum())

    # 7. Arithmetic check.
    q.amount_mismatches = int(
        (
            (df["gross_sales_idr"] != df["qty_carton"] * df["price_per_carton_idr"])
            | (df["net_sales_idr"] != df["gross_sales_idr"] - df["discount_idr"])
        ).sum()
    )

    # 8. Outlet identity: outlet_id is the key; names repeat across branches.
    ids_per_name = df.groupby("outlet_name")["outlet_id"].unique()
    q.shared_outlet_names = {
        name: sorted(ids.tolist()) for name, ids in ids_per_name.items() if len(ids) > 1
    }
    # A readable label that is unique per outlet: "Toko Sinar Abadi · Medan".
    first_branch = df.groupby("outlet_id")["branch"].agg(lambda s: s.mode().iat[0])
    first_name = df.groupby("outlet_id")["outlet_name"].agg(lambda s: s.mode().iat[0])
    df["outlet_label"] = df["outlet_id"].map(first_name + " · " + first_branch)

    q.rows_clean = len(df)
    return df.reset_index(drop=True), q
