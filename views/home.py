import streamlit as st

from ui import charts, components as C, context
from wortschatz import analytics, config, gamification, insights, srs

context.init()
snap = context.snapshot()

C.hero("Guten Tag!", "Learn the most useful German words first. Every answer is logged and analysed, "
                     "so you always know what to practise next.")
st.write("")


def use_demo() -> None:
    st.session_state["profile"] = config.PROFILE_DEMO


if snap.events.empty and not snap.is_demo:
    left, right = st.columns(2)
    with left:
        st.markdown('<div class="card" style="min-height:9.5rem"><h4>🎮 Start your first session</h4>'
                    'A session mixes new words with reviews and gets harder as a word sticks. '
                    'Plan on five minutes.</div>', unsafe_allow_html=True)
        C.page_link("views/play.py", "Play now", "▶️")
    with right:
        st.markdown('<div class="card" style="min-height:9.5rem"><h4>🔬 Explore the analytics first</h4>'
                    'Switch to the demo profile: a month of synthetic practice so every chart has data. '
                    'Your own progress stays separate.</div>', unsafe_allow_html=True)
        st.button("Open the demo profile", on_click=use_demo)
else:
    seen = snap.states.index
    list_ids = set(snap.words["word_id"])
    due = [w for w in srs.due_ids(snap.states, snap.now) if w in list_ids]
    unseen = len(list_ids - set(seen))
    k = analytics.kpis(snap.data, snap.states, snap.now.date())
    C.tiles([
        ("Due for review", str(len(due)), "words ready now"),
        ("New words left", str(unseen), f"in {context.list_label(snap.list_name or '')}"),
        ("Mastered", str(k["words_mastered"]), f"of {k['words_seen']} words met"),
        ("Streak", f"{k['streak']} d", f"best {k['best_streak']} d"),
        ("Accuracy", f"{100 * k['accuracy']:.0f}%" if k["answers"] else "–", f"{k['answers']} answers"),
    ])
    st.write("")
    if snap.is_demo:
        st.info("You are viewing the synthetic demo profile. Switch to **My progress** in the sidebar to play and "
                "record real answers.", icon="🧪")
    else:
        C.page_link("views/play.py", "Start today's session", "▶️")

    st.subheader("What the data says")
    findings = insights.generate(snap.data, snap.states, snap.catalog_words, snap.now)
    if findings:
        for item in findings[:4]:
            C.insight_card(item)
        C.page_link("views/progress.py", "See the full analysis", "📈")
    else:
        C.note("Answer a few more questions and findings will appear here.")

    st.subheader("Activity")
    span_weeks = (snap.now.date() - snap.data["day"].min().date()).days // 7 + 2
    C.show_chart(charts.calendar_heatmap(analytics.calendar_grid(snap.data, weeks=min(26, max(12, span_weeks)), today=snap.now.date())))

    st.subheader("Badges")
    C.badge_grid(gamification.evaluate_badges(snap.data, snap.states))
