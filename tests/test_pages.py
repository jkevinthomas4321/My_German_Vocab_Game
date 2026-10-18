"""End-to-end tests: drive the real Streamlit pages headlessly against a temporary data folder."""
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from tests.conftest import ROOT
from wortschatz import config, events, srs, wordlist

VIEWS = ["home", "play", "progress", "datalab", "library", "about"]
START = "▶️  Start session"


def open_view(name: str, profile: str = config.PROFILE_ME, **state) -> AppTest:
    at = AppTest.from_file(str(ROOT / "views" / f"{name}.py"), default_timeout=90)
    at.session_state["profile"] = profile
    for key, value in state.items():
        at.session_state[key] = value
    return at.run()


def click(at: AppTest, label: str) -> AppTest:
    return next(b for b in at.button if b.label == label).click().run()


def chart_count(at: AppTest) -> int:
    """Vega-Lite elements, whichever name this Streamlit version gives them."""
    return len(at.get("arrow_vega_lite_chart")) + len(at.get("vega_lite_chart"))


def no_exception(at: AppTest) -> None:
    assert not at.exception, [e.value for e in at.exception]


def start(at: AppTest, mode: str = "smart", count: int = 5) -> AppTest:
    at.radio(key="play_mode").set_value(mode).run()
    at.slider(key="play_count").set_value(count).run()
    return click(at, START)


def answer(at: AppTest, correct: bool = True, text: str | None = None) -> AppTest:
    run = at.session_state["run"]
    q = run["questions"][run["idx"]]
    if q.qtype in ("choose_en", "choose_de", "article"):
        options = q.options
        pick = q.answer if correct else next(o for o in options if o != q.answer)
        return click(at, pick)
    if q.qtype == "forms":
        past, perfect = (q.past_tense, q.perfect_tense) if correct else ("-", "-")
        at.text_input[0].set_value(past)
        at.text_input[1].set_value(perfect)
    else:
        at.text_input[0].set_value(text if text is not None else (q.answer if correct else "-"))
    return click(at, "Check")


def proceed(at: AppTest) -> AppTest:
    """Click Next (or Finish on the last question) if the feedback screen is showing."""
    run = at.session_state["run"]
    if run["phase"] != "feedback":
        return at
    return click(at, "Finish session" if run["idx"] + 1 >= len(run["questions"]) else "Next →")


def play_through(at: AppTest, correct: bool = True) -> AppTest:
    for _ in range(80):
        run = at.session_state["run"]
        if run["phase"] == "done":
            return at
        if run["phase"] == "ask":
            at = answer(at, correct)
        else:
            at = click(at, "Finish session" if run["idx"] + 1 >= len(run["questions"]) else "Next →")
        no_exception(at)
    raise AssertionError("session never finished")


# ----------------------------------------------------------------------------- every page
@pytest.mark.parametrize("profile", [config.PROFILE_ME, config.PROFILE_DEMO])
@pytest.mark.parametrize("view", VIEWS)
def test_every_view_loads(view, profile):
    no_exception(open_view(view, profile))


def test_the_real_entry_point_with_navigation_loads():
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=90).run()
    no_exception(at)
    assert len(at.sidebar.radio) == 1 and len(at.sidebar.selectbox) == 1          # profile switch + word list picker
    assert any("Guten Tag" in m.value for m in at.markdown)                        # the Home page ran inside the navigation


def test_demo_profile_is_generated_on_first_use(isolated_user_dir):
    assert not (isolated_user_dir / "demo").exists()
    open_view("progress", config.PROFILE_DEMO)
    assert len(events.load_events(config.PROFILE_DEMO)) > 300


def test_dashboards_render_charts_and_findings_for_the_demo():
    progress = open_view("progress", config.PROFILE_DEMO)
    no_exception(progress)
    assert len(progress.tabs) == 5 and chart_count(progress) >= 12
    assert any("Repetition pays off" in m.value for m in progress.markdown)
    datalab = open_view("datalab", config.PROFILE_DEMO)
    assert len(datalab.tabs) == 4 and chart_count(datalab) == 3


def test_progress_asks_for_data_when_empty():
    at = open_view("progress")
    assert any("No answers yet" in i.value for i in at.info)


def test_home_onboarding_leads_to_the_demo_profile():
    at = open_view("home")
    click(at, "Open the demo profile")
    assert at.session_state["profile"] == config.PROFILE_DEMO


# ----------------------------------------------------------------------------- playing
def test_setup_shows_what_is_due_and_what_is_new():
    text = " ".join(m.value for m in open_view("play").markdown)
    assert "Due now" in text and "New available" in text and ">515<" in text


def test_the_demo_profile_is_read_only():
    at = open_view("play", config.PROFILE_DEMO)
    assert any("read-only" in i.value for i in at.info) and not [b for b in at.button if b.label == START]


