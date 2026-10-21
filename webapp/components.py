"""Small reusable pieces: stat tiles, German words with coloured articles, flash-card faces."""
from __future__ import annotations

import html
from typing import Mapping

from nicegui import ui

from wortschatz import config

FORM_LABELS = (("Präteritum", "past_tense"), ("Perfekt", "perfect_tense"))


def esc(text: object) -> str:
    return html.escape(str(text))


def article_span(article: str) -> str:
    return f'<span class="art art-{esc(article)}">{esc(article)}</span>' if article in config.ARTICLES else ""


def german_html(word: Mapping) -> str:
    """'der Tisch' with the article in its colour."""
    return f'{article_span(word["article"])} {esc(word["german"])}'.strip()


def tile(label: str, value: str, sub: str = "") -> None:
    with ui.element("div").classes("tile"):
        ui.html(f'<div class="label">{esc(label)}</div><div class="value">{esc(value)}</div>'
                + (f'<div class="sub">{esc(sub)}</div>' if sub else ""))


def tiles(items: list[tuple[str, str, str]]) -> None:
    with ui.row().classes("w-full gap-3 no-wrap max-md:flex-wrap"):
        for label, value, sub in items:
            tile(label, value, sub)


def chip(text: str) -> str:
    return f'<span class="chip">{esc(text)}</span>'


def class_label(word_class: str) -> str:
    return {"noun": "noun", "verb": "verb", "adjective": "adjective"}.get(word_class, word_class)


def german_face(word: Mapping, hint: str = "") -> None:
    """German side of a card: article pill + word, plural, verb forms."""
    ui.html('<div class="eyebrow">German</div>')
    if word["word_class"] == "noun" and word["article"] in config.ARTICLES:
        ui.html(f'<div style="display:flex;align-items:center;gap:.8rem;justify-content:center">'
                f'<span class="art-pill {esc(word["article"])}">{esc(word["article"])}</span>'
                f'<span class="big-word">{esc(word["german"])}</span></div>')
        if word["plural"]:
            ui.html(f'<div class="muted">Plural: die {esc(word["plural"])}</div>')
    else:
        ui.html(f'<div class="big-word">{esc(word["german"])}</div>')
        if word["word_class"] == "verb" and word["past_tense"]:
            rows = "".join(f'<span class="k">{label}</span><span>{esc(word[key])}</span>' for label, key in FORM_LABELS if word[key])
            ui.html(f'<div class="forms">{rows}</div>')
    ui.html(chip(class_label(word["word_class"])))
    if hint:
        ui.html(f'<div class="flip-hint">{esc(hint)}</div>')


def english_face(word: Mapping, hint: str = "") -> None:
    ui.html('<div class="eyebrow">English</div>')
    ui.html(f'<div class="big-word">{esc(word["english"])}</div>')
    ui.html(chip(class_label(word["word_class"])))
    if hint:
        ui.html(f'<div class="flip-hint">{esc(hint)}</div>')


def segmented(options: dict, value, on_change=None):
    """A toggle whose selected option is clearly highlighted."""
    return ui.toggle(options, value=value, on_change=on_change).props(
        "no-caps unelevated toggle-color=primary toggle-text-color=white").classes("segmented")


def empty_state(icon: str, title: str, text: str, button: str | None = None, target: str | None = None) -> None:
    with ui.column().classes("card items-center text-center w-full gap-2").style("padding:2.5rem"):
        ui.icon(icon, size="3rem").classes("muted")
        ui.label(title).classes("text-xl font-bold")
        ui.label(text).classes("muted")
        if button and target:
            ui.button(button, on_click=lambda: ui.navigate.to(target)).props("unelevated no-caps color=primary")
