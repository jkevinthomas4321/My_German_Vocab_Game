"""Wortschatz: a German vocabulary trainer with a learning-analytics dashboard.

Run with:   streamlit run app.py
"""
import streamlit as st

from ui import shell, theme

st.set_page_config(page_title="Wortschatz · German vocabulary trainer", page_icon="🇩🇪", layout="wide",
                   initial_sidebar_state="expanded")
theme.inject()

navigation = st.navigation([
    st.Page("views/home.py", title="Home", icon="🏠", default=True),
    st.Page("views/play.py", title="Play", icon="🎮"),
    st.Page("views/progress.py", title="Progress", icon="📈"),
    st.Page("views/datalab.py", title="Data lab", icon="🔬"),
    st.Page("views/library.py", title="Word lists", icon="📚"),
    st.Page("views/about.py", title="About", icon="ℹ️"),
], position="top")
shell.sidebar()
navigation.run()
