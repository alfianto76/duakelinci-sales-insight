"""Sales Intelligence dashboard: region & brand sales, 5 weakest outlets, AI brief to Telegram.

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

from salesinsight import ui
from salesinsight.data import load_sales
from salesinsight.fmt import date_id, month_name, num, pct, rupiah, rupiah_short
from salesinsight.metrics import Period, by_dimension, insights, monthly_totals, weakest_outlets
from salesinsight.summary import build_facts, template_summary, write_summary
from salesinsight.telegram import TelegramError, config_from_env, send_message

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")


st.set_page_config(page_title="Sales Intelligence · Dua Kelinci", page_icon="🐇", layout="wide")
if "dark" not in st.session_state:
    st.session_state["dark"] = st.query_params.get("theme") == "dark"
DARK = st.session_state["dark"]
ui.inject_css(DARK)
CT = ui.chart_theme(DARK)

# ---------------------------------------------------------------- login

APP_USER = os.getenv("APP_USERNAME", "admin")
APP_PASSWORD = os.getenv("APP_PASSWORD", "")


def check_login(user: str, pw: str) -> bool:
    # Phones capitalise the first letter and keyboards add trailing spaces:
    # usernames are case-insensitive, and stray spaces around either field are ignored.
    user_ok = hmac.compare_digest(user.strip().casefold().encode(), APP_USER.strip().casefold().encode())
    pw_ok = hmac.compare_digest(pw.strip().encode(), APP_PASSWORD.strip().encode())
    return user_ok and pw_ok


if APP_PASSWORD and "auth_user" not in st.session_state:
    ui.login_screen(check_login)  # stops here until logged in

user_name = st.session_state.get("auth_user", "Lokal")


@st.cache_data(show_spinner=False)
def load(source) -> tuple[pd.DataFrame, object]:
    return load_sales(source)


# ---------------------------------------------------------------- sidebar

with st.sidebar:
    ui.sidebar_user(user_name)

    def _theme_changed() -> None:
        if st.session_state["dark"]:
            st.query_params["theme"] = "dark"
        else:
            st.query_params.pop("theme", None)

    st.toggle(":material/dark_mode: Mode gelap", key="dark", on_change=_theme_changed)
    if APP_PASSWORD and st.button("Keluar", width="stretch", icon=":material/logout:"):
        st.session_state.clear()
        st.rerun()

    ui.side_heading("Filter", "tune")
    try:
        df_all, quality = load(ROOT / "data" / "sales.csv")
    except ValueError as exc:
        st.error(str(exc))
        st.stop()
    regions = st.multiselect("Region", sorted(df_all["region"].unique()), placeholder="Semua region")
    brands = st.multiselect("Brand", sorted(df_all["brand"].unique()), placeholder="Semua brand")
    types = st.multiselect("Tipe outlet", sorted(df_all["outlet_type"].unique()), placeholder="Semua tipe")

    ui.side_heading("Data", "database")
    with st.expander("Ganti data CSV", icon=":material/upload_file:"):
        upload = st.file_uploader("Format kolom sama dengan sales.csv", type="csv")
    if upload is not None:
        try:
            df_all, quality = load(upload)
        except ValueError as exc:
            st.error(str(exc))
            st.stop()

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
claude_on = bool(os.getenv("ANTHROPIC_API_KEY"))

# ---------------------------------------------------------------- header + KPIs

ui.topbar(
    f"{date_id(df['date'].min())} – {date_id(df['date'].max())} · {num(len(df))} baris invoice bersih",
    claude_on,
)

totals = monthly_totals(df)
cur_total = totals.get(period.current, 0)
prev_total = totals.get(period.previous, 0) if period.previous is not None else 0
cur_df = df[df["month"] == period.current]
prev_df = df[df["month"] == period.previous] if period.previous is not None else df.iloc[0:0]


def delta(cur: float, prev: float) -> tuple[str | None, str]:
    if not prev:
        return None, "flat"
    ch = (cur - prev) / prev
    return f"{pct(ch)} vs {prev_name}", "up" if ch > 0 else "down" if ch < 0 else "flat"


avg_cur = cur_total / max(cur_df["invoice_no"].nunique(), 1)
avg_prev = prev_total / max(prev_df["invoice_no"].nunique(), 1) if prev_total else 0
ui.kpi_cards([
    ("payments", f"Penjualan bersih {cur_name}", rupiah_short(cur_total), *delta(cur_total, prev_total)),
    ("storefront", f"Outlet aktif {cur_name}", str(cur_df["outlet_id"].nunique()),
     *delta(cur_df["outlet_id"].nunique(), prev_df["outlet_id"].nunique())),
    ("receipt_long", f"Invoice {cur_name}", num(cur_df["invoice_no"].nunique()),
     *delta(cur_df["invoice_no"].nunique(), prev_df["invoice_no"].nunique())),
    ("shopping_cart", "Rata-rata per invoice", rupiah_short(avg_cur), *delta(avg_cur, avg_prev)),
])

# ---------------------------------------------------------------- AI brief

facts = build_facts(df, quality, period)
sig = (tuple(regions), tuple(brands), tuple(types), upload.name if upload is not None else "")
if st.session_state.get("summary_sig") != sig:
    st.session_state["summary_sig"] = sig
    st.session_state["summary"] = template_summary(facts)
    st.session_state["writer"] = "template"

with st.container(key="ai_panel"):
    ui.ai_head(
        "Ditulis Claude dari angka yang dihitung aplikasi"
        if st.session_state["writer"] == "claude"
        else "Draf otomatis dari angka aplikasi · bisa diedit sebelum dikirim"
    )
    text = st.text_area(
        "Ringkasan untuk sales manager",
        value=st.session_state["summary"],
        height=190,
        label_visibility="collapsed",
        key=f"summary_box_{abs(hash(st.session_state['summary']))}",
    )
    token, chat_id = config_from_env()
    b1, b2, b3 = st.columns([1.3, 1.2, 3])
    with b1:
        if st.button("Tulis dengan Claude", type="primary", width="stretch", disabled=not claude_on,
                     icon=":material/auto_awesome:",
                     help=None if claude_on else "Isi ANTHROPIC_API_KEY untuk mengaktifkan Claude."):
            with st.spinner("Claude sedang menulis…"):
                new, writer = write_summary(facts, use_claude=True)
            st.session_state["summary"], st.session_state["writer"] = new, writer
            if writer != "claude":
                st.toast("Claude tidak tersedia, memakai draf template.")
            st.rerun()
    with b2:
        if st.button("Kirim ke Telegram", width="stretch", icon=":material/send:", disabled=not (text.strip() and token and chat_id)):
            try:
                send_message(text)
                st.toast("Terkirim ke Telegram ✓")
            except TelegramError as exc:
                st.error(str(exc))
    with b3:
        if not (token and chat_id):
            st.caption("Isi TELEGRAM_BOT_TOKEN dan TELEGRAM_CHAT_ID untuk mengaktifkan pengiriman.")
    ui.insight_cards(insights(df, period))


# ---------------------------------------------------------------- charts

def comparison_chart(table: pd.DataFrame, dim: str) -> alt.Chart:
    order = table[dim].tolist()
    rows = []
    for _, r in table.iterrows():
        tip = {"Perubahan": pct(r["change"]), "Bulan ini": rupiah(r["current"]), "Bulan lalu": rupiah(r["previous"])}
        rows.append({dim: r[dim], "Bulan": cur_name, "Nilai": r["current"], **tip})
        if prev_name:
            rows.append({dim: r[dim], "Bulan": prev_name, "Nilai": r["previous"], **tip})
    data = pd.DataFrame(rows)
    domain = [cur_name] + ([prev_name] if prev_name else [])
    rng = [CT["current"]] + ([CT["previous"]] if prev_name else [])
    return (
        alt.Chart(data)
        .mark_bar(cornerRadiusEnd=4, height={"band": 0.85})
        .encode(
            y=alt.Y(f"{dim}:N", sort=order, title=None,
                    axis=alt.Axis(labelLimit=200, labelFontSize=12, labelColor=CT["label"], ticks=False, domain=False)),
            yOffset=alt.YOffset("Bulan:N", sort=domain),
            x=alt.X("Nilai:Q", title="Rp juta",
                    axis=alt.Axis(labelExpr="format(datum.value / 1e6, ',.0f')", grid=True, gridColor=CT["grid"],
                                  domain=False, ticks=False, labelColor=CT["muted"], titleColor=CT["muted"],
                                  titleFontWeight="normal")),
            color=alt.Color("Bulan:N", scale=alt.Scale(domain=domain, range=rng),
                            legend=alt.Legend(orient="top", title=None, labelColor=CT["label"], symbolType="circle")),
            tooltip=[
                alt.Tooltip(f"{dim}:N", title=dim.capitalize()),
                alt.Tooltip("Bulan ini:N", title=cur_name),
                *([alt.Tooltip("Bulan lalu:N", title=prev_name)] if prev_name else []),
                alt.Tooltip("Perubahan:N"),
            ],
        )
        .properties(height=max(220, 44 * len(order)))
        .configure_view(stroke=None)
        .configure(font="Plus Jakarta Sans", background=CT["bg"])
    )


def table_view(table: pd.DataFrame, dim: str) -> pd.DataFrame:
    out = pd.DataFrame({dim.capitalize(): table[dim], cur_name: table["current"].map(rupiah)})
    if prev_name:
        out[prev_name] = table["previous"].map(rupiah)
        out["Perubahan"] = table["change"].map(pct)
    out[f"Porsi {cur_name}"] = table["share"].map(lambda x: pct(x, signed=False))
    return out


col_r, col_b = st.columns(2, gap="large")
for col, dim, title, ic in [(col_r, "region", "Penjualan per region", "map"),
                           (col_b, "brand", "Penjualan per brand", "inventory_2")]:
    with col:
        ui.section(title, cur_name + (f" dibanding {prev_name}" if prev_name else ""), ic)
        with st.container(key=f"card_{dim}"):
            table = by_dimension(df, dim, period)
            st.altair_chart(comparison_chart(table, dim), width="stretch")
            with st.expander("Lihat tabel", icon=":material/table_chart:"):
                ui.table(table_view(table, dim))

# ---------------------------------------------------------------- weakest outlets

ui.section(
    "5 outlet terlemah",
    "Dibandingkan dengan outlet setipe (Grosir, Minimarket, Toko Kelontong, Warung), karena grosir "
    "menjual ±10× warung. Outlet yang berhenti order langsung naik ke urutan teratas.",
    "warning",
)
with st.container(key="card_weak"):
    ui.weak_table(weakest_outlets(df, period, n=5), cur_name, prev_name)
    st.write("")

# ---------------------------------------------------------------- data quality

st.write("")
with st.expander(f"Kualitas data · {len(quality.notes())} hal dirapikan dari {num(quality.rows_raw)} baris",
                 icon=":material/fact_check:"):
    for line in quality.notes():
        st.markdown(f"- {line}")
    if quality.shared_outlet_names:
        ui.table(pd.DataFrame([{"Nama outlet": k, "outlet_id": ", ".join(v)}
                               for k, v in quality.shared_outlet_names.items()]))

ui.footer()
