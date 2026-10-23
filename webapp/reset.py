"""The "Reset progress" dialog: wipes the diary, the second-chance list, the answer history and the points of the current profile."""
from __future__ import annotations

from datetime import datetime

from nicegui import ui

from .state import state


def open_reset_dialog() -> None:
    if state.is_demo:
        ui.notify("The demo profile is read-only. Switch to “My diary” to reset your own progress.", type="info")
        return
    progress = state.store.progress
    words = len(progress.records)

    def confirm() -> None:
        state.end_run()
        state.store.reset()
        dialog.close()
        ui.notify("Progress reset. You are starting fresh.", type="positive")
        ui.navigate.to("/")

    with ui.dialog() as dialog, ui.card().classes("gap-3").style("width:min(520px,94vw);border-radius:20px"):
        ui.label("Reset your progress?").classes("text-xl font-bold")
        ui.label(f"This deletes your diary and second-chance list ({words} word{'s' if words != 1 else ''}), your answer history, "
                 "your points and your statistics. Your word lists are not touched, and neither is anything on GitHub: "
                 "your progress only ever lives in the user_data folder on this computer.").classes("muted")
        ui.button("Download a backup first (zip)", icon="download", color=None, on_click=lambda: ui.download.content(
            state.store.backup_zip(), f"wortschatz_backup_{datetime.now():%Y-%m-%d}.zip")).props("outline no-caps dense")
        with ui.row().classes("justify-end w-full"):
            ui.button("Cancel", on_click=dialog.close).props("flat no-caps")
            ui.button("Reset everything", icon="delete_forever", on_click=confirm).props("unelevated no-caps color=negative")
    dialog.open()
