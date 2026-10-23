"""The opening page: four big mode buttons. Click one and the character runs to it, jumps on it, and the mode starts."""
from pathlib import Path

from nicegui import ui

from wortschatz import stats

from .. import components as C
from ..reset import open_reset_dialog
from ..icons import ICONS
from ..layout import frame
from ..state import state

SCRIPT = Path(__file__).resolve().parent.parent / "static" / "hero.js"

# (key, colour variable, title, url)
MODES = [("learn", "--learn", "Learn", "/learn"),
         ("test", "--test", "Test", "/test"),
         ("second", "--second", "Second chance", "/second-chance"),
         ("stay", "--stay", "Diary", "/diary")]


def mode_button(key: str, color: str, title: str, caption: str, badge: str, target: str, number: int, glow: bool) -> None:
    """One big button. The script in static/hero.js animates the click; the Python handler is the fallback without it."""
    box = ui.element("div").classes(f"modebtn room-{key}" + (" glow" if glow else "")).style(f"--room:var({color})").props(
        f'tabindex=0 role=button data-url="{target}" data-key="{key}" aria-label="{title}: {caption}"')
    box.on("click", lambda: ui.navigate.to(target))
    box.on("keydown.enter", lambda: ui.navigate.to(target))
    with box:
        ui.html(f'<span class="key">{number}</span><span class="badge">{C.esc(badge)}</span>'
                f'<div class="pad">{ICONS[key]}</div><div class="t">{C.esc(title)}</div><div class="s">{C.esc(caption)}</div>', sanitize=False)


def home() -> None:
    with frame("home") as shell:
        counts = state.counts()
        kpi = stats.kpis(state.store.progress, state.store.attempts())
        level = state.level()
        copy = {"learn": ("Study new words", f"{counts['new']} new"), "test": ("Revise your diary", f"{counts['diary']} to revise"),
                "second": ("Try missed words again", f"{counts['second']} waiting"), "stay": ("Your proven words", f"{counts['diary']} words")}

        ui.add_head_html(f'<script src="/static-wortschatz/hero.js?v={int(SCRIPT.stat().st_mtime)}" defer></script>')
        with ui.column().classes("opening items-center w-full gap-0"):
            ui.html("<h1>Learn German. <b>Prove it.</b></h1>", sanitize=False)
            ui.label("Choose a mode. A word only enters your diary after you have passed the test.")

        with ui.element("div").classes("stage").props("id=hero-stage"):
            with ui.element("div").classes("modes"):
                for number, (key, color, title, target) in enumerate(MODES, start=1):
                    caption, badge = copy[key]
                    mode_button(key, color, title, caption, badge, target, number, glow=key == "second" and counts["second"] > 0)
            ui.html('<div class="startmat"><i></i><span>START</span></div>', sanitize=False)
            ui.html("<canvas></canvas>", sanitize=False)

        with ui.element("div").classes("quicklinks w-full"):
            ui.label(f"Level {level.number} · {level.title}").classes("chip")
            ui.label(f"+{state.points_today()} points today").classes("chip")
            ui.label(f"{kpi['streak']} day streak").classes("chip")
        with ui.element("div").classes("quicklinks w-full"):
            ui.button("Guide: how it works", icon="menu_book", on_click=shell.guide.open).props("unelevated no-caps color=primary")
            ui.button("Progress", icon="insights", on_click=lambda: ui.navigate.to("/stats"), color=None).props("outline no-caps")
            ui.button("Word lists", icon="library_books", on_click=lambda: ui.navigate.to("/words"), color=None).props("outline no-caps")
            ui.button("Reset progress", icon="restart_alt", on_click=open_reset_dialog, color=None).props("flat no-caps").classes("muted")
