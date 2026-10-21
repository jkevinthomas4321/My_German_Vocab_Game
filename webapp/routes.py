"""The URL of every page. `register()` is called by main.py each time the app starts."""
from nicegui import ui

from .pages import diary, home, learn, play, second_chance, stats_page, words

ROUTES = {
    "/": home.home,
    "/learn": learn.learn,
    "/play": play.play,
    "/second-chance": second_chance.second_chance,
    "/diary": diary.diary,
    "/stats": stats_page.stats_page,
    "/words": words.words_page,
}


def register() -> None:
    for path, page in ROUTES.items():
        ui.page(path)(page)
