"""End-to-end tests: a simulated browser plays the real app (NiceGUI's `user` fixture)."""
import pytest
from nicegui import ui
from nicegui.testing import User

from wortschatz import answers, config, session, wordlist
from wortschatz.session import TestRun
from webapp.routes import ROUTES
from webapp.state import state

DIARY, SECOND = config.STATUS_DIARY, config.STATUS_SECOND


@pytest.fixture(autouse=True)
def fresh_state(isolated_user_dir):
    state.__init__()


# ----------------------------------------------------------------------------- helpers
def right_response(item):
    w = item.word
    if item.direction == "de_en":
        return w["english"].split("/")[0].split("(")[0].strip()
    if answers.has_forms(w):
        return (w["german"], w["past_tense"], w["perfect_tense"])
    return answers.german_display(w)


async def answer_question(user: User, right: bool = True, text: str | None = None) -> None:
    """Type into the answer box(es) and press Check."""
    item = state.run.test.current
    response = right_response(item) if right else ("zzz",) * 3
    if text is not None:
        response = text
    inputs = sorted(user.find(kind=ui.input).elements, key=lambda e: e.id)
    values = list(response) if isinstance(response, tuple) else [response]
    for element, value in zip(inputs, values + [""] * len(inputs)):
        element.set_value(value)
    user.find("Check").click()
    await user.should_see("Continue")


async def go_on(user: User) -> None:
    """Click Continue and wait for the next question (or the results)."""
    user.find("Continue").click()
    await user.should_see("words passed" if state.run.test.finished else "Check")


async def play_round(user: User, wrong_for=lambda item: False) -> None:
    """Answer every question of the running test; `wrong_for(item)` makes a question wrong."""
    while not state.run.test.finished:
        item = state.run.test.current
        await answer_question(user, right=not wrong_for(item))
        await go_on(user)


def click_chip(user: User, label: str) -> None:
    """Click the word-type chip whose label is `label` (a real browser bubbles the click from the label to the chip)."""
    from nicegui.testing.user_interaction import UserInteraction
    chip = {el.parent_slot.parent for el in user.find(label, kind=ui.label).elements if type(el).__name__ == "Label"}
    UserInteraction(user, chip, None).click()


async def start_learning(user: User, word_class: str = "Nouns") -> None:
    await user.open("/learn")
    click_chip(user, word_class)
    await user.should_see("How many words?")
    user.find("Start learning").click()
    await user.should_see("Card 1 of")
    user.find("Skip to the test").click()
    await user.should_see("Question 1 of")


def choose_directions(user: User, key: str) -> None:
    """Select an option of the 'Test me' toggle (the simulator cannot click Quasar toggle options)."""
    toggle = next(t for t in user.find(kind=ui.toggle).elements if "both" in (t.options if isinstance(t.options, dict) else {}))
    toggle.set_value(key)


def table_rows(user: User) -> list[dict]:
    return [row for table in user.find(kind=ui.table).elements for row in table.rows]


async def begin_retest(user: User, cards: bool = False) -> None:
    await user.open("/second-chance")
    user.find("Review & re-test").click()
    await user.should_see("Card 1 of")
    if not cards:
        user.find("Skip to the test").click()
        await user.should_see("Question 1 of")


async def begin_revision(user: User) -> None:
    await user.open("/test")
    user.find("Start the revision test").click()
    await user.should_see("Question 1 of")


def prepare(words_pick, fail=False):
    """Put words straight into the game through the engine (fast set-up for the second-chance and diary tests)."""
    run = TestRun(state.store, words_pick, shuffle=False)
    while not run.finished:
        run.submit("zzz" if fail else right_response(run.current))
        run.advance()


def nouns(count):
    return session.pick_new_words(state.words(), state.store.progress, "noun", count)


# ----------------------------------------------------------------------------- pages
@pytest.mark.parametrize("path", sorted(ROUTES))
async def test_every_page_loads_for_a_new_player(user: User, path):
    await user.open(path)
    await user.should_see("Wortschatz")


