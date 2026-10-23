"""The Guide: three cards under the mode buttons on the opening page (how the game works, points, learning and tracking)."""
from __future__ import annotations

from nicegui import ui

from wortschatz import config, points

from . import components as C


def _step(number: int, title: str, text: str, color: str = "var(--accent)") -> None:
    ui.html(f'<div class="guide-step"><div class="no" style="background:{color}">{number}</div>'
            f'<div><b>{C.esc(title)}</b><br><span class="muted">{C.esc(text)}</span></div></div>', sanitize=False)


def _how_it_works() -> None:
    ui.label("How the game works").classes("text-xl font-bold")
    ui.html("Click a mode (or press <span class='kbd'>1</span>–<span class='kbd'>4</span>): your character runs to it, jumps on it, and the mode starts. "
            "In every mode you first choose a word list.", sanitize=False).classes("muted")
    _step(1, "Learn", "Pick nouns, verbs or adjectives and how many. Study the flip cards, then take a typed test, German → English and English → German.", "var(--learn)")
    _step(2, "Second chance", "Words you missed wait here. Study them again and take a re-test. Pass it and the word moves to your diary.", "var(--second)")
    _step(3, "Test", "Revision: test yourself on the words in your diary. A word you miss goes back to second chance.", "var(--test)")
    _step(4, "Diary", "Your personal room: only words you have passed live here. Browse them, search them, export them.", "var(--stay)")
    with ui.column().classes("card-flat w-full gap-1").style("background:var(--surface-2)"):
        ui.label("The one rule").classes("font-bold")
        ui.html("A word <b>passes</b> only if <b>every</b> question about it is right.<br>"
                "Pass → <b style='color:var(--good)'>diary</b>. Miss → <b style='color:var(--second)'>second chance</b>. "
                "Pass the re-test → <b style='color:var(--good)'>diary</b>. Miss a revision → back to <b style='color:var(--second)'>second chance</b>.", sanitize=False)


def _points() -> None:
    ui.label("How your points work").classes("text-xl font-bold")
    ui.label("You earn points for words you have proven. You never lose points, and a miss simply earns 0.").classes("muted")
    rows = [(points.POINTS_PER_PASS[config.PHASE_LEARN], "Pass a new word on its first test", "Learn"),
            (points.POINTS_PER_PASS[config.PHASE_RETEST], "Rescue a word from the second chance list", "Second chance"),
            (points.POINTS_PER_PASS[config.PHASE_DIARY], "Pass a word in a diary revision", "Test"),
            (0, "Miss a word", "no penalty: study it and try again")]
    for pts, what, where in rows:
        ui.html(f'<div class="pointrow"><div class="pts">+{pts}</div><div><b>{C.esc(what)}</b><br><span class="muted">{C.esc(where)}</span></div></div>', sanitize=False)
    ui.label("Levels").classes("font-bold").style("margin-top:.6rem")
    ui.html('<div style="display:flex;flex-wrap:wrap;gap:.5rem">' + "".join(
        f'<span class="chip" style="font-size:.85rem">Level {lv.number} · {C.esc(lv.title)} · from {lv.floor} pts</span>'
        for lv in points.level_table(7)) + "</div>", sanitize=False)
    ui.label("Each level needs more points than the last. Your level and points are shown at the top of every page. "
             "They are worked out from your answer log, so they always match what you really did.").classes("muted text-sm")


def _track() -> None:
    ui.label("Learn well, and track it").classes("text-xl font-bold")
    ui.label("Studying cards").classes("font-bold")
    ui.html("Click a card or press <span class='kbd'>Space</span> to flip it. Use <span class='kbd'>←</span> <span class='kbd'>→</span> to move. "
            "Switch between <b>German first</b> and <b>English first</b> to practise both directions.", sanitize=False)
    ui.label("Typing answers").classes("font-bold")
    ui.html("Nouns need their article (<b>der Tisch</b>). Verbs have three boxes: infinitive, Präteritum and Perfekt. "
            "Press <span class='kbd'>Enter</span> to check and again to continue. You may type <b>ae oe ue ss</b> for ä ö ü ß, or use the letter buttons.", sanitize=False)
    ui.label("Tracking your progress").classes("font-bold")
    ui.html("<b>Diary</b>: every word you have proven, with how often you passed it in a row. Download it as CSV or Excel.<br>"
            "<b>Progress</b>: how your diary grows, your pass rate, which direction is harder, whether second chances work, "
            "whether diary words fade, and your hardest words.<br>"
            "<b>Your files</b>: your diary and every answer are saved as plain CSV in the <span class='kbd'>user_data</span> folder, on your computer only.", sanitize=False)
    ui.label("Your own words").classes("font-bold")
    ui.html("Open <b>Word lists</b>, drop in an Excel or CSV file with English, German and (optionally) article, plural, past and perfect tense. "
            "The game cleans it, shows what it changed, and lets you learn from it.", sanitize=False)


def build() -> ui.dialog:
    """The Guide pop-up: three tabs. Open it with `.open()`; it is only shown when someone asks for it."""
    with ui.dialog() as dialog, ui.card().classes("guide-card gap-2"):
        with ui.row().classes("w-full items-center justify-between no-wrap"):
            ui.label("Guide").classes("text-2xl font-bold")
            ui.button(icon="close", on_click=dialog.close, color=None).props("flat round dense")
        with ui.tabs().classes("w-full") as tabs:
            how = ui.tab("How the game works", icon="route")
            pts = ui.tab("Points", icon="emoji_events")
            track = ui.tab("Learn & track", icon="insights")
        with ui.tab_panels(tabs, value=how).classes("w-full").style("overflow:auto;max-height:58vh;background:transparent"):
            for tab, part in ((how, _how_it_works), (pts, _points), (track, _track)):
                with ui.tab_panel(tab).classes("gap-2"):
                    part()
        with ui.row().classes("justify-end w-full"):
            ui.button("Got it", on_click=dialog.close).props("unelevated no-caps color=primary")
    return dialog
