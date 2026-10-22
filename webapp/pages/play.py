"""Play: study cards, then the typed test, then the results. One page, three stages."""
from nicegui import events, ui

from wortschatz import answers, config, points
from wortschatz.session import Feedback

from .. import components as C
from ..layout import frame
from ..state import state

PRAISE = ["Richtig!", "Genau!", "Sehr gut!", "Stimmt!", "Perfekt!"]
SPECIAL = ["ä", "ö", "ü", "ß"]
FIELD_LABELS = {"infinitive": "Infinitive", "past": "Präteritum", "perfect": "Perfekt"}
NAV_FOR_MODE = {config.PHASE_LEARN: "learn", config.PHASE_RETEST: "second", config.PHASE_DIARY: "test"}
ROOM_VAR = {config.PHASE_LEARN: "--learn", config.PHASE_RETEST: "--second", config.PHASE_DIARY: "--test"}
TITLES = {config.PHASE_LEARN: "Learn room · studying", config.PHASE_RETEST: "Second-chance room · re-test",
          config.PHASE_DIARY: "Test room · revision"}


def verdict(feedback: Feedback) -> tuple[str, str] | None:
    """(css class, text) for the word-level result, shown when the last question of a word is answered."""
    t = feedback.transition
    if t is None:
        return None
    word = feedback.item.word["german"]
    if t.entered_diary:
        return "in", f"✓ “{word}” goes into your diary"
    if t.passed:
        return "in", f"✓ “{word}” stays in your diary"
    if t.left_diary:
        return "back", f"↩ “{word}” goes back to the second-chance list"
    if t.before is None:
        return "out", f"“{word}” goes to the second-chance list"
    return "out", f"“{word}” stays in the second-chance list"


