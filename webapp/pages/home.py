"""The home page: a 2D drawing of a house with four rooms. Click a room to step inside."""
from nicegui import ui

from wortschatz import stats

from .. import components as C
from .. import house
from ..layout import frame
from ..state import state


def room(key: str, title: str, subtitle: str, count: str, target: str, glow: bool = False) -> None:
    """One clickable room of the house, drawn as an illustration with a name plaque and a counter."""
    def enter() -> None:
        ui.navigate.to(target)

    box = ui.element("div").classes(f"room room-{key}" + (" glow" if glow else "")).props(f'tabindex=0 role=button aria-label="Enter the {title}"')
    box.on("click", enter)
    box.on("keydown.enter", enter)
    with box:
        ui.html(house.ROOM_ART[key](), sanitize=False)
        ui.html(f'<div class="plaque"><div class="t">{C.esc(title)}</div><div class="s">{C.esc(subtitle)}</div></div>', sanitize=False)
        ui.html(f'<div class="roomcount">{C.esc(count)}</div>', sanitize=False)
        ui.html('<div class="roomenter">Enter →</div>', sanitize=False)


def home() -> None:
    with frame("home") as shell:
        guide_dialog = shell.guide
        counts = state.counts()
        kpi = stats.kpis(state.store.progress, state.store.attempts())
        level = state.level()

        with ui.column().classes("gap-0"):
            ui.label("Welcome home").classes("text-3xl font-bold serif")
            ui.label("Click a room to step inside. In every room you choose a word list first, then you play.").classes("muted")

        with ui.element("div").classes("scene"):
            with ui.element("div").classes("sky"):
                ui.element("div").classes("sun")
                for name in ("c1", "c2", "c3"):
                    ui.html(f'<div class="cloud {name}">{house.CLOUD}</div>', sanitize=False)
            with ui.element("div").classes("roofwrap"):
                ui.element("div").classes("chimney")
                for name in ("s1", "s2", "s3"):
                    ui.element("div").classes(f"smoke {name}")
                ui.html(house.ROOF, sanitize=False)
            with ui.element("div").classes("housebody"):
                room("learn", "Learn room", "Study new words", f"{counts['new']} new", "/learn")
                room("test", "Test room", "Revise your diary", f"{counts['diary']} to revise", "/test")
                room("second", "Second-chance room", "Words to try again", f"{counts['second']} waiting", "/second-chance", glow=counts["second"] > 0)
                room("stay", "Living room", "Where your words stay", f"{counts['diary']} in the diary", "/diary")
            with ui.element("div").classes("ground"):
                ui.element("div").classes("path")
                ui.html(house.TREE, sanitize=False)
                ui.html(house.BUSH, sanitize=False)
                ui.html(house.BUSH.replace("deco-bush", "deco-bush b2"), sanitize=False)
                with ui.element("div").classes("signpost"):
                    ui.element("div").classes("post")
                    with ui.element("div").classes("sign s1").on("click", guide_dialog.open):
                        ui.label("Guide")
                    with ui.element("div").classes("sign s2").on("click", lambda: ui.navigate.to("/stats")):
                        ui.label("Progress")
                ui.html(house.MAILBOX, sanitize=False).classes("mailbox").on("click", lambda: ui.navigate.to("/words")).tooltip("Word lists")
            ui.label("Tip: the signpost opens the guide and your progress. The mailbox holds your word lists.").classes("hint")

        C.tiles([("Level", f"{level.number}", f"{level.title} · {level.points} points"), ("Points today", f"+{state.points_today()}", "from words you proved"),
                 ("Streak", f"{kpi['streak']} d", f"best {kpi['best_streak']} d"), ("Words tested today", str(kpi["today_words"]), "")])