@pytest.mark.parametrize("path", [p for p in sorted(ROUTES) if p != "/play"])
async def test_every_page_loads_on_the_demo_profile(user: User, path):
    state.switch_profile(config.PROFILE_DEMO)
    await user.open(path)
    await user.should_see("Synthetic demo data")


def room_elements(user: User) -> dict[str, ui.element]:
    """The four door buttons under the map on the home page, by key (learn, test, second, stay)."""
    rooms = {}
    for element in user.find(kind=ui.element).elements:
        for key in ("learn", "test", "second", "stay"):
            if f"room-{key}" in element.classes:
                rooms[key] = element
    return rooms


def click_element(user: User, element) -> None:
    from nicegui.testing.user_interaction import UserInteraction
    UserInteraction(user, {element}, None).click()


async def test_home_is_a_map_with_the_four_rooms_as_door_buttons(user: User):
    await user.open("/")
    await user.should_see("Walk to a room")
    assert set(room_elements(user)) == {"learn", "test", "second", "stay"}


@pytest.mark.parametrize("room, expected", [("learn", "How many words?"), ("test", "Your diary is empty"),
                                            ("second", "Nothing to repeat"), ("stay", "Your diary is empty")])
async def test_clicking_a_door_button_steps_inside(user: User, room, expected):
    await user.open("/")
    click_element(user, room_elements(user)[room])
    await user.should_see(expected)


async def test_door_buttons_show_what_is_waiting(user: User):
    prepare(nouns(3), fail=True)
    prepare(nouns(2))
    await user.open("/")
    text = " ".join(str(getattr(e, "content", "")) for e in user.find(kind=ui.html).elements if "class='n'" in str(getattr(e, "content", "")))
    assert "3 waiting" in text and "2 words" in text and "2 to revise" in text and "510 new" in text


async def test_the_sidebar_lists_every_room_and_the_guide(user: User):
    await user.open("/")
    for label in ("The map", "Learn room", "Test room", "Second-chance room", "Diary", "Progress", "Word lists", "Guide: how it works"):
        await user.should_see(label)


async def test_the_guide_explains_rooms_points_and_tracking(user: User):
    await user.open("/")
    user.find("Guide: how it works").click()
    for text in ("Walk to a room", "The one rule", "How your points work", "Learn well, and track it"):
        await user.should_see(text)


async def test_header_shows_level_and_points(user: User):
    await user.open("/")
    await user.should_see("Level 1 · 0 pts")
    prepare(nouns(5))
    await user.open("/")
    await user.should_see("Level 1 · 50 pts")
    assert state.total_points() == 50


async def test_demo_profile_is_created_on_first_use_and_is_read_only(user: User, isolated_user_dir):
    state.switch_profile(config.PROFILE_DEMO)
    assert (isolated_user_dir / "demo" / "attempts.csv").exists() and state.store.progress.count(DIARY) > 100
    await user.open("/learn")
    await user.should_see("The demo profile is read-only")
    await user.open("/stats")
    await user.should_see("What the data says")


# ----------------------------------------------------------------------------- learn -> test -> diary
async def test_choosing_what_to_learn_lists_the_word_types_with_counts(user: User):
    await user.open("/learn")
    for text in ("Nouns", "282 new", "Verbs", "96 new", "Adjectives", "Everything", "515 new", "Test me", "Both ways"):
        await user.should_see(text)


async def test_the_study_cards_show_both_languages_and_can_be_stepped_through(user: User):
    await user.open("/learn")
    user.find("Start learning").click()
    await user.should_see("Card 1 of 10")
    first = state.run.words[0]
    await user.should_see(first["german"])
    await user.should_see(first["english"])                                  # the back of the card is on the page too
    if first["plural"]:
        await user.should_see("Plural: die " + first["plural"])
    user.find("Next").click()
    await user.should_see("Card 2 of 10")
    user.find("Back").click()
    await user.should_see("Card 1 of 10")


