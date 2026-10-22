"""The frame shared by every page: a slim header with the burger button, and a collapsible sidebar."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Callable

from nicegui import app, ui

from wortschatz import config

from . import guide, theme
from .state import state

# (key, label, icon, url): the rooms of the house first, then the places to look things up
NAV = [("home", "The house", "home", "/"),
       ("learn", "Learn room", "school", "/learn"),
       ("test", "Test room", "quiz", "/test"),
       ("second", "Second-chance room", "replay", "/second-chance"),
       ("diary", "Living room · Diary", "weekend", "/diary"),
       ("stats", "Progress", "insights", "/stats"),
       ("words", "Word lists", "library_books", "/words")]


@dataclass
class Shell:
    """What a page gets from `with frame(...) as shell`."""
    guide: ui.dialog
    refresh: Callable[[], None]         # re-read the points and level in the header and the sidebar


def _switch_profile(event) -> None:
    state.switch_profile(event.value)
    ui.navigate.to("/")


@contextmanager
def frame(active: str):
    """Use as `with frame("home"):` and put the page content inside."""
    theme.colors()
    counts = state.counts()
    dark = ui.dark_mode().bind_value(app.storage.user, "dark")          # remembered between pages and visits
    guide_dialog = guide.build()

    # ------------------------------------------------------------------ sidebar (opens and closes with the burger)
    closed = app.storage.user.get("drawer_closed", False)
    drawer = ui.left_drawer(value=False if closed else None, bordered=True).props("width=282 show-if-above").classes("sidebar")

    def toggle_drawer() -> None:
        drawer.toggle()
        app.storage.user["drawer_closed"] = not drawer.value

    @ui.refreshable
    def level_card() -> None:
        level = state.level()
        ui.html(f'<div class="levelcard"><div class="lv">Level {level.number} · {level.title}</div>'
                f'<div class="bar"><span style="width:{level.progress * 100:.0f}%"></span></div>'
                f'<div class="pts">{level.points} points · {level.to_next} to level {level.number + 1}</div></div>', sanitize=False)

    @ui.refreshable
    def level_chip() -> None:
        level = state.level()
        ui.label(f"Level {level.number} · {level.points} pts").classes("chip-level")

    def refresh() -> None:
        level_card.refresh()
        level_chip.refresh()

    with drawer:
        with ui.column().classes("w-full gap-3 p-3").style("min-height:100%"):
            with ui.column().classes("gap-0"):
                ui.label("Wortschatz").classes("side-brand")
                ui.element("div").classes("rule")
                ui.label("Learn it. Prove it. Keep it.").classes("muted text-xs")
            level_card()
            with ui.column().classes("w-full gap-0"):
                for key, label, icon, url in NAV:
                    with ui.item(on_click=lambda u=url: ui.navigate.to(u)).props("clickable").classes("navitem" + (" active" if key == active else "")):
                        with ui.item_section().props("avatar"):
                            ui.icon(icon)
                        with ui.item_section():
                            ui.item_label(label)
                        badge = {"second": counts["second"], "diary": counts["diary"]}.get(key)
                        if badge:
                            with ui.item_section().props("side"):
                                ui.label(str(badge)).classes("navbadge")
            ui.element("div").style("flex:1")
            ui.button("Guide: how it works", icon="menu_book", on_click=guide_dialog.open, color=None).props(
                "no-caps outline").classes("guide-btn w-full")
            with ui.row().classes("w-full items-center justify-between no-wrap"):
                ui.toggle({config.PROFILE_ME: "My diary", config.PROFILE_DEMO: "Demo"}, value=state.profile,
                          on_change=_switch_profile).props("dense no-caps unelevated toggle-color=primary toggle-text-color=white").classes("segmented")
                ui.switch().props("dense color=amber-8 icon=dark_mode").bind_value(dark, "value").tooltip("Dark mode")

    # ------------------------------------------------------------------ header
    with ui.header().classes("app-header items-center justify-between no-wrap"):
        with ui.row().classes("items-center gap-2 no-wrap"):
            ui.button(icon="menu", on_click=toggle_drawer, color=None).props("flat round dense").classes("burger").tooltip("Menu")
            ui.link("Wortschatz", "/").classes("brand no-underline")
        with ui.row().classes("items-center gap-3 no-wrap"):
            level_chip()
            ui.button(icon="menu_book", on_click=guide_dialog.open, color=None).props("flat round dense").classes("burger").tooltip("Guide")

    with ui.column().classes("page"):
        if state.is_demo:
            with ui.row().classes("card-flat items-center gap-3 w-full").style("background:#F6EBCB;border-color:#E0C77F;color:#4A3A00"):
                ui.icon("science", color="amber-9")
                ui.label("Synthetic demo data from a simulated learner. Switch to “My diary” in the menu to play and keep your own progress.").classes("text-sm")
        yield Shell(guide_dialog, refresh)
