from datetime import date

import pandas as pd
import pytest

from wortschatz import config, points, session, stats
from wortschatz.progress import Progress
from wortschatz.storage import empty_attempts
from tests.conftest import NOW


def outcomes(rows):
    frame = pd.DataFrame(rows, columns=["phase", "passed", "ts"])
    frame["ts"] = pd.to_datetime(frame["ts"])
    frame["day"] = frame["ts"].dt.normalize()
    return frame


def test_points_per_pass():
    assert [points.word_points(p, True) for p in ("learn", "retest", "diary")] == [10, 6, 4]
    assert points.word_points("learn", False) == 0 and points.word_points("removed", True) == 0


def test_total_points_counts_only_passes():
    frame = outcomes([("learn", 1, NOW), ("learn", 0, NOW), ("retest", 1, NOW), ("diary", 1, NOW), ("diary", 0, NOW)])
    assert points.total_points(frame) == 10 + 6 + 4


def test_points_on_one_day():
    frame = outcomes([("learn", 1, NOW), ("learn", 1, NOW - pd.Timedelta(days=1))])
    assert points.points_on(frame, NOW.date()) == 10 and points.points_on(frame, date(2020, 1, 1)) == 0


def test_no_outcomes_means_no_points():
    empty = stats.word_outcomes(empty_attempts())
    assert points.total_points(empty) == 0 and points.points_on(empty, NOW.date()) == 0


@pytest.mark.parametrize("pts, level", [(0, 1), (59, 1), (60, 2), (239, 2), (240, 3), (540, 4), (4860, 10), (10**6, 1 + int((10**6 / 60) ** 0.5))])
def test_levels(pts, level):
    assert points.level_for(pts).number == level


def test_level_progress_and_titles():
    lv = points.level_for(150)
    assert (lv.floor, lv.ceiling, lv.to_next) == (60, 240, 90) and lv.progress == pytest.approx(90 / 180)
    assert points.level_for(0).title == "Anfänger" and points.level_for(10**7).title == "Wortzauberer"
    assert [l.floor for l in points.level_table(4)] == [0, 60, 240, 540]


def test_round_points():
    assert points.round_points("learn", 7) == 70 and points.round_points("diary", 3) == 12


def test_points_match_the_demo_history(core_words):
    from wortschatz import demo
    store = demo.generate(core_words, days=10, seed=3, now=NOW)
    out = stats.word_outcomes(store.attempts())
    expected = sum(points.word_points(r.phase, bool(r.passed)) for r in out.itertuples())
    assert points.total_points(out) == expected > 0


def test_second_chance_and_diary_can_be_limited_to_one_word_list(mini_words):
    from tests.test_progress_session import word
    p = Progress()
    for german, passed in [("Tisch", False), ("Stadt", False), ("Kind", True), ("Tür", True)]:
        p.apply(word(mini_words, german), passed, NOW)
    only = [word(mini_words, "Tisch")["word_id"], word(mini_words, "Kind")["word_id"]]
    assert [w["german"] for w in session.pick_second_chance(p, word_ids=only)] == ["Tisch"]
    assert [w["german"] for w in session.pick_diary(p, "all", 10, word_ids=only)] == ["Kind"]
    assert len(session.pick_diary(p, "all", 10)) == 2 and len(session.pick_second_chance(p)) == 2