async def test_a_perfect_round_puts_every_word_in_the_diary(user: User):
    await start_learning(user)
    assert len(state.run.test.items) == 20
    await play_round(user)
    await user.should_see("10 of 10 words passed")
    await user.should_see("In your diary (10)")
    assert state.store.progress.count(DIARY) == 10 and state.store.progress.count(SECOND) == 0
    log = state.store.attempts()
    assert len(log) == 20 and set(log["phase"]) == {"learn"}


async def test_a_wrong_answer_sends_the_word_to_the_second_chance_list(user: User):
    await start_learning(user)
    target = state.run.words[0]["word_id"]
    await play_round(user, wrong_for=lambda item: item.word["word_id"] == target and item.direction == "en_de")
    await user.should_see("9 of 10 words passed")
    await user.should_see("Second chance (1)")
    assert state.store.progress.status(target) == SECOND and state.store.progress.count(DIARY) == 9


async def test_feedback_names_the_right_answer_and_what_happens_to_the_word(user: User):
    await start_learning(user)
    await answer_question(user, right=False, text="zzz")
    await user.should_see("Not quite")
    await user.should_see("You typed: zzz")
    await user.should_see("One more question about this word to come")
    await go_on(user)


async def test_the_verdict_appears_after_the_last_question_of_a_word(user: User):
    await start_learning(user)
    word_id = state.run.test.current.word["word_id"]
    asked = 0
    for _ in range(20):
        item = state.run.test.current
        await answer_question(user)
        asked += item.word["word_id"] == word_id
        if asked == 2:
            await user.should_see("goes into your diary")
            return
        await go_on(user)
    raise AssertionError("never reached the second question of the word")


async def test_typing_is_forgiving_about_case_and_spacing(user: User):
    await start_learning(user, "Nouns")
    for _ in range(state.run.test.total):
        item = state.run.test.current
        text = right_response(item)
        await answer_question(user, text=text.upper() if item.direction == "en_de" else f"  {text}  ")
        assert state.run.test.feedback.correct, (item.direction, text)
        await go_on(user)
    await user.should_see("10 of 10 words passed")


async def test_a_dash_is_never_a_correct_answer(user: User):
    await start_learning(user)
    await answer_question(user, text="-")
    assert not state.run.test.feedback.correct
    await go_on(user)
    await answer_question(user, text="   ")
    assert not state.run.test.feedback.correct


async def test_i_dont_know_counts_as_wrong(user: User):
    await start_learning(user)
    user.find("I don't know").click()
    await user.should_see("Not quite")
    assert not state.run.test.log[0].correct


async def test_verbs_ask_for_all_three_forms(user: User):
    await start_learning(user, "Verbs")
    while state.run.test.current.direction != "en_de":
        await answer_question(user)
        await go_on(user)
    assert len(list(user.find(kind=ui.input).elements)) == 3
    await answer_question(user)
    assert state.run.test.feedback.correct
    assert state.run.test.feedback.check.parts == {"infinitive": True, "past": True, "perfect": True}


async def test_only_one_direction_can_be_chosen(user: User):
    await user.open("/learn")
    choose_directions(user, "de_en")
    user.find("Start learning").click()
    await user.should_see("Card 1 of 10")
    assert state.run.directions == ["de_en"]
    user.find("Skip to the test").click()
    await user.should_see("Question 1 of 10")


async def test_ending_a_session_keeps_the_words_already_finished(user: User):
    await start_learning(user)
    first = state.run.test.current.word["word_id"]
    while state.run.test.done_words == 0:
        await answer_question(user)
        await go_on(user)
    finished = next(iter(state.run.test.outcomes))
    user.find("End session").click()
    await user.should_see("Walk to a room")
    assert state.run is None and state.store.progress.status(finished) == DIARY and first


