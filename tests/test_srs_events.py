import pandas as pd
import pytest

from tests.conftest import NOW
from wortschatz import config, events, srs


def log(*entries):
    """entries: (word_id, hours_ago, correct[, retry])"""
    rows = [{"ts": NOW - pd.Timedelta(hours=h), "session_id": "s", "word_id": w, "word_class": "noun", "english": w, "german": w.upper(),
             "qtype": "choose_en", "direction": "de→en", "correct": c, "response_ms": 1500, "given": "", "expected": "",
             "article_expected": "", "article_given": "", "retry": (e[0] if (e := rest) else 0)}
            for w, h, c, *rest in entries]
    return pd.DataFrame(rows, columns=events.EVENT_COLUMNS)


# ----------------------------------------------------------------------------- box transitions
@pytest.mark.parametrize("box, correct, expected", [(0, True, 1), (0, False, 1), (1, True, 2), (4, True, 5), (5, True, 5),
                                                    (3, False, 1), (2, False, 1), (5, False, 3)])
def test_next_box(box, correct, expected):
    assert srs.next_box(box, correct) == expected


def test_status_labels():
    assert [srs.status_of(b) for b in range(6)] == ["Unseen", "Learning", "Learning", "Reviewing", "Reviewing", "Mastered"]


# ----------------------------------------------------------------------------- replay
def test_replay_walks_a_word_up_and_down_the_boxes():
    ev = log(("a", 100, 1), ("a", 90, 1), ("a", 80, 1), ("a", 70, 0), ("a", 60, 1))
    s = srs.replay(ev).loc["a"]
    # 0 -> 1 -> 2 -> 3, wrong: 3 -> 1, right: 2
    assert (s["box"], s["attempts"], s["correct"], s["wrong"], s["lapses"]) == (2, 5, 4, 1, 1)
    assert s["last_seen"] == NOW - pd.Timedelta(hours=60)
    assert s["due"] == s["last_seen"] + pd.Timedelta(days=config.INTERVAL_DAYS[2])


def test_mastery_is_dated_when_box_five_is_first_reached():
    ev = log(*[("a", 200 - 10 * i, 1) for i in range(6)])
    s = srs.replay(ev).loc["a"]
    assert s["box"] == 5 and s["mastered_at"] == NOW - pd.Timedelta(hours=160)


def test_retries_do_not_change_scheduling():
    base = srs.replay(log(("a", 50, 0)))
    with_retry = srs.replay(log(("a", 50, 0), ("a", 49, 1, 1)))
    assert with_retry.loc["a", ["box", "attempts"]].tolist() == base.loc["a", ["box", "attempts"]].tolist() == [1, 1]


def test_replay_is_order_independent_of_file_order():
    ev = log(("a", 30, 1), ("a", 20, 0), ("b", 10, 1))
    shuffled = ev.sample(frac=1, random_state=3)
    pd.testing.assert_frame_equal(srs.replay(ev).sort_index(), srs.replay(shuffled).sort_index())


def test_empty_log_gives_typed_empty_states():
    s = srs.replay(events.empty_events())
    assert s.empty and list(s.columns) == srs.STATE_COLUMNS


def test_due_ids_most_overdue_first():
    s = srs.replay(log(("old", 100, 1), ("older", 200, 1), ("fresh", 1, 1)))
    assert srs.due_ids(s, NOW) == ["older", "old"]


def test_status_counts():
    s = srs.replay(log(("a", 5, 1), ("b", 5, 0), *[("c", 100 - i, 1) for i in range(5)]))
    assert srs.status_counts(s, ["a", "b", "c", "never"]) == {"Unseen": 1, "Learning": 2, "Reviewing": 0, "Mastered": 1}


# ----------------------------------------------------------------------------- event log
def test_append_and_load_round_trip(isolated_user_dir):
    ev = log(("a", 5, 1), ("b", 4, 0))
    events.append_events(ev.to_dict("records"), "me")
    events.append_events(log(("c", 3, 1)).to_dict("records"), "me")
    loaded = events.load_events("me")
    assert loaded["word_id"].tolist() == ["a", "b", "c"] and loaded["correct"].tolist() == [1, 0, 1]
    assert pd.api.types.is_datetime64_any_dtype(loaded["ts"]) and loaded["response_ms"].dtype == "int64"
    assert (isolated_user_dir / "me" / "events.csv").read_text(encoding="utf-8").count("session_id") == 1   # one header


def test_profiles_are_separate(isolated_user_dir):
    events.append_events(log(("a", 5, 1)).to_dict("records"), "me")
    assert events.load_events("demo").empty and len(events.load_events("me")) == 1


def test_damaged_rows_are_dropped_not_fatal(isolated_user_dir):
    events.append_events(log(("a", 5, 1)).to_dict("records"), "me")
    with open(config.events_path("me"), "a", encoding="utf-8") as fh:
        fh.write("not-a-date,s,w,noun,x,X,choose_en,de→en,maybe,12,,,,,0\n")
        fh.write("2026-10-18 10:00:00,s,w,noun,x,X,choose_en,de→en,1,-5,,,,,0\n")
    assert len(events.load_events("me")) == 1


def test_missing_retry_column_defaults_to_zero(isolated_user_dir):
    path = config.events_path("me")
    path.parent.mkdir(parents=True)
    path.write_text("ts,session_id,word_id,word_class,english,german,qtype,direction,correct,response_ms,given,expected,article_expected,article_given\n"
                    "2026-10-18 10:00:00,s,w,noun,x,X,choose_en,de→en,1,900,,,,\n", encoding="utf-8")
    assert events.load_events("me")["retry"].tolist() == [0]


def test_graded_excludes_retries():
    ev = log(("a", 5, 0), ("a", 4, 1, 1))
    assert len(events.graded(ev)) == 1
