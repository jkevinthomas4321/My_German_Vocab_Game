"""The home page: a top-down map of the campus. Walk to a room (WASD or arrows, or click) and step on its pad to enter."""
import json
from pathlib import Path

from nicegui import ui

from wortschatz import stats

from .. import components as C
from ..layout import frame
from ..state import state

SCRIPT = Path(__file__).resolve().parent.parent / "static" / "world.js"

# (key, room colour, title, url): the four main rooms, also offered as plain buttons under the map
DOORS = [("learn", "#5B8DBF", "Learn room", "/learn"),
         ("test", "#44A08A", "Test room", "/test"),
         ("second", "#CC7456", "Second-chance room", "/second-chance"),
         ("stay", "#D1A24C", "Diary", "/diary")]

MAP_HTML = """<div class="world-wrap">
  <canvas id="world" aria-label="Top-down map of the campus"></canvas>
  <div class="world-chip" id="world-room"><i></i><b>Corridor</b><span>you are here</span></div>
  <div class="world-keys"><b>W</b><b>A</b><b>S</b><b>D</b> move <b>E</b> enter</div>
  <div class="world-prompt" id="world-prompt"><kbd>E</kbd><span></span></div>
</div>"""


def door_chip(key: str, color: str, title: str, caption: str, target: str, glow: bool = False) -> None:
    """A button version of a room: a shortcut, and a way in without the keyboard or a mouse-driven walk."""
    box = ui.element("div").classes(f"doorchip room-{key}" + (" glow" if glow else "")).style(f"--room:{color}").props(
        f'tabindex=0 role=button aria-label="Go to the {title}"')
    box.on("click", lambda: ui.navigate.to(target))
    box.on("keydown.enter", lambda: ui.navigate.to(target))
    with box:
        ui.element("i")
        ui.html(f"<b>{C.esc(title)}</b> <span class='n'>{C.esc(caption)}</span>", sanitize=False)


def home() -> None:
    with frame("home") as shell:
        counts = state.counts()
        kpi = stats.kpis(state.store.progress, state.store.attempts())
        level = state.level()
        captions = {"learn": f"{counts['new']} new", "test": f"{counts['diary']} to revise",
                    "second": f"{counts['second']} waiting", "stay": f"{counts['diary']} words"}

        world = {"badges": {**captions, "diary": captions["stay"], "progress": f"Level {level.number}", "library": f"{len(state.catalog())} list" + ("" if len(state.catalog()) == 1 else "s")},
                 "urgent": ["second"] if counts["second"] else []}
        ui.add_head_html(f"<script>window.WORTSCHATZ_WORLD = {json.dumps(world)};</script>")
        ui.add_head_html(f'<script src="/static-wortschatz/world.js?v={int(SCRIPT.stat().st_mtime)}" defer></script>')

        with ui.column().classes("gap-0"):
            ui.label("Walk to a room").classes("text-3xl font-bold serif")
            ui.label("Move with WASD or the arrow keys, or click where you want to go. Step on a glowing pad to enter. "
                     "In every room you choose a word list first.").classes("muted")

        ui.html(MAP_HTML, sanitize=False).classes("w-full")
        ui.button(on_click=shell.guide.open).props("id=open-guide").style("display:none")

        with ui.row().classes("doors items-center"):
            ui.label("Or go straight to:").classes("muted text-sm")
            for key, color, title, target in DOORS:
                door_chip(key, color, title, captions[key], target, glow=key == "second" and counts["second"] > 0)

        C.tiles([("Level", f"{level.number}", f"{level.title} · {level.points} points"), ("Points today", f"+{state.points_today()}", "from words you proved"),
                 ("Streak", f"{kpi['streak']} d", f"best {kpi['best_streak']} d"), ("Words tested today", str(kpi["today_words"]), "")])
