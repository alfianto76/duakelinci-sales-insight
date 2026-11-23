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

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,300..600,0..1,0&display=block');

:root {
  --brand: #D7262E;
  --brand-soft: #FDECEC;
  --ink: #1B1B1F;
  --ink-2: #55545C;
  --ink-3: #8C8A93;
  --line: #E9E6E0;
  --card: #FFFFFF;
  --up: #1F8A4C;
  --up-soft: #E7F5EC;
  --down: #C2410C;
  --down-soft: #FFF1E8;
  --ai-a: #D7262E;
  --ai-b: #7C3AED;
}
html, body, [class*="css"], .stApp, .stMarkdown, button, input, textarea, select {
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif !important;
}
.stApp { background: #F6F5F2; }
.block-container { padding-top: 1.4rem; padding-bottom: 3rem; max-width: 1280px; }
header[data-testid="stHeader"] { background: transparent; }
.ms, [data-testid="stIconMaterial"] { font-family: 'Material Symbols Rounded' !important; font-weight: normal; font-style: normal;
  line-height: 1; letter-spacing: normal; text-transform: none; white-space: nowrap; direction: ltr;
  -webkit-font-feature-settings: 'liga'; font-feature-settings: 'liga'; -webkit-font-smoothing: antialiased; }
.ms { font-size: 20px; font-variation-settings: 'FILL' 0, 'wght' 500; vertical-align: middle; }
.ms.fill { font-variation-settings: 'FILL' 1, 'wght' 500; }
.ico { width:34px; height:34px; border-radius: 11px; display:grid; place-items:center; flex:none; }
.ico.brand { background: var(--brand-soft); color: var(--brand); }
.ico.up { background: var(--up-soft); color: var(--up); }
.ico.down { background: var(--down-soft); color: var(--down); }
.ico.ai { background: linear-gradient(135deg, var(--ai-a), var(--ai-b)); color:#fff; }
.ico.sm { width:28px; height:28px; border-radius: 9px; } .ico.sm .ms { font-size: 17px; }
#MainMenu, footer { visibility: hidden; }

h1, h2, h3 { letter-spacing: -0.02em; color: var(--ink); }
.sec-title { font-size: 1.05rem; font-weight: 700; color: var(--ink); margin: 1.6rem 0 .2rem; display:flex; align-items:center; gap:.6rem; }
.sec-title .ms { color: var(--brand); font-size: 22px; }
.sec-sub { font-size: .82rem; color: var(--ink-3); margin-bottom: .7rem; }

/* header */
.topbar { display:flex; align-items:center; justify-content:space-between; gap:1rem; flex-wrap:wrap;
  background: var(--card); border:1px solid var(--line); border-radius: 18px; padding: 14px 20px; margin-bottom: 1rem; }
.brand { display:flex; align-items:center; gap:14px; }
.brand img { height: 44px; width:auto; display:block; }
.wordmark { font-weight: 800; color: var(--brand); font-size: 1.25rem; letter-spacing:-.02em; }
.brand-title { font-weight: 800; font-size: 1.15rem; color: var(--ink); line-height:1.15; }
.brand-sub { font-size: .8rem; color: var(--ink-3); }
.divider-v { width:1px; height:36px; background: var(--line); }
.pill .ms { font-size: 16px; }
.pill { display:inline-flex; align-items:center; gap:6px; font-size:.75rem; font-weight:600; padding:6px 12px; border-radius:999px; }
.pill-ai { color:#fff; background: linear-gradient(90deg, var(--ai-a), var(--ai-b)); box-shadow: 0 4px 14px rgba(124,58,237,.25); }
.pill-soft { color: var(--ink-2); background:#F1EFEA; }

/* KPI cards */
.kpis { display:grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap: 12px; }
@media (max-width: 900px) { .kpis { grid-template-columns: repeat(2, minmax(0,1fr)); } }
.kpi { background: var(--card); border:1px solid var(--line); border-radius: 16px; padding: 16px 18px; }
.kpi-top { display:flex; justify-content:space-between; align-items:flex-start; gap:8px; }
.kpi-label { font-size:.78rem; color: var(--ink-3); font-weight:600; text-transform: uppercase; letter-spacing:.04em; }
.kpi-value { font-size: 1.7rem; font-weight: 800; color: var(--ink); margin-top: 4px; letter-spacing:-.02em; }
.kpi-delta { display:inline-flex; align-items:center; gap:2px; margin-top:6px; font-size:.78rem; font-weight:700; padding:3px 8px; border-radius:8px; }
.kpi-delta.up { color: var(--up); background: var(--up-soft); }
.kpi-delta.down { color: var(--down); background: var(--down-soft); }
.kpi-delta.flat { color: var(--ink-2); background:#F1EFEA; }
.kpi-delta .ms { font-size: 16px; }

/* AI panel (st.container key="ai_panel") */
.st-key-ai_panel {
  background: linear-gradient(var(--card), var(--card)) padding-box,
              linear-gradient(120deg, var(--ai-a), var(--ai-b)) border-box;
  border: 1.5px solid transparent; border-radius: 20px; padding: 18px 20px 14px;
  box-shadow: 0 10px 30px rgba(124,58,237,.08);
}
.ai-head { display:flex; align-items:center; justify-content:space-between; gap:10px; flex-wrap:wrap; margin-bottom: 6px; }
.ai-title { font-weight:800; font-size:1.05rem; display:flex; align-items:center; gap:8px; }
.ai-spark { width:28px; height:28px; border-radius:9px; display:grid; place-items:center; color:#fff;
  background: linear-gradient(135deg, var(--ai-a), var(--ai-b)); font-size:15px; }
.ai-meta { font-size:.75rem; color: var(--ink-3); }

/* insight cards */
.insights { display:grid; grid-template-columns: repeat(auto-fit, minmax(190px,1fr)); gap: 10px; margin-top: 10px; }
.ins { border-radius: 14px; padding: 12px 14px; border:1px solid var(--line); background:#FCFBF9; }
.ins-t { font-weight:700; font-size:.88rem; display:flex; gap:10px; align-items:flex-start; line-height:1.3; }
.ins-b { font-size:.8rem; color: var(--ink-2); margin-top: 4px; line-height:1.45; }
.ins .dot { width:8px; height:8px; border-radius:50%; flex:none; }
.ins.up .dot { background: var(--up); } .ins.down .dot { background: var(--down); } .ins.alert .dot { background: var(--brand); }

/* cards around charts (st.container key starting with card_) */
[class*="st-key-card_"] { background: var(--card); border:1px solid var(--line); border-radius: 18px; padding: 16px 18px 6px; }

/* weakest outlets */
.weak { width:100%; border-collapse: separate; border-spacing: 0; font-size:.85rem; border:none !important; margin:0; }
.weak th, .weak td { border-left:none !important; border-right:none !important; border-top:none !important; background:transparent !important; }
[data-testid="stMarkdownContainer"] table.weak { display: table; }
.weak th { text-align:left; font-size:.72rem; text-transform:uppercase; letter-spacing:.04em; color: var(--ink-3); font-weight:700; padding: 8px 10px; border-bottom:1px solid var(--line); }
.weak td { padding: 12px 10px; border-bottom:1px solid #F1EFEA; vertical-align: middle; }
.weak tr:last-child td { border-bottom: none; }
.rank { width:28px; height:28px; border-radius: 9px; background: var(--brand-soft); color: var(--brand); font-weight:800; display:grid; place-items:center; }
.o-name { font-weight:700; color: var(--ink); }
.o-meta { font-size:.75rem; color: var(--ink-3); }
.bar { position:relative; height:8px; background:#F1EFEA; border-radius:99px; min-width:110px; }
.bar > span { position:absolute; left:0; top:0; bottom:0; border-radius:99px; background: var(--brand); }
.bar-l { font-size:.75rem; color: var(--ink-2); margin-top:4px; }
.chg.up { color: var(--up); font-weight:700; } .chg.down { color: var(--down); font-weight:700; }
.why { font-size:.78rem; color: var(--ink-2); }

/* sidebar */
section[data-testid="stSidebar"] { background: #FFFFFF; border-right:1px solid var(--line); }
.side-user { display:flex; align-items:center; gap:10px; padding:10px 12px; background:#F6F5F2; border-radius:12px; margin-bottom: .5rem; }
.side-head { display:flex; align-items:center; gap:8px; font-weight:700; font-size:.82rem; color: var(--ink-3);
  text-transform: uppercase; letter-spacing:.06em; margin: 1.1rem 0 .4rem; }
.side-head .ms { font-size: 18px; color: var(--ink-3); }
.online { width:9px; height:9px; border-radius:50%; background:#22C55E; border:2px solid #fff; margin-left:auto; box-shadow:0 0 0 1px #E9E6E0; }
.o-meta .ms { font-size: 14px; color: var(--ink-3); vertical-align: -2px; }
.avatar { width:32px; height:32px; border-radius:50%; background: linear-gradient(135deg, var(--ai-a), var(--ai-b)); color:#fff; display:grid; place-items:center; font-weight:800; }

/* buttons */
.stButton > button, .stFormSubmitButton > button { border-radius: 12px; font-weight: 700; }

/* login */
.st-key-login_card { max-width: 420px; margin: 7vh auto 0; background: var(--card); border:1px solid var(--line);
  border-radius: 22px; padding: 28px 28px 18px; box-shadow: 0 20px 50px rgba(27,27,31,.08); }
.login-logo { display:flex; justify-content:center; margin-bottom: 10px; }
.login-logo img { height: 84px; }
.login-badge { display:flex; justify-content:center; margin: 6px 0 2px; }
.login-title { text-align:center; font-weight:800; font-size:1.35rem; margin-top: 4px; }
.login-sub { text-align:center; color: var(--ink-3); font-size:.85rem; margin-bottom: 14px; }
.foot { text-align:center; color: var(--ink-3); font-size:.75rem; margin-top: 2rem; }
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


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
    st.markdown(f'<div class="insights">{cells}</div>', unsafe_allow_html=True)


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
