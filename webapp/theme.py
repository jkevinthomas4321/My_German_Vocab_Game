"""Design system: colours, typography and the CSS for every component."""
from __future__ import annotations

from nicegui import ui

# Article colours follow the convention many German courses use: der blue, die red, das green.
ARTICLE_COLORS = {"der": "#2A6FDB", "die": "#D6334C", "das": "#2F9E6B"}

CSS = """
:root {
  --bg: #F6F3EC; --surface: #FFFFFF; --surface-2: #FBF9F4; --ink: #1F2430; --muted: #6B7280; --line: #E7E1D5;
  --brand: #1F3A5F; --brand-2: #2C5282; --accent: #E3A008;
  --der: #2A6FDB; --die: #D6334C; --das: #2F9E6B; --good: #2F855A; --good-bg: #EAF7F0; --bad: #C8102E; --bad-bg: #FDEEF0;
  --shadow: 0 1px 2px rgba(31,36,48,.05), 0 8px 24px rgba(31,36,48,.06);
  --serif: "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif;
}
body.body--dark {
  --bg: #11151C; --surface: #1A212B; --surface-2: #161C25; --ink: #E8EAED; --muted: #9AA3AF; --line: #2A3340;
  --good-bg: #12301F; --bad-bg: #38151B; --shadow: 0 1px 2px rgba(0,0,0,.4), 0 8px 24px rgba(0,0,0,.35);
}
body { background: var(--bg) !important; color: var(--ink); font-feature-settings: "tnum"; }
.q-page-container, .q-layout { background: var(--bg); }
.serif { font-family: var(--serif); }
.muted { color: var(--muted); }
.page { width: min(1120px, 94vw); margin: 0 auto; padding: 1.4rem 0 3rem 0; gap: 1.1rem; }

/* header + navigation */
.app-header { background: linear-gradient(120deg, #14243B 0%, #1F3A5F 60%, #2C5282 100%) !important; box-shadow: 0 2px 14px rgba(20,36,59,.25); padding: 0 1.2rem; }
.app-header .brand { font-family: var(--serif); font-size: 1.55rem; font-weight: 700; color: #fff; letter-spacing: -.01em; }
.flag { display: flex; height: 4px; width: 100%; border-radius: 2px; overflow: hidden; margin-top: 2px; }
.flag i { flex: 1; display: block; }
.nav-link { color: #CBD5E1; padding: .45rem .85rem; border-radius: 999px; font-weight: 500; text-decoration: none !important; transition: all .15s; white-space: nowrap; display: inline-flex; gap: .4rem; align-items: center; }
.nav-link:hover { background: rgba(255,255,255,.12); color: #fff; }
.nav-link.active { background: rgba(255,255,255,.95); color: #14243B; font-weight: 700; }
.nav-count { background: var(--accent); color: #1F2430; border-radius: 999px; font-size: .72rem; font-weight: 700; padding: 0 .5rem; min-width: 1.3rem; text-align: center; }
.nav-link.active .nav-count { background: #14243B; color: #fff; }

/* surfaces */
.card { background: var(--surface); border: 1px solid var(--line); border-radius: 20px; box-shadow: var(--shadow); padding: 1.3rem 1.5rem; }
.card-flat { background: var(--surface); border: 1px solid var(--line); border-radius: 16px; padding: 1rem 1.2rem; }
.hero { background: linear-gradient(120deg, #14243B 0%, #1F3A5F 55%, #2C5282 100%); color: #fff; border-radius: 24px; padding: 1.8rem 2rem; position: relative; overflow: hidden; box-shadow: var(--shadow); }
.hero:after { content: ""; position: absolute; right: 0; top: 0; bottom: 0; width: 12px; background: linear-gradient(#111 0 33.3%, #D00 33.3% 66.6%, #FFCE00 66.6% 100%); }
.hero h1 { font-family: var(--serif); font-size: 2.1rem; margin: 0 0 .25rem 0; color: #fff; }
.hero p { margin: 0; color: #CBD5E1; }
.stage { position: relative; overflow: hidden; display: flex; flex-direction: column; gap: .5rem; min-height: 15rem; }
.stage:before { content: ""; position: absolute; left: 0; right: 0; top: 0; height: 6px; background: var(--stage, var(--brand)); }
.stage .num { font-size: 3rem; font-weight: 800; line-height: 1; color: var(--stage, var(--brand)); }
.stage .title { font-size: 1.15rem; font-weight: 700; }
.step { display: flex; gap: .7rem; align-items: flex-start; }
.step .dot { width: 1.9rem; height: 1.9rem; border-radius: 50%; background: var(--brand); color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 700; flex: none; }
.tile { background: var(--surface); border: 1px solid var(--line); border-radius: 16px; padding: .8rem 1.1rem; min-width: 8.5rem; flex: 1; }
.tile .label { color: var(--muted); font-size: .74rem; text-transform: uppercase; letter-spacing: .07em; }
.tile .value { font-size: 1.8rem; font-weight: 800; line-height: 1.15; }
.tile .sub { color: var(--muted); font-size: .8rem; }
.chip { display: inline-flex; align-items: center; gap: .3rem; padding: .12rem .65rem; border-radius: 999px; font-size: .78rem; border: 1px solid var(--line); background: var(--surface-2); color: var(--muted); }
.pick { cursor: pointer; border: 2px solid var(--line); border-radius: 16px; padding: .6rem 1rem; background: var(--surface); transition: all .12s; min-width: 7.5rem; text-align: center; }
.pick:hover { border-color: var(--brand-2); transform: translateY(-1px); }
.pick.on { border-color: var(--brand); background: var(--brand); color: #fff; }
.pick .n { font-size: .78rem; opacity: .75; }

/* German words */
.art { font-weight: 700; padding: 0 .1rem; }
.art-der { color: var(--der); } .art-die { color: var(--die); } .art-das { color: var(--das); }
.art-pill { display: inline-block; font-weight: 700; color: #fff; border-radius: 10px; padding: .05rem .6rem; font-size: 1.1rem; }
.art-pill.der { background: var(--der); } .art-pill.die { background: var(--die); } .art-pill.das { background: var(--das); }
.big-word { font-family: var(--serif); font-size: 3.1rem; font-weight: 700; line-height: 1.1; text-align: center; word-break: break-word; }
.mid-word { font-family: var(--serif); font-size: 1.7rem; font-weight: 700; }
.forms { display: grid; grid-template-columns: auto auto; gap: .2rem 1.2rem; font-size: 1.15rem; margin-top: .6rem; }
.forms .k { color: var(--muted); text-align: right; font-size: .85rem; align-self: center; }

/* flip card */
.flip-scene { perspective: 1500px; width: min(640px, 92vw); height: 360px; margin: .4rem auto; cursor: pointer; user-select: none; }
.flip-card { position: relative; width: 100%; height: 100%; transition: transform .6s cubic-bezier(.2,.8,.2,1); transform-style: preserve-3d; }
.flip-card.flipped { transform: rotateY(180deg); }
.flip-face { position: absolute; inset: 0; backface-visibility: hidden; -webkit-backface-visibility: hidden; border-radius: 28px; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 1.5rem; gap: .4rem; box-shadow: var(--shadow); border: 1px solid var(--line); }
.flip-face.front { background: var(--surface); }
.flip-face.back { background: linear-gradient(160deg, #1F3A5F, #14243B); color: #fff; transform: rotateY(180deg); }
.flip-face.back .big-word, .flip-face.back .mid-word { color: #fff; }
.flip-face.back .muted { color: #B6C2D3; }
.flip-hint { position: absolute; bottom: .9rem; left: 0; right: 0; text-align: center; font-size: .78rem; color: var(--muted); }
.flip-face.back .flip-hint { color: #B6C2D3; }

/* test */
.prompt-card { background: var(--surface); border: 1px solid var(--line); border-radius: 26px; box-shadow: var(--shadow); padding: 1.6rem 1.5rem; text-align: center; width: 100%; max-width: 780px; }
.flip-face.back .eyebrow { color: #B6C2D3; }
.segmented { border: 1px solid var(--line); border-radius: 10px; }
.eyebrow { color: var(--muted); font-size: .78rem; text-transform: uppercase; letter-spacing: .09em; }
.answer-box { width: min(520px, 100%); }
.answer-box .q-field__native { font-size: 1.35rem; }
.fb { border-radius: 20px; padding: 1.1rem 1.4rem; width: 100%; max-width: 780px; border: 1px solid var(--line); border-left-width: 7px; }
.fb.ok { background: var(--good-bg); border-left-color: var(--good); }
.fb.bad { background: var(--bad-bg); border-left-color: var(--bad); }
.fb .head { font-size: 1.25rem; font-weight: 800; }
.fb .expected { font-family: var(--serif); font-size: 1.9rem; font-weight: 700; margin: .1rem 0; }
.verdict { border-radius: 12px; padding: .35rem .8rem; font-weight: 600; display: inline-block; }
.verdict.in { background: var(--good-bg); color: var(--good); } .verdict.out { background: #FFF4D6; color: #7A5A00; } .verdict.back { background: var(--bad-bg); color: var(--bad); }
.kbd { border: 1px solid var(--line); border-bottom-width: 2px; border-radius: 6px; padding: 0 .4rem; font-size: .78rem; color: var(--muted); background: var(--surface-2); }
.charbtn { min-width: 2.4rem !important; }

/* tables */
.q-table__container { background: var(--surface); border: 1px solid var(--line); border-radius: 16px; box-shadow: none; }
.q-table thead th { color: var(--muted); font-weight: 600; text-transform: uppercase; font-size: .72rem; letter-spacing: .05em; }
body.body--dark .segmented { background: var(--surface); }
body.body--dark .q-field--outlined .q-field__control { background: var(--surface); }
body.body--dark .pick { color: var(--ink); }
body.body--dark .pick.on { color: #fff; background: #2C5282; border-color: #4C7DB8; }
@media (max-width: 700px) { .big-word { font-size: 2.2rem; } .flip-scene { height: 320px; } .hero h1 { font-size: 1.6rem; } }
"""

HEAD = """
<script>
window.insertChar = function (ch) {
  const el = document.activeElement;
  if (el && el.tagName === 'INPUT') { el.setRangeText(ch, el.selectionStart, el.selectionEnd, 'end'); el.dispatchEvent(new Event('input', {bubbles: true})); }
};
</script>
"""


def install() -> None:
    """Register the stylesheet and helper script for all pages; call once at start-up."""
    ui.add_css(CSS, shared=True)
    ui.add_head_html(HEAD, shared=True)


def colors() -> None:
    """Quasar widget colours; must be set on every page."""
    ui.colors(primary="#1F3A5F", secondary="#2C5282", accent="#E3A008", positive="#2F855A", negative="#C8102E",
              info="#2A6FDB", warning="#E3A008")
