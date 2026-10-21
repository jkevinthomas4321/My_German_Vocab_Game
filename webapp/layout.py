"""The frame shared by every page: header with navigation, profile switch and dark-mode toggle."""
from __future__ import annotations

from contextlib import contextmanager

from nicegui import app, ui

from wortschatz import config

from . import theme
from .state import state

NAV = [("home", "Home", "/"), ("learn", "Learn", "/learn"), ("second", "Second chance", "/second-chance"),
       ("diary", "Diary", "/diary"), ("stats", "Stats", "/stats"), ("words", "Word list", "/words")]


def _switch_profile(event) -> None:
    state.switch_profile(event.value)
    ui.navigate.to("/")


@contextmanager
def frame(active: str):
    """Use as `with frame("home"):` and put the page content inside."""
    theme.colors()
    counts = state.counts()
    dark = ui.dark_mode().bind_value(app.storage.user, "dark")          # remembered between pages and visits
    with ui.header().classes("app-header items-center justify-between gap-3 no-wrap"):
        with ui.column().classes("gap-0"):
            ui.link("Wortschatz", "/").classes("brand no-underline")
            ui.html('<div class="flag"><i style="background:#111"></i><i style="background:#D00"></i>'
                    '<i style="background:#FFCE00"></i></div>')
        with ui.row().classes("items-center gap-1 no-wrap overflow-x-auto"):
            for key, label, url in NAV:
                with ui.link(target=url).classes("nav-link" + (" active" if key == active else "")):
                    ui.label(label)
                    badge = {"second": counts["second"], "diary": counts["diary"]}.get(key)
                    if badge:
                        ui.label(str(badge)).classes("nav-count")
        with ui.row().classes("items-center gap-2 no-wrap"):
            ui.toggle({config.PROFILE_ME: "My diary", config.PROFILE_DEMO: "Demo"}, value=state.profile,
                      on_change=_switch_profile).props("dense unelevated no-caps color=white text-color=primary "
                                                       "toggle-color=amber-5 toggle-text-color=dark")
            ui.switch().props("dense color=amber-5 icon=dark_mode").bind_value(dark, "value")
    with ui.column().classes("page"):
        if state.is_demo:
            with ui.row().classes("card-flat items-center gap-3 w-full").style("background:#FFF4D6;border-color:#F0D58A;color:#4A3A00"):
                ui.icon("science", color="amber-9")
                ui.label("Synthetic demo data from a simulated learner. Switch to “My diary” to play and keep your own progress.").classes("text-sm")
        yield
