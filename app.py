"""Sales dashboard: sales by region and brand, 5 weakest outlets, Telegram summary.

Run:  streamlit run app.py
"""

from __future__ import annotations

import hmac
import os
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from salesinsight.data import load_sales
from salesinsight.fmt import date_id, month_name, num, pct, rupiah, rupiah_short
from salesinsight.metrics import Period, by_dimension, monthly_totals, weakest_outlets
from salesinsight.summary import build_facts, write_summary
from salesinsight.telegram import TelegramError, config_from_env, send_message

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

# Categorical slots 1 and 2 of the validated default chart palette.
COLOR_CURRENT, COLOR_PREVIOUS = "#2a78d6", "#eb6834"

st.set_page_config(page_title="Sales Insight · Dua Kelinci", page_icon="📊", layout="wide")


@st.cache_data(show_spinner=False)
def load(source) -> tuple[pd.DataFrame, object]:
    return load_sales(source)


# ---------------------------------------------------------------- data + filters

with st.sidebar:
    st.header("Data")
    upload = st.file_uploader("Ganti dengan CSV lain (format sama)", type="csv")
    try:
        df_all, quality = load(upload if upload is not None else ROOT / "data" / "sales.csv")
    except ValueError as exc:
        st.error(str(exc))
        st.stop()

    st.header("Filter")
    regions = st.multiselect("Region", sorted(df_all["region"].unique()))
    brands = st.multiselect("Brand", sorted(df_all["brand"].unique()))
    types = st.multiselect("Tipe outlet", sorted(df_all["outlet_type"].unique()))
    st.caption("Kosong = semua.")

    # On a public deployment, sending to Telegram and calling Claude need a password.
    app_password = os.getenv("APP_PASSWORD", "")
    unlocked = not app_password
    if app_password:
        st.header("Akses")
        entered = st.text_input("Password admin", type="password", help="Untuk Claude dan kirim ke Telegram.")
        unlocked = bool(entered) and hmac.compare_digest(entered, app_password)
        if entered and not unlocked:
            st.error("Password salah.")

df = df_all
if regions:
    df = df[df["region"].isin(regions)]
if brands:
    df = df[df["brand"].isin(brands)]
if types:
    df = df[df["outlet_type"].isin(types)]
if df.empty:
    st.warning("Tidak ada data untuk kombinasi filter ini.")
    st.stop()

period = Period.latest(df)
cur_name = month_name(period.current)
prev_name = month_name(period.previous) if period.previous is not None else None

# ---------------------------------------------------------------- header + KPIs

st.title("Penjualan per Region & Brand")
st.caption(
    f"{date_id(df['date'].min())} – {date_id(df['date'].max())} · "
    f"{num(len(df))} baris invoice bersih · bulan analisis: **{cur_name}**"
    + (f" dibanding {prev_name}" if prev_name else "")
)

totals = monthly_totals(df)
cur_total = totals.get(period.current, 0)
prev_total = totals.get(period.previous, 0) if period.previous is not None else 0
cur_df = df[df["month"] == period.current]

k1, k2, k3, k4 = st.columns(4)
k1.metric(
    f"Penjualan bersih {cur_name}",
    rupiah_short(cur_total),
    (pct((cur_total - prev_total) / prev_total).replace("−", "-") + f" vs {prev_name}") if prev_total else None,
)
k2.metric(f"Penjualan bersih {prev_name or '-'}", rupiah_short(prev_total) if prev_total else "–")
k3.metric(f"Outlet aktif {cur_name}", cur_df["outlet_id"].nunique())
k4.metric(f"Invoice {cur_name}", cur_df["invoice_no"].nunique())


# ---------------------------------------------------------------- charts

def comparison_chart(table: pd.DataFrame, dim: str) -> alt.Chart:
    """Horizontal bars, current vs previous month, one row per category."""
    order = table[dim].tolist()
    rows = []
    for _, r in table.iterrows():
        tip = {
            "Perubahan": pct(r["change"]),
            "Bulan ini": rupiah(r["current"]),
            "Bulan lalu": rupiah(r["previous"]),
        }
        rows.append({dim: r[dim], "Bulan": cur_name, "Nilai": r["current"], **tip})
        if prev_name:
            rows.append({dim: r[dim], "Bulan": prev_name, "Nilai": r["previous"], **tip})
    data = pd.DataFrame(rows)
    domain = [cur_name] + ([prev_name] if prev_name else [])
    rng = [COLOR_CURRENT] + ([COLOR_PREVIOUS] if prev_name else [])
    return (
        alt.Chart(data)
        .mark_bar(cornerRadiusEnd=4, height={"band": 0.9})
        .encode(
            y=alt.Y(f"{dim}:N", sort=order, title=None, axis=alt.Axis(labelLimit=200)),
            yOffset=alt.YOffset("Bulan:N", sort=domain),
            x=alt.X(
                "Nilai:Q",
                title="Penjualan bersih (Rp juta)",
                axis=alt.Axis(labelExpr="format(datum.value / 1e6, ',.0f')", grid=True, gridOpacity=0.4),
            ),
            color=alt.Color(
                "Bulan:N",
                scale=alt.Scale(domain=domain, range=rng),
                legend=alt.Legend(orient="top", title=None),
            ),
            tooltip=[
                alt.Tooltip(f"{dim}:N", title=dim.capitalize()),
                alt.Tooltip("Bulan ini:N", title=cur_name),
                *([alt.Tooltip("Bulan lalu:N", title=prev_name)] if prev_name else []),
                alt.Tooltip("Perubahan:N"),
            ],
        )
        .properties(height=max(220, 46 * len(order)))
    )


