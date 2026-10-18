"""Play: one question at a time, instant feedback, a summary at the end.

State lives in st.session_state["run"]. Every transition happens in an on_click callback, which
Streamlit runs exactly once per click, so an answer is logged exactly once however often the page reruns.
"""
import random
import time
from datetime import datetime

import pandas as pd
import streamlit as st

from ui import components as C, context
from wortschatz import analytics, config, events, gamification, grading, questions

context.init()
RUN = "run"
MODE_ORDER = ["smart", "article", "type", "forms", "weak"]


# ----------------------------------------------------------------------------- state transitions
def start(mode: str, count: int, classes: list[str], word_ids: list[str] | None = None) -> None:
    snap = context.snapshot()
    plan = questions.plan_session(snap.words, snap.states, mode, count, snap.now, random.Random(), classes or None, word_ids)
    if not plan:
        st.session_state["play_error"] = "There are no words for this combination. Pick another mode or word list."
        return
    st.session_state.pop("play_error", None)
    seen = set(snap.states.index)
    st.session_state[RUN] = {
        "id": events.new_session_id(), "profile": snap.profile, "mode": mode, "questions": plan, "idx": 0,
        "phase": "ask", "shown": time.time(), "started": time.time(), "log": [], "xp": 0, "combo": 0, "best_combo": 0,
        "last": None, "xp_before": snap.xp, "new_ids": {q.word_id for q in plan if q.word_id not in seen},
    }


def submit(response) -> None:
    run = st.session_state[RUN]
    if run["phase"] != "ask":
        return
    question = run["questions"][run["idx"]]
    ms = int((time.time() - run["shown"]) * 1000)
    grade = grading.grade(question, response)
    events.append_events([grading.to_event(question, grade, datetime.now().replace(microsecond=0), run["id"], ms)],
                         run["profile"])
    gain = 0
    if not question.retry:
        gain = config.XP_CORRECT * grade.correct + (config.XP_FAST_BONUS if grade.correct and ms <= config.FAST_MS else 0)
    run["xp"] += gain
    run["combo"] = run["combo"] + 1 if grade.correct else 0
    run["best_combo"] = max(run["best_combo"], run["combo"])
    if not grade.correct and not question.retry:
        run["questions"].append(questions.retry_of(question))       # one more look at the end of the session
    run["log"].append({"q": question, "grade": grade, "ms": ms, "gain": gain})
    run["last"] = run["log"][-1]
    run["phase"] = "feedback"


def submit_form(keys: list[str], skip: bool = False) -> None:
    values = ["" if skip else st.session_state.get(k, "") for k in keys]
    submit(values[0] if len(values) == 1 else tuple(values))


def advance() -> None:
    run = st.session_state[RUN]
    run["idx"] += 1
    run["phase"] = "done" if run["idx"] >= len(run["questions"]) else "ask"
    run["shown"] = time.time()


def reset() -> None:
    st.session_state.pop(RUN, None)


def focus(target: str) -> None:
    """Move keyboard focus to the first text box or the primary button so a whole session works from the keyboard."""
    C.run_js("(() => { const d = (window.parent && window.parent !== window) ? window.parent.document : document;"
             f" setTimeout(() => {{ const el = d.querySelector('{target}'); if (el) el.focus(); }}, 150); }})();")


# ----------------------------------------------------------------------------- screens
def render_setup(snap: context.Snapshot) -> None:
    if snap.is_demo:
        st.info("The demo profile is read-only. Switch to **My progress** in the sidebar to play.", icon="🧪")
        return
    if snap.words.empty:
        st.warning("No word list available. Add one on the Word lists page.")
        return
    if error := st.session_state.get("play_error"):
        st.error(error)

    mode = st.radio("Mode", MODE_ORDER, horizontal=True, format_func=questions.MODES.get, key="play_mode")
    st.caption(questions.MODE_HELP[mode])

    ids = set(snap.words["word_id"])
    due = [w for w in snap.states.index[snap.states["due"] <= pd.Timestamp(snap.now)] if w in ids] if len(snap.states) else []
    weak = int(((snap.states["wrong"] > 0) & (snap.states["attempts"] >= 2)).sum()) if len(snap.states) else 0
    unseen = len(ids - set(snap.states.index))
    if mode == "smart":
        C.tiles([("Due now", str(len(due)), "reviews"), ("New available", str(unseen), "never seen"), ("In this list", str(len(ids)), "words")])
    elif mode == "weak" and weak == 0:
        st.info("No weak spots yet. Words you miss more than once will show up here.")
        return

    classes: list[str] = []
    if mode in ("smart", "type", "weak"):
        present = [c for c in config.WORD_CLASSES if c in set(snap.words["word_class"])]
        classes = st.multiselect("Only these word classes (optional)", present, key="play_classes")
    count = st.slider("Questions", 5, 30, 15, step=1, key="play_count")
    st.button("▶️  Start session", type="primary", on_click=start, args=(mode, count, classes))


def render_header(run: dict) -> None:
    total = len(run["questions"])
    st.progress(min(run["idx"], total) / total)
    left, middle, right = st.columns([5, 2, 1])
    left.caption(f"Question {min(run['idx'] + 1, total)} of {total}")
    combo = f"🔥 ×{run['combo']}  ·  " if run["combo"] >= 2 else ""
    middle.markdown(f"<div style='text-align:right' class='note'>{combo}+{run['xp']} XP</div>", unsafe_allow_html=True)
    right.button("✕ End", on_click=reset, help="Leave the session. Answers already given are kept.")


