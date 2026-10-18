"""Structural checks on every chart. A layer without x/y encodings makes Vega-Lite draw nothing and
fail silently in the browser (this happened once with the regression line), so it is worth a test."""
import pytest

from tests.conftest import NOW
from ui import charts
from wortschatz import analytics as A
from wortschatz import simulate, srs


@pytest.fixture(scope="module")
def demo_frames():
    from wortschatz import config, wordlist
    words = wordlist.load_wordlist(config.WORDLIST_DIR / "german_core.csv")[0]
    ev = simulate.simulate_history(words, days=30, seed=2026, now=NOW)
    d = A.prepare(ev, words)
    states = srs.replay(ev)
    return words, d, states, A.word_table(d, states, words)


def builders(words, d, states, wt):
    sessions = A.session_table(d)
    return {
        "activity_bars": charts.activity_bars(A.daily_activity(d)),
        "calendar_heatmap": charts.calendar_heatmap(A.calendar_grid(d, 12, NOW.date())),
        "session_trend": charts.session_trend(sessions),
        "rolling_line": charts.rolling_line(A.rolling_accuracy(d, 50), 50),
        "rate_bars": charts.rate_bars(A.accuracy_by(d, "word_class"), "word_class"),
        "learning_curve": charts.learning_curve_chart(A.learning_curve(d)),
        "forgetting_curve": charts.forgetting_chart(A.forgetting_curve(d)),
        "confusion_heatmap": charts.confusion_heatmap(A.article_confusion(d)),
        "suffix_gender": charts.suffix_gender_chart(A.suffix_gender_table(words)),
        "funnel": charts.funnel_bars(A.mastery_funnel(states, list(words["word_id"]))),
        "forecast": charts.forecast_bars(A.due_forecast(states, NOW)),
        "growth": charts.growth_lines(A.vocabulary_growth(states)),
        "rt_histogram": charts.rt_histogram(A.response_times(d)),
        "rt_trend": charts.rt_trend_chart(A.rt_trend(d)),
        "hour": charts.hour_chart(A.hour_profile(d)),
        "scatter": charts.scatter_frequency(wt[wt["attempts"] >= 3]),
        "class_mix": charts.class_mix(words),
        "zipf_histogram": charts.zipf_histogram(words),
    }


def layers(spec: dict) -> list[dict]:
    """Leaf layers, flattening nested layer charts."""
    if "layer" not in spec:
        return [spec]
    return [leaf for child in spec["layer"] for leaf in layers(child)]


def encodes_position(spec: dict, layer: dict) -> bool:
    encoding = {**spec.get("encoding", {}), **layer.get("encoding", {})}
    mark = layer.get("mark", {})
    if (mark.get("type") if isinstance(mark, dict) else mark) == "rule":           # reference lines need only one axis
        return "x" in encoding or "y" in encoding
    return "x" in encoding and "y" in encoding


def test_every_chart_layer_has_positions_and_data(demo_frames):
    for name, chart in builders(*demo_frames).items():
        spec = chart.to_dict()
        assert spec.get("data") or spec.get("datasets"), f"{name}: no data"
        for i, layer in enumerate(layers(spec)):
            assert encodes_position(spec, layer), f"{name}: layer {i} has no x/y encoding"


def test_charts_do_not_mix_up_percent_axes(demo_frames):
    """Accuracy charts are plotted on a 0-100% axis."""
    spec = charts.rate_bars(A.accuracy_by(demo_frames[1], "word_class"), "word_class").to_dict()
    bars = layers(spec)[0]
    assert bars["encoding"]["x"]["scale"]["domain"] == [0, 1] and bars["encoding"]["x"]["axis"]["format"] == "%"
