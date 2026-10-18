"""Colour palette and the page-level CSS."""
from __future__ import annotations

import streamlit as st

INK = "#1D1B19"
MUTED = "#6F6A63"
LINE = "#E7E0D5"
PAPER = "#FBF8F3"
SURFACE = "#FFFFFF"

BLUE = "#2A6F97"        # primary data colour; "correct"
ORANGE = "#E07A1F"      # "wrong"  (blue/orange stays distinguishable for colour-blind readers)
GOLD = "#E3A008"
RED = "#C8102E"
GREEN = "#2F855A"
GREY = "#B9B2A6"

ARTICLE_COLORS = {"der": BLUE, "die": RED, "das": GOLD}
STATUS_COLORS = {"Unseen": GREY, "Learning": ORANGE, "Reviewing": BLUE, "Mastered": GREEN}
CLASS_COLORS = {"noun": BLUE, "verb": ORANGE, "adjective": GREEN, "adverb": GOLD, "preposition": "#7B5EA7",
                "conjunction": "#B5476B", "interjection": GREY, "other": "#8C8C8C"}

CSS = f"""
<style>
:root {{
  --ink: {INK}; --muted: {MUTED}; --line: {LINE}; --paper: {PAPER}; --surface: {SURFACE};
  --blue: {BLUE}; --orange: {ORANGE}; --gold: {GOLD}; --red: {RED}; --green: {GREEN};
}}
.block-container {{ padding-top: 2.2rem; max-width: 1180px; }}
h1, h2, h3 {{ letter-spacing: -0.01em; }}
.serif {{ font-family: "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif; }}

/* ---- sidebar brand + level card ---- */
.brand {{ font-family: "Iowan Old Style", "Palatino Linotype", Georgia, serif; font-size: 1.7rem; font-weight: 700;
         line-height: 1.1; margin-bottom: .1rem; }}
.flag {{ display: flex; height: 5px; border-radius: 3px; overflow: hidden; margin: .35rem 0 .9rem 0; }}
.flag i {{ flex: 1; display: block; }}
.level-card {{ background: var(--surface); border: 1px solid var(--line); border-radius: 14px; padding: .8rem .9rem; margin: .6rem 0; }}
.level-card .lv {{ font-weight: 700; }}
.level-card .sub {{ color: var(--muted); font-size: .8rem; }}
.bar {{ background: #EFE8DC; border-radius: 6px; height: 8px; overflow: hidden; margin: .45rem 0 .25rem 0; }}
.bar > span {{ display: block; height: 100%; background: linear-gradient(90deg, var(--gold), var(--orange)); border-radius: 6px; }}
.bar.goal > span {{ background: linear-gradient(90deg, var(--blue), #4C9BC4); }}

/* ---- generic cards ---- */
.card {{ background: var(--surface); border: 1px solid var(--line); border-radius: 16px; padding: 1.1rem 1.25rem; }}
.card h4 {{ margin: 0 0 .35rem 0; font-size: 1rem; }}
.tile {{ background: var(--surface); border: 1px solid var(--line); border-radius: 14px; padding: .85rem 1rem; height: 100%; }}
.tile .label {{ color: var(--muted); font-size: .78rem; text-transform: uppercase; letter-spacing: .06em; }}
.tile .value {{ font-size: 1.85rem; font-weight: 700; line-height: 1.15; }}
.tile .sub {{ color: var(--muted); font-size: .82rem; }}
.hero {{ background: linear-gradient(135deg, #1D1B19 0%, #34302B 100%); color: #FBF8F3; border-radius: 22px;
        padding: 2rem 2.2rem; position: relative; overflow: hidden; }}
.hero:after {{ content: ""; position: absolute; right: 0; top: 0; bottom: 0; width: 14px;
              background: linear-gradient(#1D1B19 0 33.3%, {RED} 33.3% 66.6%, {GOLD} 66.6% 100%); }}
.hero h1 {{ font-family: "Iowan Old Style", "Palatino Linotype", Georgia, serif; margin: 0 0 .3rem 0; font-size: 2.3rem; color: #FBF8F3; }}
.hero p {{ margin: 0; color: #D8D1C4; font-size: 1.02rem; }}
.chip {{ display: inline-block; border: 1px solid var(--line); background: var(--surface); color: var(--muted);
        border-radius: 999px; padding: .12rem .65rem; font-size: .78rem; margin-right: .35rem; }}
.chip.hot {{ background: #FFF4D6; border-color: #F0D58A; color: #7A5A00; }}
.insight {{ border-left: 5px solid var(--blue); background: var(--surface); border-radius: 10px; padding: .7rem 1rem; margin-bottom: .6rem;
           border-top: 1px solid var(--line); border-right: 1px solid var(--line); border-bottom: 1px solid var(--line); }}
.insight.good {{ border-left-color: var(--green); }}
.insight.watch {{ border-left-color: var(--orange); }}
.insight b {{ display: block; margin-bottom: .1rem; }}
.badge {{ text-align: center; background: var(--surface); border: 1px solid var(--line); border-radius: 14px; padding: .8rem .4rem; height: 100%; }}
.badge .ico {{ font-size: 1.7rem; }}
.badge .t {{ font-weight: 700; font-size: .88rem; }}
.badge .d {{ color: var(--muted); font-size: .72rem; }}
.badge.locked {{ opacity: .45; filter: grayscale(1); }}
.note {{ color: var(--muted); font-size: .86rem; }}

/* ---- question card ---- */
.qcard {{ background: var(--surface); border: 1px solid var(--line); border-radius: 22px; padding: 2.2rem 1.5rem 1.8rem 1.5rem;
         text-align: center; box-shadow: 0 8px 28px rgba(29,27,25,.06); margin: .6rem 0 1rem 0; }}
.qcard .eyebrow {{ color: var(--muted); font-size: .8rem; text-transform: uppercase; letter-spacing: .09em; }}
.qcard .prompt {{ font-family: "Iowan Old Style", "Palatino Linotype", Georgia, serif; font-size: 3rem; font-weight: 700;
                 line-height: 1.15; margin: .35rem 0 .2rem 0; word-break: break-word; }}
.qcard .hint {{ color: var(--muted); }}
.fb {{ border-radius: 16px; padding: 1rem 1.3rem; margin: .4rem 0 1rem 0; border: 1px solid var(--line); border-left-width: 6px; }}
.fb.ok {{ background: #F0FAF4; border-left-color: var(--green); }}
.fb.bad {{ background: #FFF4F2; border-left-color: var(--red); }}
.fb .head {{ font-size: 1.25rem; font-weight: 700; }}
.fb .answer {{ font-family: "Iowan Old Style", "Palatino Linotype", Georgia, serif; font-size: 1.7rem; font-weight: 700; }}
.fb .tip {{ color: var(--muted); margin-top: .3rem; }}

/* big answer buttons, scoped to the container keyed "choices" */
.st-key-choices button {{ min-height: 3.6rem; font-size: 1.12rem; border-radius: 14px; }}
.st-key-articles button {{ min-height: 4.2rem; font-size: 1.5rem; font-weight: 700; border-radius: 16px; }}
.st-key-articles [data-testid="stColumn"]:nth-child(1) button {{ border-color: {BLUE}; color: {BLUE}; }}
.st-key-articles [data-testid="stColumn"]:nth-child(2) button {{ border-color: {RED}; color: {RED}; }}
.st-key-articles [data-testid="stColumn"]:nth-child(3) button {{ border-color: #B07F00; color: #8A6400; }}
[data-testid="stSidebar"] {{ border-right: 1px solid var(--line); }}
@media (max-width: 640px) {{ .qcard .prompt {{ font-size: 2.2rem; }} .hero h1 {{ font-size: 1.7rem; }} }}
</style>
"""


def inject() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
