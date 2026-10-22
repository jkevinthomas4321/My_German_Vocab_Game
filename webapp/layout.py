"""The frame shared by every page: a slim dark header (home, guide, level, profile) and the page content below it."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Callable

from nicegui import ui

from wortschatz import config

from . import theme
from .state import state


@dataclass
class Shell:
    """What a page gets from `with frame(...) as shell`."""
    refresh: Callable[[], None]         # re-read the points and level in the header


def _switch_profile(event) -> None:
    state.switch_profile(event.value)
    ui.navigate.to("/")


@contextmanager
def frame(active: str):
    """Use as `with frame("home"):` and put the page content inside."""
    theme.colors()
    ui.dark_mode(True)

    @ui.refreshable
    def level_chip() -> None:
        level = state.level()
        ui.label(f"Level {level.number} · {level.points} pts").classes("chip-level")

    with ui.header().classes("app-header items-center justify-between no-wrap"):
        with ui.row().classes("items-center gap-3 no-wrap"):
            ui.label("Wortschatz").classes("brand cursor-pointer").on("click", lambda: ui.navigate.to("/"))
            if active != "home":
                ui.link("← Home", "/").classes("navlink")
        with ui.row().classes("items-center gap-3 no-wrap"):
            ui.link("Guide", "/#guide").classes("navlink")
            level_chip()
            ui.toggle({config.PROFILE_ME: "My diary", config.PROFILE_DEMO: "Demo"}, value=state.profile,
                      on_change=_switch_profile).props("dense no-caps unelevated toggle-color=primary toggle-text-color=white").classes("segmented")

    with ui.column().classes("page"):
        if state.is_demo:
            with ui.row().classes("card-flat demo-banner items-center gap-3 w-full"):
                ui.icon("science", color="amber-5")
                ui.label("Synthetic demo data from a simulated learner. Switch to “My diary” (top right) to play and keep your own progress.").classes("text-sm")
        yield Shell(level_chip.refresh)