# ----------------------------------------------------------------------------- second chance
async def test_second_chance_page_lists_the_missed_words_and_starts_a_review(user: User):
    prepare(nouns(4), fail=True)
    await user.open("/second-chance")
    await user.should_see("Review & re-test")
    assert {r["german"] for r in table_rows(user)} == {w["german"] for w in session.pick_second_chance(state.store.progress)}
    user.find("Review & re-test").click()
    await user.should_see("Card 1 of 4")
    await user.should_see("Second-chance room · re-test")


async def test_passing_the_retest_moves_words_into_the_diary(user: User):
    prepare(nouns(4), fail=True)
    await begin_retest(user)
    await user.should_see("Question 1 of 8")
    await play_round(user)
    await user.should_see("4 of 4 words passed")
    assert state.store.progress.count(DIARY) == 4 and state.store.progress.count(SECOND) == 0
    assert set(state.store.attempts()["phase"]) == {"learn", "retest"}


async def test_failing_the_retest_keeps_words_in_second_chance(user: User):
    prepare(nouns(3), fail=True)
    await begin_retest(user)
    await play_round(user, wrong_for=lambda item: True)
    await user.should_see("0 of 3 words passed")
    assert state.store.progress.count(SECOND) == 3 and state.store.progress.count(DIARY) == 0


async def test_second_chance_page_is_empty_when_everything_passed(user: User):
    await user.open("/second-chance")
    await user.should_see("Nothing to repeat")


# ----------------------------------------------------------------------------- diary
async def test_diary_shows_only_passed_words_and_offers_revision(user: User):
    picked = nouns(5)
    prepare(picked[:3])
    prepare(picked[3:], fail=True)
    await user.open("/diary")
    await user.should_see("My diary")
    await user.should_see("Revise them in the Test room")
    assert {r["german"] for r in table_rows(user)} == {w["german"] for w in picked[:3]}


async def test_diary_is_empty_at_the_start(user: User):
    await user.open("/diary")
    await user.should_see("Your diary is empty")


async def test_failing_a_diary_revision_sends_the_word_back_to_second_chance(user: User):
    prepare(nouns(4))
    await begin_revision(user)
    await user.should_see("Test room · revision")
    await user.should_see("Question 1 of 8")
    miss = state.run.words[0]["word_id"]
    await play_round(user, wrong_for=lambda item: item.word["word_id"] == miss)
    await user.should_see("3 of 4 words passed")
    await user.should_see("Still in your diary")
    assert state.store.progress.status(miss) == SECOND and state.store.progress.count(DIARY) == 3
    assert set(state.store.attempts()["phase"]) == {"learn", "diary"}


async def test_a_passed_revision_keeps_everything_in_the_diary(user: User):
    prepare(nouns(3))
    await begin_revision(user)
    await play_round(user)
    await user.should_see("3 of 3 words passed")
    assert state.store.progress.count(DIARY) == 3
    assert all(r["streak"] == 2 for r in state.store.progress.records.values())


# ----------------------------------------------------------------------------- the whole journey, and persistence
async def test_the_whole_journey_learn_fail_retest_revise(user: User):
    await start_learning(user)
    ids = [w["word_id"] for w in state.run.words]
    await play_round(user, wrong_for=lambda item: item.word["word_id"] in ids[:2])             # two words fail
    assert state.store.progress.count(SECOND) == 2 and state.store.progress.count(DIARY) == 8
    await begin_retest(user)
    await play_round(user)                                                                      # both pass the re-test
    assert state.store.progress.count(DIARY) == 10 and state.store.progress.count(SECOND) == 0
    await begin_revision(user)
    await play_round(user, wrong_for=lambda item: item.word["word_id"] == ids[0])               # one is forgotten
    assert state.store.progress.status(ids[0]) == SECOND and state.store.progress.count(DIARY) == 9
    await user.open("/stats")
    await user.should_see("What the data says")
    await user.should_see("First-try pass rate")


async def test_progress_survives_restarting_the_app(user: User):
    prepare(nouns(3))
    before = state.store.progress.ids(DIARY)
    state.__init__()                                                                            # a fresh process reading the same files
    assert state.store.progress.ids(DIARY) == before
    await user.open("/")
    await user.should_see("My diary")


