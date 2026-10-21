"""Wortschatz: learn German words, pass the test, build your own diary.

Run with:   python main.py      (opens http://localhost:8080)
Environment (optional): PORT=8081 to change the port, NO_BROWSER=1 to not open the browser.
"""
import os

from nicegui import ui

from webapp import routes, theme

theme.install()
routes.register()

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="Wortschatz · German vocabulary game", favicon="📖", port=int(os.environ.get("PORT", 8080)), reload=False,
           show="NO_BROWSER" not in os.environ, storage_secret="wortschatz-local-single-user")
