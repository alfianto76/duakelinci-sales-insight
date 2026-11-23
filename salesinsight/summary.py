"""One-paragraph summary for the sales manager.

Numbers are computed in `build_facts` and handed to the writer as data. The
writer is Claude when an Anthropic credential is available; otherwise (or if
the call fails) a fixed template writes the same paragraph. Either way the
paragraph never contains a number that was not computed here.
"""

from __future__ import annotations

import json
import logging

import pandas as pd

from .data import DataQuality
from .fmt import month_name, pct, rupiah_short
from .metrics import Period, by_dimension, monthly_totals, movers, weakest_outlets

log = logging.getLogger(__name__)

MODEL = "claude-opus-5-5"


def build_facts(df: pd.DataFrame, quality: DataQuality, period: Period) -> dict:
    totals = monthly_totals(df)
    cur_total = int(totals.get(period.current, 0))
    prev_total = int(totals.get(period.previous, 0)) if period.previous is not None else None

    regions = by_dimension(df, "region", period)
    brands = by_dimension(df, "brand", period)
    weak = weakest_outlets(df, period, n=5)

    facts: dict = {
        "bulan": month_name(period.current, long=True),
        "bulan_sebelumnya": month_name(period.previous, long=True) if period.previous is not None else None,
        "total_bulan_ini": rupiah_short(cur_total),
        "total_bulan_lalu": rupiah_short(prev_total) if prev_total is not None else None,
        "perubahan_total": pct((cur_total - prev_total) / prev_total) if prev_total else None,
        "region_terbesar": _row(regions.iloc[0], "region"),
        "brand_terbesar": _row(brands.iloc[0], "brand"),
        "outlet_terlemah": [
            {
                "outlet": r["outlet_label"],
                "tipe": r["outlet_type"],
                "salesman": r["salesman"],
                "penjualan_bulan_ini": rupiah_short(r["current"]),
                "persen_dari_median_tipe": pct(r["peer_index"], signed=False),
            }
            for _, r in weak.iterrows()
        ],
        "catatan_data": quality.notes(),
    }
    if period.previous is not None:
        facts["region_naik_terbanyak"] = _best(regions, "region", ascending=False)
        facts["region_turun_terbanyak"] = _best(regions, "region", ascending=True)
        facts["brand_turun_terbanyak"] = _best(brands, "brand", ascending=True)
        _, drops = movers(df, "branch", period, n=1)
        facts["cabang_turun_terbesar"] = {
            "cabang": drops.iloc[0]["branch"],
            "selisih": rupiah_short(drops.iloc[0]["delta"]),
        }
    return facts


def _row(r: pd.Series, dim: str) -> dict:
    return {"nama": r[dim], "penjualan": rupiah_short(r["current"]), "perubahan": pct(r["change"])}


def _best(t: pd.DataFrame, dim: str, ascending: bool) -> dict:
    r = t.dropna(subset=["change"]).sort_values("change", ascending=ascending).iloc[0]
    return _row(r, dim)


# ---------------------------------------------------------------- template writer


def template_summary(f: dict) -> str:
    s = [f"Ringkasan penjualan {f['bulan']}: total {f['total_bulan_ini']}"]
    if f.get("perubahan_total"):
        s[0] += f" ({f['perubahan_total']} dari {f['bulan_sebelumnya']})"
    s[0] += "."
    rb, bb = f["region_terbesar"], f["brand_terbesar"]
    s.append(
        f"{rb['nama']} masih region terbesar ({rb['penjualan']}) dan {bb['nama']} brand terlaris ({bb['penjualan']})."
    )
    if "region_naik_terbanyak" in f:
        up, down = f["region_naik_terbanyak"], f["region_turun_terbanyak"]
        s.append(
            f"{up['nama']} tumbuh paling cepat ({up['perubahan']}), sedangkan {down['nama']} turun paling dalam "
            f"({down['perubahan']}); penurunan rupiah terbesar ada di cabang {f['cabang_turun_terbesar']['cabang']} "
            f"({f['cabang_turun_terbesar']['selisih']})."
        )
    weak = f["outlet_terlemah"]
    names = ", ".join(f"{w['outlet']} ({w['penjualan_bulan_ini']})" for w in weak)
    s.append(
        f"Lima outlet terlemah dibanding outlet setipenya: {names}; "
        "mohon salesman terkait mengunjungi dan mengecek stok serta kendala order minggu ini."
    )
    return " ".join(s)


# ---------------------------------------------------------------- Claude writer

SYSTEM_PROMPT = """Kamu menulis ringkasan penjualan untuk sales manager PT Dua Kelinci yang dibaca di Telegram.

Tulis tepat satu paragraf dalam Bahasa Indonesia, 80-120 kata, nada lugas seperti laporan internal.
Isi: kondisi total bulan ini, region dan brand yang perlu perhatian, lima outlet terlemah (sebut namanya),
dan satu tindakan konkret untuk minggu ini.

Gunakan hanya angka dan nama yang ada di data JSON dari pengguna, persis seperti tertulis.
Jangan menghitung angka baru, jangan membulatkan ulang, jangan menebak penyebab yang tidak ada di data.
Tanpa judul, tanpa bullet, tanpa emoji, tanpa markdown."""


def claude_summary(facts: dict, client=None) -> str:
    import anthropic

    client = client or anthropic.Anthropic()
    response = client.beta.messages.create(
        model=MODEL,
        max_tokens=4000,
        output_config={"effort": "low"},
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": json.dumps(facts, ensure_ascii=False, indent=2)}],
    )
    if response.stop_reason == "refusal":
        raise RuntimeError("Claude menolak permintaan ringkasan.")
    text = "".join(b.text for b in response.content if b.type == "text").strip()
    if not text:
        raise RuntimeError("Claude tidak mengembalikan teks.")
    return " ".join(text.split())


def write_summary(facts: dict, use_claude: bool = True) -> tuple[str, str]:
    """Return (paragraph, writer) where writer is 'claude' or 'template'."""
    if use_claude:
        try:
            return claude_summary(facts), "claude"
        except Exception as exc:  # network, auth, refusal: the template still works
            log.warning("Claude summary failed, using template: %s", exc)
    return template_summary(facts), "template"
