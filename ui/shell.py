"""Sidebar shared by every page: brand, profile switch, word-list picker, level and daily goal."""
from __future__ import annotations

import streamlit as st

from wortschatz import config, gamification

from . import components as C
from . import context


def sidebar() -> None:
    context.init()
    with st.sidebar:
        st.markdown('<div class="brand">Wortschatz</div>'
                    '<div class="flag"><i style="background:#1D1B19"></i><i style="background:#C8102E"></i>'
                    '<i style="background:#E3A008"></i></div>', unsafe_allow_html=True)

        st.radio("Profile", [config.PROFILE_ME, config.PROFILE_DEMO], key="profile",
                 format_func=config.PROFILE_LABELS.get, label_visibility="collapsed")
        catalog = context.catalog()
        if catalog:
            st.selectbox("Word list", list(catalog), key="wordlist", format_func=context.list_label)

        snap = context.snapshot()
        if snap.is_demo:
            st.caption("Synthetic data from a simulated learner, so the dashboards have something to show. "
                       "Your own progress is kept separately.")
            if st.button("Regenerate demo data"):
                context.ensure_demo(force=True)
                st.rerun()

        level = snap.level
        goal = st.session_state["daily_goal"]
        today = gamification.answers_today(snap.data)
        st.markdown(
            f'<div class="level-card"><div class="lv">Level {level.number} · {C.esc(level.title)}</div>'
            f'{C.progress_bar(level.progress)}<div class="sub">{snap.xp - level.floor} / {level.ceiling - level.floor} XP to the next level</div></div>'
            f'<div class="level-card"><div class="lv">Today</div>{C.progress_bar(today / goal, "goal")}'
            f'<div class="sub">{today} / {goal} answers</div></div>', unsafe_allow_html=True)
        st.slider("Daily goal (answers)", 5, 100, key="daily_goal", step=5)
