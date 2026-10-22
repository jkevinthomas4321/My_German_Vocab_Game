"""The Guide: a pop-up (three tabs) explaining the rooms, the points, and how to learn and track progress."""
from __future__ import annotations

from nicegui import ui

from wortschatz import config, points

from . import components as C


def _step(number: int, title: str, text: str, color: str = "var(--brand)") -> None:
    ui.html(f'<div class="guide-step"><div class="no" style="background:{color}">{number}</div>'
            f'<div><b>{C.esc(title)}</b><br><span class="muted">{C.esc(text)}</span></div></div>', sanitize=False)


def _how_it_works() -> None:
    ui.label("Walk to a room").classes("text-xl font-bold serif")
    ui.html("On the map, walk with <span class='kbd'>W</span> <span class='kbd'>A</span> <span class='kbd'>S</span> <span class='kbd'>D</span> or the arrow keys, or click where you want to go. "
            "Step on a glowing pad and press <span class='kbd'>E</span> (or click the pad) to enter. In every room you first choose a word list, then you play.", sanitize=False)
    _step(1, "Learn room", "Pick nouns, verbs or adjectives and how many. Study the flip cards, then take a typed test, German → English and English → German.", "var(--learn)")
    _step(2, "Second-chance room", "Words you missed wait here. Study them again and take a re-test. Pass it and the word moves to your diary.", "var(--second)")
    _step(3, "Test room", "Revision: test yourself on the words in your diary. A word you miss goes back to the second-chance room.", "var(--test)")
    _step(4, "Diary", "Your personal room: only words you have passed live here. Browse them, search them, export them.", "var(--stay)")
    with ui.column().classes("card-flat w-full gap-1").style("background:var(--surface-2)"):
        ui.label("The one rule").classes("font-bold")
        ui.html("A word <b>passes</b> only if <b>every</b> question about it is right.<br>"
                "Pass → <b style='color:var(--good)'>diary</b>. Miss → <b style='color:var(--second)'>second chance</b>. "
                "Pass the re-test → <b style='color:var(--good)'>diary</b>. Miss a revision → back to <b style='color:var(--second)'>second chance</b>.", sanitize=False)


def _points() -> None:
    ui.label("How your points work").classes("text-xl font-bold serif")
    ui.label("You earn points for words you have proven. You never lose points, and a miss simply earns 0.").classes("muted")
    rows = [(points.POINTS_PER_PASS[config.PHASE_LEARN], "Pass a new word on its first test", "Learn room"),
            (points.POINTS_PER_PASS[config.PHASE_RETEST], "Rescue a word from the second chance list", "Second-chance room"),
            (points.POINTS_PER_PASS[config.PHASE_DIARY], "Pass a word in a diary revision", "Test room"),
            (0, "Miss a word", "no penalty: study it and try again")]
    for pts, what, where in rows:
        ui.html(f'<div class="pointrow"><div class="pts">+{pts}</div><div><b>{C.esc(what)}</b><br><span class="muted">{C.esc(where)}</span></div></div>', sanitize=False)
    ui.label("Levels").classes("font-bold").style("margin-top:.6rem")
    ui.html('<div style="display:flex;flex-wrap:wrap;gap:.5rem">' + "".join(
        f'<span class="chip" style="font-size:.85rem">Level {lv.number} · {C.esc(lv.title)} · from {lv.floor} pts</span>'
        for lv in points.level_table(7)) + "</div>", sanitize=False)
    ui.label("Each level needs more points than the last. Your level and points are always shown in the menu. "
             "They are worked out from your answer log, so they always match what you really did.").classes("muted text-sm")


def _track() -> None:
    ui.label("Learn well, and track it").classes("text-xl font-bold serif")
    ui.label("Studying cards").classes("font-bold")
    ui.html("Click a card or press <span class='kbd'>Space</span> to flip it. Use <span class='kbd'>←</span> <span class='kbd'>→</span> to move. "
            "Switch between <b>German first</b> and <b>English first</b> to practise both directions.", sanitize=False)
    ui.label("Typing answers").classes("font-bold")
    ui.html("Nouns need their article (<b>der Tisch</b>). Verbs have three boxes: infinitive, Präteritum and Perfekt. "
            "Press <span class='kbd'>Enter</span> to check and again to continue. You may type <b>ae oe ue ss</b> for ä ö ü ß, or use the letter buttons.", sanitize=False)
    ui.label("Tracking your progress").classes("font-bold")
    ui.html("<b>Diary</b>: every word in your diary, with how often you passed it in a row. Download it as CSV or Excel.<br>"
            "<b>Progress</b> (menu): how your diary grows, your pass rate, which direction is harder, whether second chances work, "
            "whether diary words fade, and your hardest words.<br>"
            "<b>Your files</b>: your diary and every answer are saved as plain CSV in the <span class='kbd'>user_data</span> folder, on your computer only.", sanitize=False)
    ui.label("Your own words").classes("font-bold")
    ui.html("Open <b>Word lists</b> in the menu (or the mailbox in the garden) and drop in an Excel or CSV sheet.", sanitize=False)


def build() -> ui.dialog:
    """The guide dialog for the current page; call `.open()` on it."""
    with ui.dialog() as dialog, ui.card().classes("guide-card gap-2"):
        with ui.row().classes("w-full items-center justify-between no-wrap"):
            ui.label("Guide").classes("text-2xl font-bold serif")
            ui.button(icon="close", on_click=dialog.close, color=None).props("flat round dense")
        with ui.tabs().props("no-caps align=left active-color=primary indicator-color=amber-8").classes("w-full") as tabs:
            one = ui.tab("How the game works", icon="home")
            two = ui.tab("Points", icon="emoji_events")
            three = ui.tab("Learn & track", icon="insights")
        with ui.tab_panels(tabs, value=one).classes("w-full").style("max-height:60vh;overflow:auto;background:transparent"):
            with ui.tab_panel(one).classes("gap-2"):
                _how_it_works()
            with ui.tab_panel(two).classes("gap-2"):
                _points()
            with ui.tab_panel(three).classes("gap-2"):
                _track()
        with ui.row().classes("w-full justify-end"):
            ui.button("Got it", on_click=dialog.close).props("unelevated no-caps color=primary")
    return dialog
