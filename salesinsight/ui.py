"""Look and feel: CSS, header, cards, login screen.

Everything here is presentation only; numbers come from metrics.py.
"""

from __future__ import annotations

import base64
import html
from pathlib import Path

import pandas as pd
import streamlit as st

from .fmt import pct, rupiah, rupiah_short

ASSETS = Path(__file__).parents[1] / "assets"
BRAND = "#D7262E"

LIGHT = """
  --bg: #F6F5F2; --card: #FFFFFF; --card-2: #FAF9F6; --chip: #F1EFEA; --input: #FFFFFF;
  --line: #E7E4DE; --line-2: #F0EDE8;
  --ink: #1B1B1F; --ink-2: #55545C; --ink-3: #8C8A93;
  --brand: #D7262E; --brand-soft: #FDECEC;
  --up: #1F8A4C; --up-soft: #E7F5EC; --down: #C2410C; --down-soft: #FFF1E8;
  --ai-a: #D7262E; --ai-b: #7C3AED; --shadow: 0 1px 2px rgba(27,27,31,.04), 0 8px 24px rgba(27,27,31,.05);
"""
DARK = """
  --bg: #0E0E11; --card: #17171C; --card-2: #1C1C22; --chip: #24242B; --input: #1C1C22;
  --line: #2A2A32; --line-2: #222229;
  --ink: #F2F1EE; --ink-2: #C4C2BD; --ink-3: #8F8D97;
  --brand: #F0464D; --brand-soft: rgba(240,70,77,.15);
  --up: #43C47C; --up-soft: rgba(67,196,124,.14); --down: #F2915A; --down-soft: rgba(242,145,90,.14);
  --ai-a: #F0464D; --ai-b: #9B6BFF; --shadow: 0 1px 2px rgba(0,0,0,.3), 0 10px 30px rgba(0,0,0,.35);
"""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,300..600,0..1,0&display=block');

:root { __VARS__ }
html, body, [class*="css"], .stApp, .stMarkdown, button, input, textarea, select {
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif !important;
}
.stApp { background: var(--bg) !important; color: var(--ink); }
.block-container { padding-top: 1.6rem; padding-bottom: 3.5rem; max-width: 1360px; }
header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }
.stMarkdown p, .stMarkdown li { color: var(--ink); }

/* icons */
.ms, [data-testid="stIconMaterial"] { font-family: 'Material Symbols Rounded' !important; font-weight: normal; font-style: normal;
  line-height: 1; letter-spacing: normal; text-transform: none; white-space: nowrap; direction: ltr;
  -webkit-font-feature-settings: 'liga'; font-feature-settings: 'liga'; -webkit-font-smoothing: antialiased; }
