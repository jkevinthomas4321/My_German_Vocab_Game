"""The frame shared by every page: a slim header (home, guide, level, theme, profile) and the page content below it."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Callable

from nicegui import app, ui

from wortschatz import config

from . import guide, theme
from .state import state


@dataclass
class Shell:
    """What a page gets from `with frame(...) as shell`."""
    guide: ui.dialog                    # the Guide pop-up; call .open() to show it
    refresh: Callable[[], None]         # re-read the points and level in the header


def _switch_profile(event) -> None:
    state.switch_profile(event.value)
    ui.navigate.to("/")


@contextmanager
def frame(active: str):
    """Use as `with frame("home"):` and put the page content inside."""
    theme.colors()
    app.storage.user.setdefault("dark", True)
    dark = ui.dark_mode().bind_value(app.storage.user, "dark")          # remembered between pages and visits
    guide_dialog = guide.build()

    @ui.refreshable
    def level_chip() -> None:
        level = state.level()
        ui.label(f"Level {level.number} · {level.points} pts").classes("chip-level")

    with ui.header().classes("app-header items-center justify-between no-wrap"):
        with ui.row().classes("items-center gap-3 no-wrap"):
            ui.label("Wortschatz").classes("brand cursor-pointer").on("click", lambda: ui.navigate.to("/"))
            if active != "home":
                ui.link("← Home", "/").classes("navlink")
        with ui.row().classes("items-center gap-2 no-wrap"):
            ui.button("Guide", icon="menu_book", on_click=guide_dialog.open, color=None).props("flat no-caps dense").classes("navlink")
            level_chip()
            ui.switch().props("dense color=blue-5 checked-icon=dark_mode unchecked-icon=light_mode").bind_value(dark, "value").tooltip("Dark / light")
            ui.toggle({config.PROFILE_ME: "My diary", config.PROFILE_DEMO: "Demo"}, value=state.profile,
                      on_change=_switch_profile).props("dense no-caps unelevated toggle-color=primary toggle-text-color=white").classes("segmented")

    with ui.column().classes("page"):
        if state.is_demo:
            with ui.row().classes("card-flat demo-banner items-center gap-3 w-full"):
                ui.icon("science", color="amber-5")
                ui.label("Synthetic demo data from a simulated learner. Switch to “My diary” (top right) to play and keep your own progress.").classes("text-sm")
        yield Shell(guide_dialog, level_chip.refresh)