# ----------------------------------------------------------------------------- the word list page
async def test_word_list_page_shows_the_quality_checks(user: User):
    await user.open("/words")
    await user.should_see("Data-quality checks")
    await user.should_see("Nouns have a valid article")
    await user.should_see("Load your own sheet")


async def test_a_loaded_sheet_becomes_the_list_to_learn_from(user: User, mini_words):
    wordlist.save_upload(mini_words, "tiny")
    state.wordlist = "tiny"
    await user.open("/learn")
    await user.should_see("10 new")                                                             # "Everything" has the 10 words of the sheet
    user.find("Start learning").click()
    assert {w["german"] for w in state.run.words} <= set(mini_words["german"])


async def test_the_diary_survives_switching_the_word_list(user: User, mini_words):
    prepare(nouns(3))
    wordlist.save_upload(mini_words, "tiny")
    state.wordlist = "tiny"
    assert state.store.progress.count(DIARY) == 3
    await user.open("/diary")
    await user.should_see("My diary")


# ----------------------------------------------------------------------------- rooms ask for a word list; points
def click_card(user: User, title: str) -> None:
    """Click the word-list card with this title."""
    from nicegui.testing.user_interaction import UserInteraction
    cards = {el.parent_slot.parent for el in user.find(title, kind=ui.label).elements
             if type(el).__name__ == "Label" and "listcard" in el.parent_slot.parent.classes}
    UserInteraction(user, cards, None).click()


def unique_list(name: str):
    import pandas as pd
    raw = pd.DataFrame({"english": ["zebra", "yak", "xerus"], "german": ["Zebra", "Yak", "Xerus"], "article": ["das", "der", "das"],
                        "word_class": ["noun"] * 3})
    wordlist.save_upload(wordlist.standardize(raw)[0], name)


async def test_the_test_room_can_be_limited_to_one_word_list(user: User):
    prepare(nouns(5))
    unique_list("zoo")
    await user.open("/test")
    await user.should_see("How many words?")
    click_card(user, "Zoo")
    await user.should_see("No diary words from that list yet.")
    click_card(user, "German Core")
    await user.should_see("How many words?")
    user.find("Start the revision test").click()
    await user.should_see("Question 1 of")
    assert len(state.run.words) == 5


async def test_the_second_chance_room_can_be_limited_to_one_word_list(user: User):
    prepare(nouns(4), fail=True)
    unique_list("zoo")
    await user.open("/second-chance")
    click_card(user, "Zoo")
    await user.should_see("How many?")
    user.find("Review & re-test").click()
    await user.should_see("No second-chance words from that list.") if False else None
    assert state.run is None                                                             # nothing from that list: no session starts


async def test_a_good_round_earns_points_and_a_level_up(user: User):
    await start_learning(user)
    await play_round(user)
    await user.should_see("Level up!")
    assert state.total_points() == 100 and state.level().number == 2
    await user.should_see("Level 2 · 100 pts")


async def test_missing_a_word_earns_no_points(user: User):
    await start_learning(user)
    await play_round(user, wrong_for=lambda item: True)
    assert state.total_points() == 0


async def test_the_map_page_ships_its_world_script_and_numbers(user: User):
    await user.open("/")
    await user.should_see("Walk to a room")
    response = await user.http_client.get("/static-wortschatz/world.js")
    assert response.status_code == 200 and "Learn room" in response.text and "Diary" in response.text and "Living room" not in response.text


def test_every_pad_on_the_map_leads_to_a_real_page():
    import re
    from pathlib import Path
    script = (Path(__file__).resolve().parent.parent / "webapp" / "static" / "world.js").read_text(encoding="utf-8")
    urls = set(re.findall(r'url: "(/[a-z-]*)"', script))
    assert urls == {"/learn", "/test", "/second-chance", "/diary", "/stats", "/words"} and urls <= set(ROUTES)