def question_card(q: questions.Question) -> None:
    eyebrow = {"choose_en": "What does this mean?", "choose_de": "Which is the German word?",
               "type_de": "Type the German word" + (" with its article" if q.article else ""),
               "article": "Which article?", "forms": "Type the Präteritum and the Perfekt"}[q.qtype]
    tags = C.chips(questions.QTYPE_LABELS[q.qtype], q.word_class, "Try again" if q.retry else "", hot=["Try again"])
    prompt = q.prompt
    sub = q.english if q.qtype == "forms" else ""
    st.markdown(f'<div class="qcard"><div class="eyebrow">{C.esc(eyebrow)}</div><div class="prompt">{C.esc(prompt)}</div>'
                f'<div class="hint">{C.esc(sub)}</div><div style="margin-top:.8rem">{tags}</div></div>', unsafe_allow_html=True)


def render_question(run: dict) -> None:
    q = run["questions"][run["idx"]]
    question_card(q)
    base = f"{run['id']}_{run['idx']}"

    if q.qtype in ("choose_en", "choose_de"):
        with st.container(key="choices"):
            for row in range(0, len(q.options), 2):
                for column, option in zip(st.columns(2), q.options[row:row + 2]):
                    column.button(option, key=f"{base}_opt_{q.options.index(option)}", on_click=submit, args=(option,),
                                  **C.stretch(st.button))
    elif q.qtype == "article":
        with st.container(key="articles"):
            for column, article in zip(st.columns(3), q.options):
                column.button(article, key=f"{base}_art_{article}", on_click=submit, args=(article,), **C.stretch(st.button))
    else:
        fields = [("past", "Präteritum (e.g. ging)"), ("perfect", "Perfekt (e.g. ist gegangen)")] if q.qtype == "forms" \
            else [("answer", "Your answer")]
        keys = [f"{base}_{name}" for name, _ in fields]
        with st.form(f"form_{base}", border=False):
            for key, (_, label) in zip(keys, fields):
                st.text_input(label, key=key, autocomplete="off")
            check, skip = st.columns([3, 1])
            check.form_submit_button("Check", type="primary", on_click=submit_form, args=(keys,), **C.stretch(st.form_submit_button))
            skip.form_submit_button("I don't know", on_click=submit_form, args=(keys, True), **C.stretch(st.form_submit_button))
        focus("input[type=text]")


def render_feedback(run: dict) -> None:
    last = run["last"]
    q, grade = last["q"], last["grade"]
    question_card(q)
    if grade.correct:
        bonus = " ⚡ fast" if last["gain"] > config.XP_CORRECT else ""
        head = f"✅ Richtig!  <span class='note'>+{last['gain']} XP{bonus}</span>" if last["gain"] else "✅ Richtig!"
        body = f'<div class="answer">{C.esc(grade.expected)}</div>'
    else:
        head = "❌ Not quite" + (" — so close, check the spelling" if grade.near_miss else "")
        body = (f'<div class="answer">{C.esc(grade.expected)}</div>'
                f'<div class="tip">You answered: {C.esc(grade.given) if grade.given.strip(" |") else "(nothing)"}'
                f'{(" · " + C.esc(grade.message)) if grade.message else ""}</div>')
    st.markdown(f'<div class="fb {"ok" if grade.correct else "bad"}"><div class="head">{head}</div>{body}'
                f'<div class="tip">📌 {C.esc(questions.info_line(q))}</div></div>', unsafe_allow_html=True)
    final = run["idx"] + 1 >= len(run["questions"])
    st.button("Finish session" if final else "Next →", type="primary", on_click=advance, **C.stretch(st.button))
    focus("button[kind=primary]")


def render_done(run: dict, snap: context.Snapshot) -> None:
    graded = [r for r in run["log"] if not r["q"].retry]
    right = sum(r["grade"].correct for r in graded)
    seconds = time.time() - run["started"]
    st.markdown("### Session complete")
    C.tiles([
        ("Score", f"{100 * right / len(graded):.0f}%", f"{right} of {len(graded)} correct"),
        ("XP earned", f"+{run['xp']}", f"best combo ×{run['best_combo']}"),
        ("New words met", str(len(run["new_ids"])), "added to your reviews"),
        ("Time", f"{seconds / 60:.1f} min", f"{seconds / max(len(graded), 1):.0f} s per question"),
    ])
    before, after = gamification.level_for(run["xp_before"]), snap.level
    if after.number > before.number:
        st.balloons()
        st.success(f"Level up! You are now level {after.number}: {after.title}.", icon="🎉")

    missed = [r for r in graded if not r["grade"].correct]
    if missed:
        st.markdown("#### Review these")
        C.show_table(pd.DataFrame({
            "English": [r["q"].english for r in missed],
            "You answered": [r["grade"].given.strip(" |") or "(nothing)" for r in missed],
            "Correct": [questions.info_line(r["q"]) for r in missed],
        }))
    else:
        st.success("Flawless: nothing to review.", icon="✨")

    left, right_col = st.columns(2)
    left.button("🔁 New session", type="primary", on_click=reset, **C.stretch(st.button))
    if missed:
        right_col.button("🎯 Practise the misses", on_click=lambda ids: (reset(), start("smart", min(len(ids) , 30), [], ids)),
                         args=([r["q"].word_id for r in missed],), **C.stretch(st.button))


# ----------------------------------------------------------------------------- page
st.title("Play")
snap = context.snapshot()
run = st.session_state.get(RUN)
if run is None:
    render_setup(snap)
else:
    if run["phase"] != "done":
        render_header(run)
    if run["phase"] == "ask":
        render_question(run)
    elif run["phase"] == "feedback":
        render_feedback(run)
    else:
        render_done(run, snap)
