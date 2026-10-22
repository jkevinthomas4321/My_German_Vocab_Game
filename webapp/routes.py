"""The URL of every page. `register()` is called by main.py each time the app starts."""
from pathlib import Path

from nicegui import app, ui

from .pages import diary, home, learn, play, second_chance, stats_page, testroom, words

ROUTES = {
    "/": home.home,
    "/learn": learn.learn,
    "/play": play.play,
    "/test": testroom.test_room,
    "/second-chance": second_chance.second_chance,
    "/diary": diary.diary,
    "/stats": stats_page.stats_page,
    "/words": words.words_page,
}


STATIC = Path(__file__).resolve().parent / "static"


def register() -> None:
    app.add_static_files("/static-wortschatz", STATIC)
    for path, page in ROUTES.items():
        ui.page(path)(page)