.ms { font-size: 20px; font-variation-settings: 'FILL' 0, 'wght' 500; vertical-align: middle; }
.ms.fill { font-variation-settings: 'FILL' 1, 'wght' 500; }
.ico { width:36px; height:36px; border-radius: 11px; display:grid; place-items:center; flex:none; }
.ico.brand { background: var(--brand-soft); color: var(--brand); }
.ico.up { background: var(--up-soft); color: var(--up); }
.ico.down { background: var(--down-soft); color: var(--down); }
.ico.ai { background: linear-gradient(135deg, var(--ai-a), var(--ai-b)); color:#fff; }
.ico.sm { width:30px; height:30px; border-radius: 9px; } .ico.sm .ms { font-size: 18px; }

/* section titles */
.sec-title { font-size: 1.08rem; font-weight: 700; color: var(--ink); margin: 2.4rem 0 .25rem; display:flex; align-items:center; gap:.6rem; }
.sec-title .ms { color: var(--brand); font-size: 22px; }
.sec-sub { font-size: .84rem; color: var(--ink-3); margin-bottom: 1rem; line-height: 1.5; max-width: 900px; }

/* header */
.topbar { display:flex; align-items:center; justify-content:space-between; gap:1rem; flex-wrap:wrap;
  background: var(--card); border:1px solid var(--line); border-radius: 20px; padding: 16px 24px; margin-bottom: 1.25rem; box-shadow: var(--shadow); }
.brand { display:flex; align-items:center; gap:18px; }
.brand img { height: 54px; width:auto; display:block; }
.wordmark { font-weight: 800; color: var(--brand); font-size: 1.25rem; letter-spacing:-.02em; }
.brand-title { font-weight: 800; font-size: 1.2rem; color: var(--ink); line-height:1.15; }
.brand-sub { font-size: .82rem; color: var(--ink-3); margin-top: 3px; }
.divider-v { width:1px; height:40px; background: var(--line); }
.pill .ms { font-size: 16px; }
.pill { display:inline-flex; align-items:center; gap:6px; font-size:.76rem; font-weight:600; padding:7px 13px; border-radius:999px; }
.pill-ai { color:#fff; background: linear-gradient(90deg, var(--ai-a), var(--ai-b)); box-shadow: 0 4px 14px rgba(124,58,237,.25); }
.pill-soft { color: var(--ink-2); background: var(--chip); }

/* KPI cards */
.kpis { display:grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap: 16px; }
@media (max-width: 1000px) { .kpis { grid-template-columns: repeat(2, minmax(0,1fr)); } }
.kpi { background: var(--card); border:1px solid var(--line); border-radius: 18px; padding: 20px 22px; box-shadow: var(--shadow); }
.kpi-top { display:flex; justify-content:space-between; align-items:flex-start; gap:10px; }
.kpi-label { font-size:.76rem; color: var(--ink-3); font-weight:600; text-transform: uppercase; letter-spacing:.05em; line-height:1.4; }
.kpi-value { font-size: 1.85rem; font-weight: 800; color: var(--ink); margin-top: 8px; letter-spacing:-.02em; }
.kpi-delta { display:inline-flex; align-items:center; gap:3px; margin-top:10px; font-size:.78rem; font-weight:700; padding:4px 10px; border-radius:9px; }
.kpi-delta.up { color: var(--up); background: var(--up-soft); }
.kpi-delta.down { color: var(--down); background: var(--down-soft); }
.kpi-delta.flat { color: var(--ink-2); background: var(--chip); }
.kpi-delta .ms { font-size: 16px; }

/* AI panel (st.container key="ai_panel") */
.st-key-ai_panel {
  background: linear-gradient(var(--card), var(--card)) padding-box,
              linear-gradient(120deg, var(--ai-a), var(--ai-b)) border-box;
  border: 1.5px solid transparent; border-radius: 22px; padding: 24px 26px 28px !important;
  box-shadow: 0 14px 40px rgba(124,58,237,.10); gap: 1rem !important; margin-top: 1.25rem;
}
.st-key-ai_panel [data-testid="stElementContainer"], .st-key-ai_panel [data-testid="stMarkdown"],
.st-key-ai_panel [data-testid="stMarkdownContainer"] { overflow: visible !important; }
.ai-head { display:flex; align-items:center; justify-content:space-between; gap:10px; flex-wrap:wrap; }
.ai-title { font-weight:800; font-size:1.12rem; display:flex; align-items:center; gap:10px; color: var(--ink); }
.ai-meta { font-size:.78rem; color: var(--ink-3); }
.st-key-ai_panel textarea { font-size: .95rem !important; line-height: 1.65 !important; padding: 14px 16px !important; }

/* insight cards */
.insights-label { font-size:.76rem; font-weight:700; color: var(--ink-3); text-transform: uppercase; letter-spacing:.06em;
  display:flex; align-items:center; gap:6px; margin-top: .4rem; }
.insights-label .ms { font-size: 17px; }
.insights { display:grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap: 14px; margin: 12px 0 4px; }
@media (max-width: 1280px) { .insights { grid-template-columns: repeat(2, minmax(0,1fr)); } }
@media (max-width: 640px) { .insights { grid-template-columns: 1fr; } }
.ins { border-radius: 16px; padding: 18px 18px 16px; border:1px solid var(--line); background: var(--card-2); }
.ins-t { font-weight:700; font-size:.92rem; display:flex; gap:12px; align-items:center; line-height:1.35; color: var(--ink); }
.ins-b { font-size:.83rem; color: var(--ink-2); margin-top: 10px; line-height:1.6; }

/* cards around charts / tables (st.container key starting with card_) */
[class*="st-key-card_"] { background: var(--card); border:1px solid var(--line); border-radius: 20px; padding: 20px 22px 12px !important; box-shadow: var(--shadow); }

/* weakest outlets */
.weak { width:100%; border-collapse: separate; border-spacing: 0; font-size:.88rem; border:none !important; margin:0; }
.weak th, .weak td { border-left:none !important; border-right:none !important; border-top:none !important; background:transparent !important; color: var(--ink); }
[data-testid="stMarkdownContainer"] table.weak, [data-testid="stMarkdownContainer"] table.tbl { display: table; }
.weak th { text-align:left; font-size:.72rem; text-transform:uppercase; letter-spacing:.05em; color: var(--ink-3) !important; font-weight:700; padding: 10px 14px; border-bottom:1px solid var(--line) !important; }
.weak td { padding: 16px 14px; border-bottom:1px solid var(--line-2) !important; vertical-align: middle; }
.weak tr:last-child td { border-bottom: none !important; }
.rank { width:32px; height:32px; border-radius: 10px; background: var(--brand-soft); color: var(--brand); font-weight:800; display:grid; place-items:center; }
.o-name { font-weight:700; color: var(--ink); }
.o-meta { font-size:.76rem; color: var(--ink-3); margin-top: 3px; }
.o-meta .ms { font-size: 14px; color: var(--ink-3); vertical-align: -2px; }
.bar { position:relative; height:8px; background: var(--chip); border-radius:99px; min-width:140px; }
.bar > span { position:absolute; left:0; top:0; bottom:0; border-radius:99px; background: var(--brand); }
.bar-l { font-size:.76rem; color: var(--ink-2); margin-top:6px; }
.chg.up { color: var(--up); font-weight:700; } .chg.down { color: var(--down); font-weight:700; }

/* simple data tables */
.tbl { width:100%; border-collapse: collapse; font-size:.84rem; border:none !important; }
.tbl th, .tbl td { border:none !important; border-bottom:1px solid var(--line-2) !important; padding: 9px 10px; text-align:left; color: var(--ink); background: transparent !important; }
.tbl th { font-size:.72rem; text-transform: uppercase; letter-spacing:.05em; color: var(--ink-3) !important; font-weight:700; border-bottom:1px solid var(--line) !important; }
.tbl tr:last-child td { border-bottom: none !important; }

/* sidebar */
section[data-testid="stSidebar"] { background: var(--card) !important; border-right:1px solid var(--line); }
section[data-testid="stSidebar"] * { color: var(--ink); }
.side-user { display:flex; align-items:center; gap:10px; padding:12px 14px; background: var(--chip); border-radius:14px; margin-bottom: .6rem; }
.side-head { display:flex; align-items:center; gap:8px; font-weight:700; font-size:.78rem; color: var(--ink-3) !important;
  text-transform: uppercase; letter-spacing:.07em; margin: 1.4rem 0 .5rem; }
.side-head .ms { font-size: 18px; color: var(--ink-3) !important; }
.online { width:9px; height:9px; border-radius:50%; background:#22C55E; border:2px solid var(--card); margin-left:auto; }
.avatar { width:34px; height:34px; border-radius:50%; background: linear-gradient(135deg, var(--ai-a), var(--ai-b)); color:#fff !important; display:grid; place-items:center; font-weight:800; }

/* native widgets follow the theme */
[data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label { color: var(--ink-2) !important; }
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p { color: var(--ink-3) !important; }
[data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="base-input"], [data-baseweb="select"] > div {
  background-color: var(--input) !important; border-color: var(--line) !important; }
[data-baseweb="input"] input, [data-baseweb="textarea"] textarea, [data-baseweb="select"] div { color: var(--ink) !important; -webkit-text-fill-color: var(--ink); }
[data-baseweb="select"] input::placeholder, [data-baseweb="input"] input::placeholder { color: var(--ink-3) !important; -webkit-text-fill-color: var(--ink-3); }
[data-baseweb="popover"] ul, [data-baseweb="popover"] li, [data-baseweb="menu"] { background: var(--card) !important; color: var(--ink) !important; }
[data-baseweb="tag"] { background: var(--brand-soft) !important; }
[data-baseweb="tag"] span { color: var(--brand) !important; }
[data-testid="stExpander"] details { background: var(--card); border:1px solid var(--line) !important; border-radius: 14px; }
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary * { color: var(--ink) !important; }
[data-testid="stFileUploaderDropzone"] { background: var(--card-2) !important; }
.stButton button, .stFormSubmitButton button { border-radius: 12px; font-weight: 700; padding: .55rem 1rem; }
.stButton button[kind="secondary"] { background: var(--card) !important; color: var(--ink) !important; border-color: var(--line) !important; }
.stButton button[kind="secondary"]:hover { border-color: var(--brand) !important; color: var(--brand) !important; }
.stButton button:disabled { opacity: .55; }
[data-testid="stToggle"] label p { color: var(--ink) !important; }
.stTextArea textarea, .stTextInput input { background-color: var(--input) !important; color: var(--ink) !important;
  -webkit-text-fill-color: var(--ink) !important; caret-color: var(--ink); }
.stTextArea [data-baseweb], .stTextInput [data-baseweb],
[data-testid="stTextInputRootElement"], [data-testid="stTextAreaRootElement"],
.stMultiSelect .react-aria-ComboBox > div, .stSelectbox .react-aria-ComboBox > div {
  background-color: var(--input) !important; border-color: var(--line) !important; }
.stMultiSelect input { color: var(--ink) !important; -webkit-text-fill-color: var(--ink) !important; }
.stMultiSelect input::placeholder { color: var(--ink-3) !important; -webkit-text-fill-color: var(--ink-3) !important; }
.stMultiSelect [data-baseweb="select"] > div, .stMultiSelect [data-baseweb="select"] > div > div:first-child {
  background-color: var(--input) !important; border-color: var(--line) !important; }
.stMultiSelect svg, .stTextInput svg { fill: var(--ink-3) !important; color: var(--ink-3) !important; }
.stTextInput [data-testid="stIconMaterial"], .stTextInput button, .stTextInput button *,
.stMultiSelect [data-testid="stIconMaterial"] { color: var(--ink-3) !important; }
[data-testid="stExpander"] [data-testid="stIconMaterial"] { color: var(--ink-2) !important; }
.stButton button:disabled, .stButton button[disabled] { background: var(--chip) !important; color: var(--ink-3) !important;
  border: 1px solid var(--line) !important; opacity: 1 !important; }
.stButton button:disabled p, .stButton button:disabled [data-testid="stIconMaterial"] { color: var(--ink-3) !important; }

/* login */
.st-key-login_card { max-width: 440px; margin: 8vh auto 0; background: var(--card); border:1px solid var(--line);
  border-radius: 24px; padding: 32px 32px 20px !important; box-shadow: 0 24px 60px rgba(0,0,0,.10); }
.login-logo { display:flex; justify-content:center; margin-bottom: 10px; }
.login-logo img { height: 88px; }
.login-badge { display:flex; justify-content:center; margin: 8px 0 4px; }
.login-title { text-align:center; font-weight:800; font-size:1.4rem; margin-top: 6px; color: var(--ink); }
.login-sub { text-align:center; color: var(--ink-3); font-size:.88rem; margin-bottom: 18px; }
.foot { text-align:center; color: var(--ink-3); font-size:.76rem; margin-top: 2.5rem; }
.foot .ms { font-size: 15px; vertical-align: -3px; }
</style>
"""


def inject_css(dark: bool = False) -> None:
    st.markdown(CSS.replace("__VARS__", DARK if dark else LIGHT), unsafe_allow_html=True)


def chart_theme(dark: bool) -> dict:
    """Colors for Altair charts so they match the page theme."""
    if dark:
        return {"bg": "#17171C", "label": "#C4C2BD", "muted": "#8F8D97", "grid": "#26262D",
                "current": "#F0464D", "previous": "#6E6A64"}
    return {"bg": "#FFFFFF", "label": "#55545C", "muted": "#8C8A93", "grid": "#EFECE6",
            "current": "#D7262E", "previous": "#B4AFA6"}


def table(df: pd.DataFrame) -> None:
    """Small themed HTML table (replaces the canvas grid, which ignores our theme)."""
    st.markdown(df.to_html(index=False, classes="tbl", border=0, escape=True), unsafe_allow_html=True)


def _logo_src() -> str | None:
    for name, mime in [("logo.png", "image/png"), ("logo.svg", "image/svg+xml"), ("logo.jpg", "image/jpeg"), ("logo.webp", "image/webp")]:
        p = ASSETS / name
        if p.exists():
            return f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"
    return None


def icon(name: str, cls: str = "") -> str:
    """Material Symbols icon (Rounded)."""
    return f'<span class="ms {cls}">{name}</span>'


def logo_html() -> str:
    src = _logo_src()
    if src:
        return f'<img src="{src}" alt="Dua Kelinci">'
    return '<span class="wordmark">Dua Kelinci</span>'


def topbar(subtitle: str, claude_on: bool) -> None:
    ai = f'<span class="pill pill-ai">{icon("auto_awesome", "fill")}AI-assisted</span>'
    mode = (f'{icon("check_circle")}Claude aktif' if claude_on else f'{icon("description")}Mode template')
    st.markdown(
        f"""<div class="topbar">
          <div class="brand">{logo_html()}<div class="divider-v"></div>
            <div><div class="brand-title">Sales Intelligence</div><div class="brand-sub">{html.escape(subtitle)}</div></div>
          </div>
          <div style="display:flex;gap:8px;flex-wrap:wrap">{ai}<span class="pill pill-soft">{mode}</span></div>
        </div>""",
        unsafe_allow_html=True,
    )


def kpi_cards(items: list[tuple[str, str, str, str | None, str]]) -> None:
    """items: (icon, label, value, delta_text, tone) with tone in up/down/flat."""
    arrows = {"up": "arrow_upward", "down": "arrow_downward", "flat": "remove"}
    cells = []
    for ic, label, value, delta, tone in items:
        d = (f'<div class="kpi-delta {tone}">{icon(arrows[tone])}{html.escape(delta)}</div>' if delta else "")
        cells.append(f'<div class="kpi"><div class="kpi-top"><div class="kpi-label">{html.escape(label)}</div>'
                     f'<div class="ico brand sm">{icon(ic)}</div></div>'
                     f'<div class="kpi-value">{html.escape(value)}</div>{d}</div>')
    st.markdown(f'<div class="kpis">{"".join(cells)}</div>', unsafe_allow_html=True)


def section(title: str, sub: str = "", ic: str = "") -> None:
    st.markdown(
        f'<div class="sec-title">{icon(ic) if ic else ""}{html.escape(title)}</div>'
        + (f'<div class="sec-sub">{html.escape(sub)}</div>' if sub else ""),
        unsafe_allow_html=True,
    )


def ai_head(meta: str) -> None:
    st.markdown(
        f"""<div class="ai-head"><div class="ai-title"><span class="ico ai sm">{icon("auto_awesome", "fill")}</span>AI Sales Brief</div>
        <div class="ai-meta">{html.escape(meta)}</div></div>""",
        unsafe_allow_html=True,
    )


def insight_cards(items: list[dict]) -> None:
    if not items:
        return
    icons = {"up": ("trending_up", "up"), "down": ("trending_down", "down"), "alert": ("priority_high", "brand")}
    cells = "".join(
        f'<div class="ins {i["tone"]}"><div class="ins-t"><span class="ico sm {icons[i["tone"]][1]}">'
        f'{icon(icons[i["tone"]][0])}</span>{html.escape(i["title"])}</div>'
        f'<div class="ins-b">{html.escape(i["body"])}</div></div>'
        for i in items
    )
    st.markdown(f'<div class="insights-label">{icon("insights")}Sinyal otomatis dari data</div>'
                f'<div class="insights">{cells}</div>', unsafe_allow_html=True)


def weak_table(weak: pd.DataFrame, cur_name: str, prev_name: str | None) -> None:
    rows = []
    for i, r in enumerate(weak.itertuples(), start=1):
        share = 0 if pd.isna(r.peer_index) else max(0.0, min(1.0, float(r.peer_index)))
        if prev_name and r.previous > 0:
            tone = "up" if r.change > 0 else "down"
            chg = f'<span class="chg {tone}">{pct(r.change)}</span><div class="o-meta">vs {html.escape(prev_name)}</div>'
        elif prev_name:
            chg = '<span class="o-meta">outlet baru</span>'
        else:
            chg = "–"
        rows.append(f"""<tr>
          <td><div class="rank">{i}</div></td>
          <td><div class="o-name">{html.escape(r.outlet_label)}</div>
              <div class="o-meta">{icon("storefront")} {html.escape(r.outlet_type)} · {icon("location_on")} {html.escape(r.region)} · {icon("badge")} {html.escape(r.salesman)}</div></td>
          <td><div class="o-name">{rupiah_short(r.current)}</div><div class="o-meta">{rupiah(r.current)}</div></td>
          <td><div class="bar"><span style="width:{share*100:.0f}%"></span></div>
              <div class="bar-l">{pct(r.peer_index, signed=False)} dari median {html.escape(r.outlet_type)} ({rupiah_short(r.peer_median)})</div></td>
          <td>{chg}</td>
        </tr>""")
    st.markdown(
        f"""<table class="weak"><thead><tr><th></th><th>Outlet</th><th>{html.escape(cur_name)}</th>
        <th>Dibanding outlet setipe</th><th>Tren</th></tr></thead><tbody>{''.join(rows)}</tbody></table>""",
        unsafe_allow_html=True,
    )


def sidebar_user(name: str) -> None:
    initial = (name[:1] or "A").upper()
    st.markdown(
        f'<div class="side-user"><div class="avatar">{html.escape(initial)}</div>'
        f'<div><div style="font-weight:700">{html.escape(name)}</div><div class="o-meta">Sales manager</div></div>'
        '<span class="online" title="Online"></span></div>',
        unsafe_allow_html=True,
    )


def side_heading(title: str, ic: str) -> None:
    st.markdown(f'<div class="side-head">{icon(ic)}{html.escape(title)}</div>', unsafe_allow_html=True)


def footer() -> None:
    st.markdown(
        '<div class="foot">Prototype tes AI Builder · data dummy dari soal tes · '
        "angka dihitung kode, kalimat ringkasan dibantu Claude</div>",
        unsafe_allow_html=True,
    )


def login_screen(check) -> None:
    """Render the login card. `check(username, password) -> bool`. Stops the script until logged in."""
    with st.container(key="login_card"):
        st.markdown(
            f'<div class="login-logo">{logo_html()}</div>'
            f'<div class="login-badge"><span class="pill pill-ai">{icon("auto_awesome", "fill")}AI-assisted</span></div>'
            '<div class="login-title">Sales Intelligence</div>'
            '<div class="login-sub">Masuk untuk melihat dashboard penjualan</div>',
            unsafe_allow_html=True,
        )
        with st.form("login", border=False):
            user = st.text_input("Username", placeholder="admin", icon=":material/person:")
            pw = st.text_input("Password", type="password", icon=":material/lock:")
            ok = st.form_submit_button("Masuk", type="primary", width="stretch", icon=":material/login:")
        if ok:
            if check(user, pw):
                st.session_state["auth_user"] = user.strip()
                st.rerun()
            else:
                st.error("Username atau password salah.")
        st.markdown(f'<div class="foot" style="margin-top:.6rem">{icon("shield_lock")} Prototype tes AI Builder · data dummy</div>',
                    unsafe_allow_html=True)
    st.stop()