def table_view(table: pd.DataFrame, dim: str) -> pd.DataFrame:
    out = pd.DataFrame({
        dim.capitalize(): table[dim],
        cur_name: table["current"].map(rupiah),
    })
    if prev_name:
        out[prev_name] = table["previous"].map(rupiah)
        out["Perubahan"] = table["change"].map(pct)
    out[f"Porsi {cur_name}"] = table["share"].map(lambda x: pct(x, signed=False))
    return out


col_r, col_b = st.columns(2, gap="large")
for col, dim, title in [(col_r, "region", "Per region"), (col_b, "brand", "Per brand")]:
    with col:
        st.subheader(title)
        table = by_dimension(df, dim, period)
        st.altair_chart(comparison_chart(table, dim), width="stretch")
        with st.expander("Lihat tabel"):
            st.dataframe(table_view(table, dim), hide_index=True, width="stretch")

# ---------------------------------------------------------------- weakest outlets

st.subheader("5 outlet terlemah")
st.caption(
    f"Dibandingkan dengan outlet **setipe** (Grosir, Minimarket, Toko Kelontong, Warung): "
    f"penjualan {cur_name} dibagi median penjualan tipe yang sama. Grosir menjual ±10× warung, "
    "jadi peringkat rupiah mentah hanya akan mendaftar warung terkecil. Outlet yang order bulan lalu "
    "tapi kosong bulan ini mendapat skor 0 dan naik ke urutan teratas."
)
weak = weakest_outlets(df, period, n=5)
weak_view = pd.DataFrame({
    "#": range(1, len(weak) + 1),
    "Outlet": weak["outlet_label"],
    "Tipe": weak["outlet_type"],
    "Region": weak["region"],
    "Salesman": weak["salesman"],
    cur_name: weak["current"].map(rupiah),
    **({prev_name: weak["previous"].map(rupiah)} if prev_name else {}),
    "% dari median tipe": weak["peer_index"].map(lambda x: pct(x, signed=False)),
    "Order terakhir": weak["last_order"].map(date_id),
    "Kenapa": weak["reason"],
})
st.dataframe(weak_view, hide_index=True, width="stretch")

# ---------------------------------------------------------------- summary + Telegram

st.subheader("Ringkasan untuk sales manager")
facts = build_facts(df, quality, period)

c1, c2 = st.columns([1, 3])
with c1:
    use_claude = st.toggle(
        "Tulis dengan Claude",
        value=unlocked,
        disabled=not unlocked,
        help="Tanpa kredensial Anthropic, otomatis pakai template."
        + ("" if unlocked else " Masukkan password admin di sidebar untuk memakai Claude."),
    )
    if st.button("Buat ringkasan", type="primary", width="stretch"):
        with st.spinner("Menulis ringkasan…"):
            text, writer = write_summary(facts, use_claude=use_claude)
        st.session_state["summary"] = text
        st.session_state["writer"] = writer
with c2:
    text = st.text_area(
        "Bisa diedit sebelum dikirim",
        value=st.session_state.get("summary", ""),
        height=180,
        placeholder="Tekan “Buat ringkasan”.",
    )
    if "writer" in st.session_state:
        st.caption(
            "Ditulis oleh Claude dari angka yang dihitung aplikasi."
            if st.session_state["writer"] == "claude"
            else "Ditulis dengan template (Claude tidak dipakai atau tidak tersedia)."
        )

token, chat_id = config_from_env()
send = st.button("Kirim ke Telegram", disabled=not (text.strip() and unlocked))
if not unlocked:
    st.caption("Masukkan password admin di sidebar untuk mengirim ke Telegram.")
elif not (token and chat_id):
    st.caption("Isi TELEGRAM_BOT_TOKEN dan TELEGRAM_CHAT_ID di file .env untuk mengaktifkan pengiriman.")
if send and unlocked:
    try:
        send_message(text)
        st.success("Terkirim ke Telegram.")
    except TelegramError as exc:
        st.error(str(exc))

# ---------------------------------------------------------------- data quality

with st.expander(f"Kualitas data: {len(quality.notes())} hal dirapikan dari {num(quality.rows_raw)} baris"):
    for line in quality.notes():
        st.markdown(f"- {line}")
    if quality.shared_outlet_names:
        st.markdown("**Nama outlet yang dipakai lebih dari satu outlet_id:**")
        st.dataframe(
            pd.DataFrame(
                [{"Nama outlet": k, "outlet_id": ", ".join(v)} for k, v in quality.shared_outlet_names.items()]
            ),
            hide_index=True,
            width="stretch",
        )