def test_a_perfect_session_is_logged_once_per_answer():
    at = start(open_view("play"), "smart", 5)
    assert at.session_state["run"]["phase"] == "ask" and len(at.session_state["run"]["questions"]) == 5
    at = play_through(at, correct=True)
    log = events.load_events("me")
    assert len(log) == 5 and log["correct"].tolist() == [1] * 5 and (log["retry"] == 0).all() and log["session_id"].nunique() == 1
    assert log["response_ms"].between(0, 60000).all()
    summary = " ".join(m.value for m in at.markdown)
    assert "Session complete" in summary and "100%" in summary and "+" in summary


def test_logging_does_not_repeat_when_the_page_reruns():
    at = start(open_view("play"), "smart", 5)
    at = answer(at)
    assert len(events.load_events("me")) == 1
    at.run()
    at.run()
    assert len(events.load_events("me")) == 1


def test_wrong_answers_come_back_once_as_ungraded_retries():
    at = play_through(start(open_view("play"), "smart", 5), correct=False)
    log = events.load_events("me")
    assert len(log) == 10 and log["retry"].tolist() == [0] * 5 + [1] * 5 and log["correct"].sum() == 0
    graded = srs.replay(log)
    assert len(graded) == 5 and graded["attempts"].tolist() == [1] * 5          # retries do not count as attempts
    assert "0%" in " ".join(m.value for m in at.markdown)


def test_typing_a_dash_is_wrong_in_type_mode():
    at = start(open_view("play"), "type", 5)
    for _ in range(5):
        at = proceed(answer(at, text="-"))
    assert events.load_events("me")["correct"].sum() == 0


def test_typed_answers_are_graded_by_the_real_grader():
    at = start(open_view("play"), "type", 5)
    for _ in range(5):
        q = at.session_state["run"]["questions"][at.session_state["run"]["idx"]]
        at = proceed(answer(at, text=q.answer.upper()))              # right word, wrong capitalisation
    assert events.load_events("me")["correct"].tolist() == [1] * 5


def test_i_dont_know_logs_a_miss():
    at = start(open_view("play"), "type", 5)
    at = click(at, "I don't know")
    log = events.load_events("me")
    assert len(log) == 1 and log["correct"].iloc[0] == 0 and log["given"].iloc[0].strip(" |") == ""
    assert any("Not quite" in m.value for m in at.markdown)


def test_article_trainer_logs_the_article_claim():
    at = start(open_view("play"), "article", 5)
    at = play_through(at, correct=False)
    log = events.graded(events.load_events("me"))
    assert (log["qtype"] == "article").all() and (log["article_given"] != log["article_expected"]).all() and (log["article_given"] != "").all()


def test_verb_form_questions():
    at = start(open_view("play"), "forms", 5)
    assert all(q.qtype == "forms" for q in at.session_state["run"]["questions"])
    at = play_through(at, correct=True)
    assert events.load_events("me")["correct"].tolist() == [1] * 5


def test_ending_a_session_keeps_the_answers_already_given():
    at = start(open_view("play"), "smart", 5)
    at = answer(at)
    at = click(at, "✕ End")
    assert "run" not in at.session_state and len(events.load_events("me")) == 1
    assert any(b.label == START for b in at.button)


def test_practise_the_misses_starts_a_session_with_those_words():
    at = play_through(start(open_view("play"), "smart", 5), correct=False)
    missed = {r["q"].word_id for r in at.session_state["run"]["log"] if not r["q"].retry}
    at = click(at, "🎯 Practise the misses")
    assert at.session_state["run"]["phase"] == "ask" and {q.word_id for q in at.session_state["run"]["questions"]} == missed


def test_second_session_reviews_what_the_first_one_taught():
    play_through(start(open_view("play"), "smart", 5), correct=True)
    at = open_view("play")
    assert at.radio(key="play_mode").value == "smart"
    due = pd.Timestamp.now() + pd.Timedelta(days=2)
    states = srs.replay(events.load_events("me"))
    assert (states["box"] == 1).all() and (states["due"] < due).all()


def test_weak_spots_mode_waits_for_real_misses():
    at = open_view("play")
    at.radio(key="play_mode").set_value("weak").run()
    assert any("No weak spots yet" in i.value for i in at.info)


def test_class_filter_is_respected():
    at = open_view("play")
    at.multiselect(key="play_classes").set_value(["verb"]).run()
    at = start(at, "smart", 5)
    assert {q.word_class for q in at.session_state["run"]["questions"]} == {"verb"}


# ----------------------------------------------------------------------------- word lists
def test_library_lists_bundled_and_uploaded_lists(mini_words):
    wordlist.save_upload(mini_words, "my_list")
    at = open_view("library")
    no_exception(at)
    table = at.dataframe[-1].value
    assert set(table["List"]) == {"german_core", "my_list"} and table.set_index("List").loc["my_list", "Source"] == "uploaded"


def test_play_uses_the_selected_word_list(mini_words):
    wordlist.save_upload(mini_words, "tiny")
    at = start(open_view("play", wordlist="tiny"), "smart", 5)
    assert {q.german for q in at.session_state["run"]["questions"]} <= set(mini_words["german"])
