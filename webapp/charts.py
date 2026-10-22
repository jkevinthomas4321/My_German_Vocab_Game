"""ECharts option builders for the Stats page. Colours: blue = passed, orange = failed (colour-blind safe)."""
from __future__ import annotations

import pandas as pd

BLUE, ORANGE, GREEN, GOLD, MUTED = "#4F8CFF", "#FF8A5B", "#2DD4A8", "#F5B94C", "#8C9BB5"   # the app palette, bright enough for the dark background
_AXIS = {"axisLabel": {"color": MUTED}, "axisLine": {"lineStyle": {"color": "#2A3A5A"}},
         "splitLine": {"lineStyle": {"color": "rgba(140,160,200,.14)"}}}
_BASE = {"animationDuration": 500, "backgroundColor": "transparent", "textStyle": {"color": MUTED},
         "grid": {"left": 46, "right": 18, "top": 30, "bottom": 34, "containLabel": False}}

# draws the vertical 95% interval whisker of the "custom" series (columns: category, low, high)
_WHISKER = """function (params, api) {
  var x = api.value(0), hi = api.coord([x, api.value(2)]), lo = api.coord([x, api.value(1)]);
  var w = api.size([1, 0])[0] * 0.12, s = {stroke: '#C9D6EE', lineWidth: 1.6};
  return {type: 'group', children: [
    {type: 'line', shape: {x1: hi[0], y1: hi[1], x2: lo[0], y2: lo[1]}, style: s},
    {type: 'line', shape: {x1: hi[0] - w, y1: hi[1], x2: hi[0] + w, y2: hi[1]}, style: s},
    {type: 'line', shape: {x1: lo[0] - w, y1: lo[1], x2: lo[0] + w, y2: lo[1]}, style: s}]};
}"""


def _category_axis(labels, boundary_gap: bool = True) -> dict:
    """A category axis that shows every label (wrapping long ones) instead of hiding overlapping ones."""
    axis = {"type": "category", "data": list(labels), **_AXIS,
            "axisLabel": {"color": MUTED, "interval": 0, "overflow": "break", "width": 110}}
    if not boundary_gap:
        axis["boundaryGap"] = False
    return axis


def _opts(**extra) -> dict:
    return {**_BASE, **extra}


def diary_growth(frame: pd.DataFrame) -> dict:
    return _opts(
        tooltip={"trigger": "axis"},
        xAxis={"type": "category", "data": [d.strftime("%d %b") for d in frame["day"]], **_AXIS},
        yAxis={"type": "value", "minInterval": 1, **_AXIS},
        series=[{"name": "Words in the diary", "type": "line", "data": [int(v) for v in frame["diary"]], "smooth": 0.25, "showSymbol": False,
                 "lineStyle": {"width": 3, "color": GREEN}, "itemStyle": {"color": GREEN},
                 "areaStyle": {"color": {"type": "linear", "x": 0, "y": 0, "x2": 0, "y2": 1,
                                         "colorStops": [{"offset": 0, "color": "rgba(45,212,168,.35)"}, {"offset": 1, "color": "rgba(45,212,168,0)"}]}}}])


def daily_tests(frame: pd.DataFrame) -> dict:
    days = pd.date_range(frame["day"].min(), frame["day"].max(), freq="D")
    full = frame.set_index("day").reindex(days, fill_value=0)
    return _opts(
        tooltip={"trigger": "axis", "axisPointer": {"type": "shadow"}}, legend={"top": 0, "textStyle": {"color": MUTED}},
        grid={**_BASE["grid"], "top": 34},
        xAxis={"type": "category", "data": [d.strftime("%d %b") for d in days], **_AXIS},
        yAxis={"type": "value", "minInterval": 1, **_AXIS},
        series=[{"name": "Passed", "type": "bar", "stack": "t", "data": [int(v) for v in full["passed"]], "itemStyle": {"color": BLUE}},
                {"name": "Failed", "type": "bar", "stack": "t", "data": [int(v) for v in full["failed"]],
                 "itemStyle": {"color": ORANGE, "borderRadius": [4, 4, 0, 0]}}])


