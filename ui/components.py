"""Small HTML building blocks and Streamlit compatibility helpers."""
from __future__ import annotations

import html
import inspect
from typing import Iterable

import pandas as pd
import streamlit as st

from wortschatz.gamification import Badge
from wortschatz.insights import Insight


def stretch(fn) -> dict:
    """Keyword that makes `fn` fill its container: width="stretch" on current Streamlit,
    use_container_width=True on older versions (where `width` is a plain pixel number or absent)."""
    try:
        parameter = inspect.signature(fn).parameters.get("width")
    except (TypeError, ValueError):
        parameter = None
    if parameter is not None and str(parameter.annotation).replace("'", "") not in ("int | None", "int"):
        return {"width": "stretch"}
    return {"use_container_width": True}


def run_js(script: str) -> None:
    """Run a small script in the page (used only to focus the next input). Best effort: never raises."""
    body = f"<script>{script}</script>"
    try:
        if "unsafe_allow_javascript" in inspect.signature(st.html).parameters:
            st.html(body, unsafe_allow_javascript=True)
        else:
            import streamlit.components.v1 as components
            components.html(body, height=0)
    except Exception:
        pass


def show_chart(chart) -> None:
    st.altair_chart(chart, **stretch(st.altair_chart))


def show_table(frame: pd.DataFrame, **kwargs) -> None:
    st.dataframe(frame, hide_index=True, **stretch(st.dataframe), **kwargs)


def page_link(path: str, label: str, icon: str | None = None) -> None:
    """st.page_link that degrades to plain text when a view runs outside the multipage navigation."""
    try:
        st.page_link(path, label=label, icon=icon)
    except Exception:
        st.caption(f"{icon or ''} {label}".strip())


def esc(text: object) -> str:
    return html.escape(str(text))


def tile(label: str, value: str, sub: str = "") -> str:
    sub_html = f'<div class="sub">{esc(sub)}</div>' if sub else ""
    return f'<div class="tile"><div class="label">{esc(label)}</div><div class="value">{esc(value)}</div>{sub_html}</div>'


def tiles(items: Iterable[tuple[str, str, str]]) -> None:
    items = list(items)
    for column, (label, value, sub) in zip(st.columns(len(items)), items):
        column.markdown(tile(label, value, sub), unsafe_allow_html=True)


def hero(title: str, subtitle: str) -> None:
    st.markdown(f'<div class="hero"><h1>{esc(title)}</h1><p>{esc(subtitle)}</p></div>', unsafe_allow_html=True)


def chips(*labels: str, hot: Iterable[str] = ()) -> str:
    hot = set(hot)
    return "".join(f'<span class="chip{" hot" if label in hot else ""}">{esc(label)}</span>' for label in labels if label)


def insight_card(item: Insight) -> None:
    st.markdown(f'<div class="insight {item.tone}"><b>{esc(item.icon)} {esc(item.title)}</b>{esc(item.text)}</div>',
                unsafe_allow_html=True)


def badge_grid(badges: list[Badge], per_row: int = 5) -> None:
    for start in range(0, len(badges), per_row):
        row = badges[start:start + per_row]
        for column, badge in zip(st.columns(per_row), row):
            when = f"{badge.earned_on:%d %b %Y}" if badge.earned else badge.description
            column.markdown(
                f'<div class="badge{"" if badge.earned else " locked"}"><div class="ico">{badge.icon}</div>'
                f'<div class="t">{esc(badge.title)}</div><div class="d">{esc(when)}</div></div>', unsafe_allow_html=True)


def progress_bar(fraction: float, kind: str = "") -> str:
    return f'<div class="bar {kind}"><span style="width:{max(0.0, min(1.0, fraction)) * 100:.0f}%"></span></div>'


def note(text: str) -> None:
    st.markdown(f'<div class="note">{esc(text)}</div>', unsafe_allow_html=True)