def play() -> None:
    run = state.run
    with frame(NAV_FOR_MODE.get(run.mode, "learn") if run else "learn") as shell:
        if run is None:
            C.empty_state("sports_esports", "Nothing in progress", "Pick some words to learn, re-test or revise.", "Choose words", "/learn")
            return

        def leave(target: str) -> None:
            state.end_run()
            ui.navigate.to(target)

        # ------------------------------------------------------------------ study cards
        def cards_view() -> None:
            deck = run.deck
            word = deck.current
            with ui.column().classes("w-full items-center gap-3"):
                with ui.row().classes("w-full items-center justify-between"):
                    ui.label(f"Card {deck.index + 1} of {len(deck.words)}").classes("muted")
                    C.segmented({"de": "German first", "en": "English first"}, run.front,
                                lambda e: (setattr(run, "front", e.value), setattr(run, "flipped", False), view.refresh()))
                ui.linear_progress(value=(deck.index + 1) / len(deck.words), show_value=False).props("rounded size=8px color=primary")

                faces = (C.german_face, C.english_face) if run.front == "de" else (C.english_face, C.german_face)
                scene = ui.element("div").classes("flip-scene")
                with scene:
                    card = ui.element("div").classes("flip-card" + (" flipped" if run.flipped else ""))
                    with card:
                        with ui.element("div").classes("flip-face front"):
                            faces[0](word, "Click or press Space to flip")
                        with ui.element("div").classes("flip-face back"):
                            faces[1](word, "Click or press Space to flip back")

                def flip() -> None:
                    run.flipped = not run.flipped
                    card.classes(add="flipped") if run.flipped else card.classes(remove="flipped")

                scene.on("click", flip)
                with ui.row().classes("items-center gap-3"):
                    ui.button("Back", icon="arrow_back", on_click=lambda: step(-1)).props("flat no-caps").set_enabled(deck.index > 0)
                    if deck.last:
                        ui.button("Start the test", icon="quiz", on_click=start_test).props("unelevated no-caps size=lg color=primary")
                    else:
                        ui.button("Next", icon="arrow_forward", on_click=lambda: step(1)).props("unelevated no-caps size=lg color=primary")
                    if not deck.last:
                        ui.button("Skip to the test", on_click=start_test).props("flat no-caps color=grey-7")
                ui.html('<span class="muted text-sm"><span class="kbd">←</span> <span class="kbd">→</span> to move · '
                        '<span class="kbd">Space</span> to flip</span>')
            run._flip = flip                                   # used by the keyboard handler

        def step(delta: int) -> None:
            (run.deck.next if delta > 0 else run.deck.previous)()
            run.flipped = False
            view.refresh()

        def start_test() -> None:
            run.begin_test()
            view.refresh()

        # ------------------------------------------------------------------ the test
        def test_view() -> None:
            test = run.test
            if test.finished:
                run.stage = "results"
                return results_view()
            item, feedback = test.current, test.feedback
            word = item.word
            with ui.column().classes("w-full items-center gap-3"):
                with ui.row().classes("w-full items-center justify-between"):
                    ui.label(f"Question {min(test.index + 1, test.total)} of {test.total}").classes("muted")
                    ui.html(C.chip(config.DIRECTIONS[item.direction]))
                ui.linear_progress(value=len(test.log) / test.total, show_value=False).props("rounded size=8px color=primary")
                prompt_card(item)
                if feedback is None:
                    answer_form(item)
                else:
                    feedback_view(feedback)

        def prompt_card(item) -> None:
            word = item.word
            with ui.element("div").classes("prompt-card"):
                if item.direction == "de_en":
                    ui.html('<div class="eyebrow">Translate into English</div>')
                    ui.html(f'<div class="big-word">{C.german_html(word)}</div>')
                else:
                    extra = (" with its article" if word["article"] else "") if not answers.has_forms(word) else " and its forms"
                    ui.html(f'<div class="eyebrow">Write it in German{extra}</div>')
                    ui.html(f'<div class="big-word">{C.esc(word["english"])}</div>')
                ui.html(C.chip(C.class_label(word["word_class"])))

        def answer_form(item) -> None:
            word = item.word
            fields = answers.german_fields(word) if item.direction == "en_de" else ["answer"]
            inputs: list[ui.input] = []
            for i, field in enumerate(fields):
                if item.direction == "de_en":
                    label, hint = "English", "type the English translation"
                elif field == "answer":
                    label, hint = "German", "article + word, e.g. der Tisch" if word["article"] else "type the German word"
                else:
                    label, hint = FIELD_LABELS[field], {"infinitive": "gehen", "past": "ging", "perfect": "ist gegangen"}[field]
                inputs.append(ui.input(label=label, placeholder=hint).props("outlined" + (" autofocus" if i == 0 else "")
                                                                             + " autocomplete=off").classes("answer-box"))

            def submit() -> None:
                values = [i.value or "" for i in inputs]
                run.test.submit(tuple(values) if len(values) > 1 else values[0])
                if run.test.feedback.word_done:
                    shell.refresh()
                view.refresh()

            def skip() -> None:
                run.test.skip()
                if run.test.feedback.word_done:
                    shell.refresh()
                view.refresh()

            for index, field in enumerate(inputs):
                if index < len(inputs) - 1:
                    field.on("keydown.enter", lambda _e, nxt=inputs[index + 1]: nxt.run_method("focus"))
                else:
                    field.on("keydown.enter", submit)
            if item.direction == "en_de":
                with ui.row().classes("gap-1 items-center"):
                    ui.label("Special letters").classes("muted text-xs")
                    for char in SPECIAL:
                        ui.button(char, color=None).props("dense outline no-caps size=md tabindex=-1").classes("charbtn").on(
                            "mousedown.prevent", lambda _e, c=char: ui.run_javascript(f"insertChar('{c}')"))
            with ui.row().classes("gap-3 items-center"):
                ui.button("Check", icon="check", on_click=submit).props("unelevated no-caps size=lg color=primary")
                ui.button("I don't know", on_click=skip).props("flat no-caps color=grey-7")
            ui.html('<span class="muted text-sm"><span class="kbd">Enter</span> to check · umlauts may be typed as ae, oe, ue, ss</span>')

        def feedback_view(feedback: Feedback) -> None:
            check, item = feedback.check, feedback.item
            word = item.word
            index = len(run.test.log)
            head = PRAISE[index % len(PRAISE)] if check.correct else ("Almost — check the spelling" if check.near_miss else "Not quite")
            expected = (C.esc(check.expected) if item.direction == "de_en"
                        else (f'{C.article_span(word["article"])} {C.esc(word["german"])}'.strip() if not answers.has_forms(word)
                              else C.esc(check.expected)))
            with ui.element("div").classes("fb " + ("ok" if check.correct else "bad")):
                ui.html(f'<div class="head">{"✅" if check.correct else "❌"} {C.esc(head)}</div>'
                        f'<div class="expected">{expected}</div>')
                if not check.correct:
                    typed = check.given.strip(" ·-–—") or "(nothing)"
                    ui.html(f'<div class="muted">You typed: {C.esc(typed)}{(" · " + C.esc(check.message)) if check.message else ""}</div>')
                if word["word_class"] == "noun" and word["plural"] and item.direction == "en_de":
                    ui.html(f'<div class="muted">Plural: die {C.esc(word["plural"])}</div>')
                v = verdict(feedback)
                if v:
                    ui.html(f'<div style="margin-top:.6rem"><span class="verdict {v[0]}">{C.esc(v[1])}</span></div>')
                elif len(run.test.directions) > 1:
                    ui.html('<div class="muted" style="margin-top:.4rem">One more question about this word to come.</div>')
            ui.button("Continue", icon="arrow_forward", on_click=advance).props("unelevated no-caps size=lg color=primary")
            ui.html('<span class="muted text-sm"><span class="kbd">Enter</span> to continue</span>')

        def advance() -> None:
            if run.test.feedback is None:
                return
            run.test.advance()
            if run.test.finished:
                run.stage = "results"
            view.refresh()

        # ------------------------------------------------------------------ results
        def results_view() -> None:
            res = run.test.results()
            passed, failed = res["passed"], res["failed"]
            total = len(passed) + len(failed)
            with ui.column().classes("w-full gap-4"):
                earned = points.round_points(run.mode, len(passed))
                before, after = points.level_for(state.points_before), state.level()
                with ui.element("div").classes("hero w-full"):
                    ui.html(f'<h1>{len(passed)} of {total} words passed</h1>'
                            f'<p>{res["correct"]} of {res["answered"]} answers correct. '
                            + ("Perfect round!" if not failed else "Words you missed are waiting in the second-chance room.") + '</p>'
                            + (f'<p style="margin-top:.7rem"><span class="pointsburst">+{earned} points</span> '
                               f'&nbsp; Level {after.number} · {after.title}</p>' if earned else ''), sanitize=False)
                if after.number > before.number:
                    with ui.row().classes("card-flat items-center gap-3 w-full").style("border-color:var(--brass);background:color-mix(in srgb, var(--brass) 12%, var(--surface))"):
                        ui.icon("emoji_events", color="amber-9", size="2rem")
                        ui.label(f"Level up! You are now level {after.number}: {after.title}.").classes("text-lg font-bold")
                with ui.row().classes("w-full gap-4 items-start max-md:flex-wrap no-wrap"):
                    with ui.column().classes("card grow gap-2").style("flex:1"):
                        label = "In your diary" if run.mode != config.PHASE_DIARY else "Still in your diary"
                        ui.html(f'<b style="color:var(--good);font-size:1.1rem">✓ {label} ({len(passed)})</b>')
                        for r in passed:
                            ui.html(f'<div class="mid-word" style="font-size:1.25rem">{C.german_html(r["word"])} '
                                    f'<span class="muted" style="font-weight:400;font-size:.95rem">{C.esc(r["word"]["english"])}</span></div>')
                        if not passed:
                            ui.label("None this time.").classes("muted")
                    with ui.column().classes("card grow gap-2").style("flex:1"):
                        ui.html(f'<b style="color:#B7791F;font-size:1.1rem">↺ Second chance ({len(failed)})</b>')
                        for r in failed:
                            wrong = r["wrong"][0].check if r["wrong"] else None
                            typed = f' · you typed “{C.esc(wrong.given.strip(" ·-–—"))}”' if wrong and wrong.given.strip(" ·-–—") else ""
                            ui.html(f'<div class="mid-word" style="font-size:1.25rem">{C.german_html(r["word"])} '
                                    f'<span class="muted" style="font-weight:400;font-size:.95rem">{C.esc(r["word"]["english"])}{typed}</span></div>')
                        if not failed:
                            ui.label("Nothing to repeat. Nice!").classes("muted")
                with ui.row().classes("gap-3"):
                    counts = state.counts()
                    if run.mode == config.PHASE_LEARN:
                        ui.button("Back to the Learn room", icon="school", on_click=lambda: leave("/learn")).props("unelevated no-caps size=lg color=primary")
                    if counts["second"]:
                        ui.button(f"Second-chance room ({counts['second']})", icon="replay", on_click=lambda: leave("/second-chance"), color=None).props("outline no-caps size=lg")
                    ui.button("Open the diary", icon="menu_book", on_click=lambda: leave("/diary"), color=None).props("outline no-caps size=lg")

        # ------------------------------------------------------------------ the page
        @ui.refreshable
        def view() -> None:
            if run.stage == "cards":
                cards_view()
            elif run.stage == "test":
                test_view()
            else:
                results_view()

        def on_key(event: events.KeyEventArguments) -> None:
            if not event.action.keydown or event.action.repeat:
                return
            if run.stage == "cards":
                if event.key.arrow_right and not run.deck.last:
                    step(1)
                elif event.key.arrow_left and run.deck.index > 0:
                    step(-1)
                elif event.key.space or event.key.enter:
                    getattr(run, "_flip", lambda: None)()
            elif run.stage == "test" and run.test.feedback is not None and (event.key.enter or event.key.space):
                advance()

        ui.keyboard(on_key=on_key)
        with ui.column().classes("w-full gap-3").style(f"--room:var({ROOM_VAR[run.mode]})"):
            with ui.row().classes("w-full items-center justify-between"):
                ui.label(TITLES[run.mode]).classes("text-3xl font-bold serif")
                ui.button("End session", icon="close", on_click=lambda: leave("/")).props("flat no-caps color=grey-7").tooltip(
                    "Words you have finished are already saved.")
            view()
