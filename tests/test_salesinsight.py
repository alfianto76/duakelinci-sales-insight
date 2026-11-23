from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from salesinsight.data import UNASSIGNED_SALESMAN, clean_sales, load_sales
from salesinsight.fmt import pct, rupiah, rupiah_short
from salesinsight.metrics import Period, by_dimension, weakest_outlets
from salesinsight.summary import build_facts, claude_summary, template_summary, write_summary

CSV = Path(__file__).parents[1] / "data" / "sales.csv"


def row(**kw):
    base = dict(
        date="2026-10-01", invoice_no="INV1", region="Jabodetabek", branch="Bekasi",
        outlet_id="OUT1", outlet_name="Toko A", outlet_type="Warung", salesman="Andi",
        brand="Sukro", sku="Sukro Original 100g", qty_carton="1",
        price_per_carton_idr="100", gross_sales_idr="100", discount_idr="0", net_sales_idr="100",
    )
    base.update({k: str(v) for k, v in kw.items()})
    return base


def frame(*rows):
    return pd.DataFrame(list(rows))


# ---------------------------------------------------------------- cleaning

def test_real_file_cleaning_counts():
    df, q = load_sales(CSV)
    assert q.rows_raw == 1891
    assert q.duplicate_rows_removed == 3
    assert len(df) == 1888
    assert sorted(df["region"].unique()) == [
        "Jabodetabek", "Jawa Barat", "Jawa Tengah", "Jawa Timur", "Kalimantan", "Sumatera",
    ]
    assert q.blank_salesman == 5
    assert q.return_rows == 1
    assert q.amount_mismatches == 0
    assert not df["outlet_name"].str.endswith(" ").any()


def test_region_variants_are_merged():
    df, q = clean_sales(frame(
        row(region="JABODETABEK"), row(region="Jabar", invoice_no="INV2"),
        row(region=" jawa  barat ", invoice_no="INV3"),
    ))
    assert df["region"].tolist() == ["Jabodetabek", "Jawa Barat", "Jawa Barat"]
    assert q.region_values_fixed == 3


def test_unknown_region_kept_and_reported():
    df, q = clean_sales(frame(row(region="Bali")))
    assert df["region"].iat[0] == "Bali"
    assert q.unknown_regions == ["Bali"]


def test_blank_salesman_labelled():
    df, q = clean_sales(frame(row(salesman="")))
    assert df["salesman"].iat[0] == UNASSIGNED_SALESMAN


def test_same_name_different_ids_stay_separate():
    df, q = clean_sales(frame(
        row(outlet_id="OUT1", branch="Medan"), row(outlet_id="OUT2", branch="Solo", invoice_no="INV2"),
    ))
    assert df["outlet_label"].nunique() == 2
    assert q.shared_outlet_names == {"Toko A": ["OUT1", "OUT2"]}


def test_missing_column_is_a_clear_error():
    with pytest.raises(ValueError, match="net_sales_idr"):
        clean_sales(frame(row()).drop(columns=["net_sales_idr"]))


# ---------------------------------------------------------------- metrics

def test_returns_reduce_net_sales():
    df, _ = clean_sales(frame(
        row(net_sales_idr=1000, gross_sales_idr=1000, qty_carton=10),
        row(invoice_no="RTR1", qty_carton=-2, gross_sales_idr=-200, net_sales_idr=-200),
    ))
    t = by_dimension(df, "region", Period.latest(df))
    assert t["current"].iat[0] == 800


def test_weakest_is_relative_to_outlet_type():
    rows = []
    # Grosir peers: 1000, 1000, 300 -> the 300 one is at 30% of its median
    for i, v in enumerate([1000, 1000, 300]):
        rows.append(row(outlet_id=f"G{i}", outlet_name=f"G{i}", outlet_type="Grosir",
                        invoice_no=f"G{i}", net_sales_idr=v))
    # Warung peers: 100, 100, 90 -> smallest rupiah overall, but 90% of its median
    for i, v in enumerate([100, 100, 90]):
        rows.append(row(outlet_id=f"W{i}", outlet_name=f"W{i}", outlet_type="Warung",
                        invoice_no=f"W{i}", net_sales_idr=v))
    df, _ = clean_sales(frame(*rows))
    weak = weakest_outlets(df, Period.latest(df), n=1)
    assert weak["outlet_id"].iat[0] == "G2"


def test_outlet_that_stopped_ordering_ranks_first():
    df, _ = clean_sales(frame(
        row(date="2026-09-10", outlet_id="LOST", outlet_name="Lost", invoice_no="A", net_sales_idr=500),
        row(outlet_id="X", outlet_name="X", invoice_no="B", net_sales_idr=50),
        row(outlet_id="Y", outlet_name="Y", invoice_no="C", net_sales_idr=500),
    ))
    weak = weakest_outlets(df, Period.latest(df), n=3)
    assert weak["outlet_id"].iat[0] == "LOST"
    assert weak["current"].iat[0] == 0


def test_real_file_weakest_five():
    df, _ = load_sales(CSV)
    weak = weakest_outlets(df, Period.latest(df), n=5)
    assert len(weak) == 5
    assert (weak["peer_index"].diff().dropna() >= 0).all()


# ---------------------------------------------------------------- summary

def test_template_summary_uses_computed_numbers():
    df, q = load_sales(CSV)
    facts = build_facts(df, q, Period.latest(df))
    text = template_summary(facts)
    assert facts["total_bulan_ini"] in text
    for w in facts["outlet_terlemah"]:
        assert w["outlet"] in text
    assert "\n" not in text


def test_falls_back_to_template_when_claude_fails(monkeypatch):
    df, q = load_sales(CSV)
    facts = build_facts(df, q, Period.latest(df))

    def boom(*a, **k):
        raise RuntimeError("no credentials")

    monkeypatch.setattr("salesinsight.summary.claude_summary", boom)
    text, writer = write_summary(facts, use_claude=True)
    assert writer == "template"
    assert text == template_summary(facts)


def test_claude_summary_sends_facts_and_reads_text():
    calls = {}

    class FakeMessages:
        def create(self, **kw):
            calls.update(kw)
            return SimpleNamespace(
                stop_reason="end_turn",
                content=[SimpleNamespace(type="thinking"), SimpleNamespace(type="text", text="Satu  paragraf.\n")],
            )

    client = SimpleNamespace(beta=SimpleNamespace(messages=FakeMessages()))
    out = claude_summary({"total_bulan_ini": "Rp1 jt"}, client=client)
    assert out == "Satu paragraf."
    assert "Rp1 jt" in calls["messages"][0]["content"]
    assert calls["fallbacks"] == "default"


def test_claude_refusal_raises():
    class FakeMessages:
        def create(self, **kw):
            return SimpleNamespace(stop_reason="refusal", content=[])

    client = SimpleNamespace(beta=SimpleNamespace(messages=FakeMessages()))
    with pytest.raises(RuntimeError):
        claude_summary({}, client=client)


# ---------------------------------------------------------------- formatting

def test_formatting():
    assert rupiah(1234500) == "Rp1.234.500"
    assert rupiah_short(878_400_000) == "Rp878,4 jt"
    assert rupiah_short(1_730_000_000) == "Rp1,73 M"
    assert pct(0.036) == "+3,6%"
    assert pct(-0.14) == "−14%"
