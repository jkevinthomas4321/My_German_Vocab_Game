"""Design system: a classic palette of ivory, deep navy and brass, serif headings, and the CSS for every component."""
from __future__ import annotations

from nicegui import ui

# Article colours follow the convention many German courses use: der blue, die red, das green (muted to suit the palette).
ARTICLE_COLORS = {"der": "#2F5F9E", "die": "#A93A4F", "das": "#2F7D5E"}

CSS = """
:root {
  --bg: #F5F0E6; --surface: #FFFDF8; --surface-2: #FAF6EC; --ink: #1B2433; --muted: #6B6F7A; --line: #E6DCC8;
  --brand: #1B2A41; --brand-2: #2C3E5C; --brass: #B8893A; --brass-2: #D8B16A; --burgundy: #7B2D3B;
  --der: #2F5F9E; --die: #A93A4F; --das: #2F7D5E; --good: #2F6B4F; --good-bg: #E8F3EC; --bad: #9E2A3A; --bad-bg: #F8E9EA;
  --learn: #35506B; --second: #A4553D; --test: #2F5D50; --stay: #9A7B3C;
  --shadow: 0 1px 2px rgba(27,36,51,.05), 0 10px 28px rgba(27,36,51,.07);
  --serif: "Iowan Old Style", "Palatino Linotype", Palatino, "Book Antiqua", Georgia, serif;
}
body.body--dark {
  --bg: #0F141D; --surface: #171F2E; --surface-2: #131A27; --ink: #ECE8DF; --muted: #9AA3B0; --line: #29344A;
  --good-bg: #12301F; --bad-bg: #38151B; --shadow: 0 1px 2px rgba(0,0,0,.4), 0 10px 28px rgba(0,0,0,.4);
}
body { background: var(--bg) !important; color: var(--ink); font-feature-settings: "tnum"; }
.q-page-container, .q-layout, .q-page { background: var(--bg); }
.serif { font-family: var(--serif); }
.muted { color: var(--muted); }
.page { width: min(1120px, 94%); margin: 0 auto; padding: 1.4rem 0 3rem 0; gap: 1.1rem; }
h1, h2, h3 { letter-spacing: -.01em; }

/* ---- header ---- */
.app-header { background: var(--brand) !important; border-bottom: 3px solid var(--brass); padding: 0 .9rem; height: 56px; }
.app-header .brand { font-family: var(--serif); font-size: 1.45rem; font-weight: 700; color: #fff; letter-spacing: .01em; }
.app-header .brand i { color: var(--brass-2); font-style: normal; }
.chip-level { background: rgba(255,255,255,.1); border: 1px solid rgba(216,177,106,.55); color: #F3E6C8; border-radius: 999px; padding: .2rem .8rem; font-size: .85rem; font-weight: 600; white-space: nowrap; }
.burger { color: #fff !important; }

/* ---- sidebar ---- */
.sidebar { background: var(--surface) !important; border-right: 1px solid var(--line) !important; }
.sidebar .side-brand { font-family: var(--serif); font-size: 1.5rem; font-weight: 700; color: var(--brand); }
body.body--dark .sidebar .side-brand { color: var(--brass-2); }
.sidebar .rule { height: 3px; width: 44px; background: var(--brass); border-radius: 2px; margin: .25rem 0 .2rem 0; }
.levelcard { background: linear-gradient(160deg, var(--brand), var(--brand-2)); color: #fff; border-radius: 16px; padding: .9rem 1rem; box-shadow: var(--shadow); }
.levelcard .lv { font-family: var(--serif); font-size: 1.1rem; font-weight: 700; }
.levelcard .pts { color: #E9D8B0; font-size: .82rem; }
.bar { background: rgba(255,255,255,.18); border-radius: 6px; height: 8px; overflow: hidden; margin: .5rem 0 .25rem 0; }
.bar > span { display: block; height: 100%; background: linear-gradient(90deg, var(--brass), var(--brass-2)); border-radius: 6px; transition: width .6s; }
.q-item.navitem { width: 100%; }
.navitem { border-radius: 12px; margin: 2px 0; color: var(--ink); transition: background .15s, transform .15s; }
.navitem:hover { background: var(--surface-2); transform: translateX(2px); }
.navitem.active { background: color-mix(in srgb, var(--brass) 18%, transparent); box-shadow: inset 3px 0 0 var(--brass); font-weight: 700; }
.navitem .q-icon { color: var(--brand-2); }
body.body--dark .navitem .q-icon { color: var(--brass-2); }
.navbadge { background: var(--brass); color: #1B2433; border-radius: 999px; font-size: .72rem; font-weight: 700; padding: 0 .5rem; min-width: 1.4rem; text-align: center; }
.guide-btn { border: 1.5px solid var(--brass) !important; border-radius: 12px !important; color: var(--ink) !important; background: color-mix(in srgb, var(--brass) 10%, transparent); }

/* ---- generic surfaces ---- */
.card { background: var(--surface); border: 1px solid var(--line); border-radius: 20px; box-shadow: var(--shadow); padding: 1.3rem 1.5rem; }
.card-flat { background: var(--surface); border: 1px solid var(--line); border-radius: 16px; padding: 1rem 1.2rem; }
.hero { background: linear-gradient(135deg, var(--brand) 0%, var(--brand-2) 100%); color: #fff; border-radius: 22px; padding: 1.7rem 2rem; position: relative; overflow: hidden; box-shadow: var(--shadow); border-bottom: 4px solid var(--brass); }
.hero h1 { font-family: var(--serif); font-size: 2rem; margin: 0 0 .25rem 0; color: #fff; }
.hero p { margin: 0; color: #D5DCE8; }
.tile { background: var(--surface); border: 1px solid var(--line); border-radius: 16px; padding: .8rem 1.1rem; min-width: 8.5rem; flex: 1; }
.tile .label { color: var(--muted); font-size: .74rem; text-transform: uppercase; letter-spacing: .08em; }
.tile .value { font-family: var(--serif); font-size: 1.9rem; font-weight: 700; line-height: 1.15; }
.tile .sub { color: var(--muted); font-size: .8rem; }
.chip { display: inline-flex; align-items: center; gap: .3rem; padding: .12rem .65rem; border-radius: 999px; font-size: .78rem; border: 1px solid var(--line); background: var(--surface-2); color: var(--muted); }
.pick { cursor: pointer; border: 2px solid var(--line); border-radius: 16px; padding: .65rem 1.05rem; background: var(--surface); transition: all .15s; min-width: 8rem; text-align: center; }
.pick:hover { border-color: var(--brass); transform: translateY(-2px); box-shadow: var(--shadow); }
.pick.on { border-color: var(--brand); background: var(--brand); color: #fff; }
body.body--dark .pick.on { border-color: var(--brass); background: var(--brand-2); }
.pick .n { font-size: .78rem; opacity: .75; }
.listcard { cursor: pointer; border: 2px solid var(--line); border-radius: 18px; padding: .9rem 1.2rem; background: var(--surface); min-width: 12rem; transition: all .15s; }
.listcard:hover { border-color: var(--brass); transform: translateY(-2px); box-shadow: var(--shadow); }
.listcard.on { border-color: var(--room, var(--brand)); box-shadow: 0 0 0 3px color-mix(in srgb, var(--room, var(--brand)) 22%, transparent), var(--shadow); }
.listcard .big { font-family: var(--serif); font-size: 1.9rem; font-weight: 700; color: var(--room, var(--brand)); line-height: 1.1; }
body.body--dark .listcard .big { color: var(--brass-2); }
.roombanner { border-radius: 22px; padding: 1.2rem 1.6rem; color: #fff; background: linear-gradient(130deg, var(--room), color-mix(in srgb, var(--room) 70%, #000)); box-shadow: var(--shadow); border-bottom: 4px solid var(--brass); display: flex; align-items: center; gap: 1.2rem; overflow: hidden; }
.roombanner .art { width: 150px; height: 88px; border-radius: 12px; overflow: hidden; flex: none; border: 2px solid rgba(255,255,255,.55); }
.roombanner h1 { font-family: var(--serif); font-size: 1.9rem; margin: 0; color: #fff; }
.roombanner p { margin: .15rem 0 0 0; color: rgba(255,255,255,.85); }
.stepno { width: 1.9rem; height: 1.9rem; border-radius: 50%; background: var(--brass); color: #1B2433; display: inline-flex; align-items: center; justify-content: center; font-weight: 800; margin-right: .5rem; }

/* ---- the campus map ---- */
.world-wrap { position: relative; width: 100%; height: clamp(420px, 68vh, 680px); border-radius: 22px; overflow: hidden; background: #070B12; border: 1px solid #2A3550;
  box-shadow: 0 24px 60px rgba(8,12,22,.45), inset 0 0 0 1px rgba(201,161,90,.25); transition: opacity .3s, transform .3s; }
.world-wrap.leaving { opacity: 0; transform: scale(1.03); }
.world-wrap canvas { display: block; width: 100%; height: 100%; cursor: pointer; touch-action: none; }
.world-wrap::after { content: ""; position: absolute; inset: 0; pointer-events: none; background: radial-gradient(ellipse at center, transparent 55%, rgba(4,7,14,.7) 100%); }
.world-chip { position: absolute; left: 16px; top: 14px; z-index: 2; display: flex; align-items: center; gap: .55rem; padding: .4rem .9rem .4rem .7rem; border-radius: 999px;
  background: rgba(12,18,30,.72); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,.12); color: #F2EDE0; font-size: .85rem; }
.world-chip i { width: .6rem; height: .6rem; border-radius: 50%; background: var(--room, #6E7FA0); box-shadow: 0 0 10px var(--room, #6E7FA0); }
.world-chip span { opacity: .65; }
.world-keys { position: absolute; right: 16px; top: 14px; z-index: 2; display: flex; gap: .4rem; align-items: center; color: rgba(242,237,224,.78); font-size: .78rem;
  padding: .4rem .8rem; border-radius: 999px; background: rgba(12,18,30,.72); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,.12); }
.world-keys b { font-weight: 700; padding: .05rem .4rem; border-radius: 6px; background: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.18); }
.world-prompt { position: absolute; left: 50%; bottom: 22px; z-index: 3; transform: translate(-50%, 14px); opacity: 0; pointer-events: none; transition: all .22s; cursor: pointer;
  display: flex; align-items: center; gap: .7rem; padding: .55rem 1.1rem .55rem .6rem; border-radius: 999px; border: 1px solid var(--room, #C9A15A); color: #F6F1E4; font-size: 1rem;
  background: rgba(12,18,30,.82); backdrop-filter: blur(12px); box-shadow: 0 10px 30px rgba(0,0,0,.45), 0 0 24px color-mix(in srgb, var(--room, #C9A15A) 45%, transparent); }
.world-prompt.on { opacity: 1; transform: translate(-50%, 0); pointer-events: auto; }
.world-prompt kbd { display: inline-flex; align-items: center; justify-content: center; min-width: 1.9rem; height: 1.9rem; border-radius: 50%; background: var(--room, #C9A15A); color: #0E1420; font-weight: 800; }
.doors { display: flex; flex-wrap: wrap; gap: .6rem; }
.doorchip { display: flex; align-items: center; gap: .55rem; padding: .5rem 1rem .5rem .75rem; border-radius: 999px; background: var(--surface); border: 1px solid var(--line); cursor: pointer;
  box-shadow: var(--shadow); transition: transform .18s, border-color .18s; font-size: .92rem; outline: none; }
.doorchip:hover, .doorchip:focus-visible { transform: translateY(-2px); border-color: var(--room); }
.doorchip i { width: .7rem; height: .7rem; border-radius: 50%; background: var(--room); }
.doorchip .n { color: var(--muted); font-size: .82rem; }
.doorchip.glow { animation: glow 2.2s ease-in-out infinite; }
@keyframes glow { 0%,100% { box-shadow: 0 0 0 0 color-mix(in srgb, var(--room) 60%, transparent); } 50% { box-shadow: 0 0 0 9px color-mix(in srgb, var(--room) 0%, transparent); } }
@media (max-width: 700px) { .world-keys { display: none; } .world-wrap { height: 62vh; } }

/* ---- German words ---- */
.art { font-weight: 700; padding: 0 .1rem; }
.art-der { color: var(--der); } .art-die { color: var(--die); } .art-das { color: var(--das); }
.art-pill { display: inline-block; font-weight: 700; color: #fff; border-radius: 10px; padding: .05rem .6rem; font-size: 1.1rem; }
.art-pill.der { background: var(--der); } .art-pill.die { background: var(--die); } .art-pill.das { background: var(--das); }
.big-word { font-family: var(--serif); font-size: 3.1rem; font-weight: 700; line-height: 1.1; text-align: center; word-break: break-word; }
.mid-word { font-family: var(--serif); font-size: 1.7rem; font-weight: 700; }
.forms { display: grid; grid-template-columns: auto auto; gap: .2rem 1.2rem; font-size: 1.15rem; margin-top: .6rem; }
.forms .k { color: var(--muted); text-align: right; font-size: .85rem; align-self: center; }

/* ---- flip cards ---- */
.flip-scene { perspective: 1500px; width: min(640px, 92vw); height: 360px; margin: .4rem auto; cursor: pointer; user-select: none; }
.flip-card { position: relative; width: 100%; height: 100%; transition: transform .6s cubic-bezier(.2,.8,.2,1); transform-style: preserve-3d; }
.flip-card.flipped { transform: rotateY(180deg); }
.flip-face { position: absolute; inset: 0; backface-visibility: hidden; -webkit-backface-visibility: hidden; border-radius: 28px; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 1.5rem; gap: .4rem; box-shadow: var(--shadow); border: 1px solid var(--line); }
.flip-face.front { background: var(--surface); border-top: 5px solid var(--room, var(--brass)); }
.flip-face.back { background: linear-gradient(160deg, var(--brand), var(--brand-2)); color: #fff; transform: rotateY(180deg); border-top: 5px solid var(--brass); }
.flip-face.back .big-word, .flip-face.back .mid-word { color: #fff; }
.flip-face.back .muted, .flip-face.back .eyebrow { color: #C6D0E0; }
.flip-hint { position: absolute; bottom: .9rem; left: 0; right: 0; text-align: center; font-size: .78rem; color: var(--muted); }
.flip-face.back .flip-hint { color: #C6D0E0; }

/* ---- test ---- */
.prompt-card { background: var(--surface); border: 1px solid var(--line); border-radius: 26px; box-shadow: var(--shadow); padding: 1.6rem 1.5rem; text-align: center; width: 100%; max-width: 780px; border-top: 5px solid var(--room, var(--brass)); }
.eyebrow { color: var(--muted); font-size: .78rem; text-transform: uppercase; letter-spacing: .09em; }
.answer-box { width: min(520px, 100%); }
.answer-box .q-field__native { font-size: 1.35rem; }
.fb { border-radius: 20px; padding: 1.1rem 1.4rem; width: 100%; max-width: 780px; border: 1px solid var(--line); border-left-width: 7px; }
.fb.ok { background: var(--good-bg); border-left-color: var(--good); }
.fb.bad { background: var(--bad-bg); border-left-color: var(--bad); }
.fb .head { font-size: 1.25rem; font-weight: 800; }
.fb .expected { font-family: var(--serif); font-size: 1.9rem; font-weight: 700; margin: .1rem 0; }
.verdict { border-radius: 12px; padding: .35rem .8rem; font-weight: 600; display: inline-block; }
.verdict.in { background: var(--good-bg); color: var(--good); } .verdict.out { background: #F6EBCB; color: #7A5A00; } .verdict.back { background: var(--bad-bg); color: var(--bad); }
.kbd { border: 1px solid var(--line); border-bottom-width: 2px; border-radius: 6px; padding: 0 .4rem; font-size: .78rem; color: var(--muted); background: var(--surface-2); }
.charbtn { min-width: 2.4rem !important; }
.pointsburst { display: inline-block; background: var(--brass); color: #1B2433; border-radius: 999px; padding: .25rem 1rem; font-weight: 800; animation: pop .6s cubic-bezier(.2,1.6,.4,1) both; }
@keyframes pop { from { transform: scale(.4); opacity: 0; } to { transform: scale(1); opacity: 1; } }

/* ---- guide ---- */
.guide-card { width: min(780px, 94vw); max-height: 86vh; border-radius: 24px !important; background: var(--surface) !important; color: var(--ink); }
.guide-step { display: flex; gap: .8rem; align-items: flex-start; padding: .5rem 0; }
.guide-step .no { width: 2rem; height: 2rem; border-radius: 50%; background: var(--brand); color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 800; flex: none; }
.pointrow { display: flex; align-items: center; gap: .9rem; padding: .55rem .9rem; border-radius: 14px; background: var(--surface-2); border: 1px solid var(--line); }
.pointrow .pts { font-family: var(--serif); font-size: 1.5rem; font-weight: 700; color: var(--brass); min-width: 3.6rem; text-align: right; }

/* ---- tables ---- */
.q-table__container { background: var(--surface); border: 1px solid var(--line); border-radius: 16px; box-shadow: none; }
.q-table thead th { color: var(--muted); font-weight: 600; text-transform: uppercase; font-size: .72rem; letter-spacing: .05em; }
.segmented { border: 1px solid var(--line); border-radius: 10px; }
body.body--dark .segmented { background: var(--surface); }
body.body--dark .q-field--outlined .q-field__control { background: var(--surface); }
body.body--dark .pick { color: var(--ink); }
body.body--dark .pick.on { color: #fff; }
@media (max-width: 700px) { .big-word { font-size: 2.2rem; } .flip-scene { height: 320px; } .roombanner .art { display: none; } }
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
    ui.colors(primary="#1B2A41", secondary="#2C3E5C", accent="#B8893A", positive="#2F6B4F", negative="#9E2A3A",
              info="#2F5F9E", warning="#B8893A")