def calendar(frame: pd.DataFrame, end: pd.Timestamp, weeks: int = 20) -> dict:
    start = (end - pd.Timedelta(weeks=weeks)).normalize()
    top = max(int(frame["tests"].max()) if len(frame) else 1, 1)
    data = [[d.strftime("%Y-%m-%d"), int(n)] for d, n in zip(frame["day"], frame["tests"])]
    return _opts(
        tooltip={":formatter": "function(p){return p.value[0] + ': ' + p.value[1] + ' words tested';}"},
        visualMap={"min": 0, "max": top, "show": False, "inRange": {"color": ["#111C33", "#1E3F85", BLUE, "#CFE0FF"]}},
        calendar={"range": [start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")], "cellSize": ["auto", 18], "left": 40, "right": 10, "top": 28,
                  "itemStyle": {"borderWidth": 3, "borderColor": "transparent", "color": "#111C33"}, "splitLine": {"show": False},
                  "yearLabel": {"show": False}, "monthLabel": {"color": MUTED}, "dayLabel": {"color": MUTED, "firstDay": 1}},
        series=[{"type": "heatmap", "coordinateSystem": "calendar", "data": data, "itemStyle": {"borderRadius": 4}}])


def rate_with_whiskers(labels: list[str], rate, lo, hi, n, color: str = BLUE) -> dict:
    """Vertical bars of a rate with 95% interval whiskers; the tooltip shows the sample size."""
    rate, lo, hi = [float(v) for v in rate], [float(v) for v in lo], [float(v) for v in hi]
    return _opts(
        tooltip={"trigger": "axis", "axisPointer": {"type": "shadow"}},
        xAxis=_category_axis([f"{label}\nn={int(k)}" for label, k in zip(labels, n)]),
        yAxis={"type": "value", "min": 0, "max": 1, "axisLabel": {"color": MUTED, ":formatter": "function(v){return Math.round(v*100)+'%'}"},
               "splitLine": _AXIS["splitLine"]},
        series=[{"name": "Rate", "type": "bar", "data": rate, "barMaxWidth": 46, "itemStyle": {"color": color, "borderRadius": [6, 6, 0, 0]},
                 "label": {"show": True, "position": "inside", "color": "#fff", "fontWeight": "bold",
                           ":formatter": "function(p){return Math.round(p.value*100)+'%'}"}},
                {"name": "95% interval", "type": "custom", ":renderItem": _WHISKER, "z": 10, "tooltip": {"show": False},
                 "data": [[i, a, b] for i, (a, b) in enumerate(zip(lo, hi))]}])


def line_with_band(labels: list[str], rate, lo, hi, n) -> dict:
    """A line with a shaded 95% confidence band (drawn as two stacked areas)."""
    rate, lo, hi = [round(float(v), 4) for v in rate], [round(float(v), 4) for v in lo], [round(float(v), 4) for v in hi]
    return _opts(
        tooltip={"trigger": "axis"},
        xAxis=_category_axis([f"{label}\nn={int(k)}" for label, k in zip(labels, n)], boundary_gap=False),
        yAxis={"type": "value", "min": 0, "max": 1, "axisLabel": {"color": MUTED, ":formatter": "function(v){return Math.round(v*100)+'%'}"},
               "splitLine": _AXIS["splitLine"]},
        series=[{"type": "line", "data": lo, "stack": "band", "symbol": "none", "lineStyle": {"opacity": 0}, "tooltip": {"show": False}},
                {"type": "line", "data": [round(b - a, 4) for a, b in zip(lo, hi)], "stack": "band", "symbol": "none", "lineStyle": {"opacity": 0},
                 "areaStyle": {"color": "rgba(79,140,255,.16)"}, "tooltip": {"show": False}},
                {"name": "Pass rate", "type": "line", "data": rate, "symbolSize": 9, "lineStyle": {"width": 3, "color": BLUE},
                 "itemStyle": {"color": BLUE},
                 "label": {"show": True, "position": "top", "color": MUTED, ":formatter": "function(p){return Math.round(p.value*100)+'%'}"}}])


def counts_bars(labels: list[str], values: list[int], color: str = GOLD) -> dict:
    return _opts(
        tooltip={"trigger": "axis", "axisPointer": {"type": "shadow"}},
        xAxis=_category_axis(labels), yAxis={"type": "value", "minInterval": 1, **_AXIS},
        series=[{"type": "bar", "data": [int(v) for v in values], "barMaxWidth": 48, "itemStyle": {"color": color, "borderRadius": [6, 6, 0, 0]},
                 "label": {"show": True, "position": "top", "color": MUTED}}])
