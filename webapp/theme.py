"""Design system: black and deep navy with an electric-blue accent, one dark theme, and the CSS for every component."""
from __future__ import annotations

from nicegui import ui

# Article colours follow the convention many German courses use: der blue, die red, das green (bright, to read on dark).
ARTICLE_COLORS = {"der": "#6EA8FF", "die": "#FF7A93", "das": "#4ADE9A"}

CSS = """
:root {
  --bg: #05080F; --bg-2: #080D18; --surface: #0D1526; --surface-2: #101B31; --ink: #E8EEF9; --muted: #8C9BB5; --line: #1C2944;
  --brand: #070C18; --accent: #4F8CFF; --accent-2: #8DB6FF;
  --der: #6EA8FF; --die: #FF7A93; --das: #4ADE9A; --good: #34D399; --good-bg: #0E2B24; --bad: #FB7185; --bad-bg: #351622;
  --learn: #4F8CFF; --second: #FF8A5B; --test: #2DD4A8; --stay: #F5B94C;
  --shadow: 0 1px 2px rgba(0,0,0,.5), 0 14px 34px rgba(0,0,0,.45);
  --title: #FFFFFF; --warn: #F6D590; --panel: #0A1020;
  --tile-bg: linear-gradient(180deg, rgba(255,255,255,.055), rgba(255,255,255,.012)); --tile-line: rgba(255,255,255,.09);
  --stage-bg: radial-gradient(900px 380px at 50% -8%, rgba(79,140,255,.20), transparent 65%), radial-gradient(700px 320px at 50% 112%, rgba(45,212,168,.10), transparent 65%), linear-gradient(180deg, #0A1226, #060A14);
  --grid: rgba(120,160,255,.07); --mat-line: rgba(255,255,255,.16);
  --display: "Inter", "Segoe UI Variable Display", "Segoe UI", system-ui, -apple-system, Roboto, "Helvetica Neue", Arial, sans-serif;
}
body.body--light {
  --bg: #EDF2FA; --bg-2: #E4ECF8; --surface: #FFFFFF; --surface-2: #F3F7FD; --ink: #0B1426; --muted: #5A6B88; --line: #D3DEEE;
  --accent: #2F6BFF; --accent-2: #2457D6;
  --der: #1F5FD1; --die: #D1294F; --das: #0E8F63; --good: #0E8F63; --good-bg: #DDF5EA; --bad: #D6304A; --bad-bg: #FDE4E8;
  --learn: #2F6BFF; --test: #0E9F7E; --second: #E5602B; --stay: #C98A0B;
  --shadow: 0 1px 2px rgba(20,40,90,.06), 0 12px 30px rgba(20,40,90,.10);
  --title: #0B1426; --warn: #7A5200; --panel: #FFFFFF;
  --tile-bg: linear-gradient(180deg, #FFFFFF, #F1F5FD); --tile-line: #D3DEEE;
  --stage-bg: radial-gradient(900px 380px at 50% -8%, rgba(47,107,255,.14), transparent 65%), radial-gradient(700px 320px at 50% 112%, rgba(14,159,126,.10), transparent 65%), linear-gradient(180deg, #F8FAFF, #E8EFFB);
  --grid: rgba(47,107,255,.08); --mat-line: rgba(11,20,38,.22);
}
body { background: var(--bg) !important; color: var(--ink); font-feature-settings: "tnum"; font-family: var(--display); }
.q-page-container, .q-layout, .q-page { background: var(--bg); }
.serif { font-family: var(--display); letter-spacing: -.02em; }
.muted { color: var(--muted); }
.page { width: min(1180px, 94%); margin: 0 auto; padding: 1.4rem 0 3rem 0; gap: 1.1rem; }
h1, h2, h3 { letter-spacing: -.02em; }

/* ---- header ---- */
.app-header { background: rgba(7,12,24,.92) !important; backdrop-filter: blur(12px); border-bottom: 1px solid var(--line); padding: 0 1rem; height: 58px; }
.app-header::after { content: ""; position: absolute; left: 0; right: 0; bottom: -1px; height: 1px; background: linear-gradient(90deg, transparent, var(--accent), transparent); opacity: .7; }
.app-header .brand { font-size: 1.3rem; font-weight: 800; letter-spacing: -.02em; background: linear-gradient(90deg, #8DB6FF, #fff 55%); -webkit-background-clip: text; background-clip: text; color: transparent; }
.chip-level { background: rgba(79,140,255,.14); border: 1px solid rgba(79,140,255,.45); color: #8DB6FF; border-radius: 999px; padding: .2rem .8rem; font-size: .85rem; font-weight: 600; white-space: nowrap; }
.navlink { color: var(--muted) !important; font-size: .9rem; text-decoration: none; padding: .3rem .7rem; border-radius: 999px; transition: all .15s; }
.navlink:hover { color: var(--ink) !important; background: color-mix(in srgb, var(--accent) 12%, transparent); }
.app-header .navlink, .app-header .q-btn { color: #B4C3DD !important; }
.app-header .navlink:hover, .app-header .q-btn:hover { color: #fff !important; background: rgba(255,255,255,.08); }
.app-header .segmented { background: #0D1526; border-color: #1C2944; }
.app-header .segmented .q-btn { color: #B4C3DD !important; }
.app-header .segmented .q-btn.bg-primary { color: #fff !important; background: #3B7BFF !important; }
.demo-banner { background: rgba(245,185,76,.12); border-color: rgba(245,185,76,.4) !important; color: var(--warn); }

/* ---- generic surfaces ---- */
.card { background: var(--surface); border: 1px solid var(--line); border-radius: 20px; box-shadow: var(--shadow); padding: 1.3rem 1.5rem; }
.card-flat { background: var(--surface); border: 1px solid var(--line); border-radius: 16px; padding: 1rem 1.2rem; }
.hero { background: linear-gradient(135deg, #0F2150 0%, #0A1330 100%); color: #fff; border-radius: 22px; padding: 1.7rem 2rem; position: relative; overflow: hidden; box-shadow: var(--shadow); border: 1px solid rgba(79,140,255,.35); }
.hero h1 { font-size: 2rem; font-weight: 800; margin: 0 0 .25rem 0; color: #fff; }
.hero p { margin: 0; color: #C5D3EC; }
.tile { background: var(--surface); border: 1px solid var(--line); border-radius: 16px; padding: .8rem 1.1rem; min-width: 8.5rem; flex: 1; }
.tile .label { color: var(--muted); font-size: .74rem; text-transform: uppercase; letter-spacing: .08em; }
.tile .value { font-size: 1.9rem; font-weight: 800; line-height: 1.15; letter-spacing: -.02em; }
.tile .sub { color: var(--muted); font-size: .8rem; }
.chip { display: inline-flex; align-items: center; gap: .3rem; padding: .12rem .65rem; border-radius: 999px; font-size: .78rem; border: 1px solid var(--line); background: var(--surface-2); color: var(--muted); }
.pick { cursor: pointer; border: 2px solid var(--line); border-radius: 16px; padding: .65rem 1.05rem; background: var(--surface); transition: all .15s; min-width: 8rem; text-align: center; color: var(--ink); }
.pick:hover { border-color: var(--accent); transform: translateY(-2px); box-shadow: var(--shadow); }
.pick.on { border-color: var(--accent); background: color-mix(in srgb, var(--accent) 24%, var(--surface)); color: var(--ink); }
.pick .n { font-size: .78rem; opacity: .75; }
.listcard { cursor: pointer; border: 2px solid var(--line); border-radius: 18px; padding: .9rem 1.2rem; background: var(--surface); min-width: 12rem; transition: all .15s; }
.listcard:hover { border-color: var(--room, var(--accent)); transform: translateY(-2px); box-shadow: var(--shadow); }
.listcard.on { border-color: var(--room, var(--accent)); box-shadow: 0 0 0 3px color-mix(in srgb, var(--room, var(--accent)) 25%, transparent), var(--shadow); }
.listcard .big { font-size: 1.9rem; font-weight: 800; color: var(--room, var(--accent)); line-height: 1.1; }
.roombanner { border-radius: 22px; padding: 1.3rem 1.7rem; color: #fff; background: linear-gradient(130deg, color-mix(in srgb, var(--room) 38%, #0A1226), #0A1226 75%); box-shadow: var(--shadow); border: 1px solid color-mix(in srgb, var(--room) 45%, transparent);
  display: flex; align-items: center; gap: 1.2rem; overflow: hidden; position: relative; }
.roombanner::before { content: ""; position: absolute; left: 0; right: 0; top: 0; height: 3px; background: var(--room); box-shadow: 0 0 20px var(--room); }
.roombanner .art { width: 64px; height: 64px; border-radius: 50%; flex: none; display: flex; align-items: center; justify-content: center; color: var(--room);
  border: 2px solid var(--room); background: radial-gradient(circle, color-mix(in srgb, var(--room) 25%, #0A1226), #0A1226 75%); box-shadow: 0 0 28px color-mix(in srgb, var(--room) 40%, transparent); }
.roombanner .art svg { width: 32px; height: 32px; }
.roombanner h1 { font-size: 1.9rem; margin: 0; color: #fff; font-weight: 800; }
.roombanner p { margin: .15rem 0 0 0; color: rgba(255,255,255,.78); }
.stepno { width: 1.9rem; height: 1.9rem; border-radius: 50%; background: var(--accent); color: #fff; display: inline-flex; align-items: center; justify-content: center; font-weight: 800; margin-right: .5rem; }

/* ---- opening page: four mode buttons and the character that runs to them ---- */
.opening { text-align: center; padding: .6rem 0 0 0; }
.opening h1 { font-size: clamp(1.8rem, 6.4vw, 3.4rem); font-weight: 800; margin: 0; letter-spacing: -.04em; color: var(--title); }
.opening h1 b { white-space: nowrap; background: linear-gradient(90deg, #8DB6FF, #4F8CFF 50%, #2DD4A8); -webkit-background-clip: text; background-clip: text; color: transparent; }
.opening p { margin: .35rem 0 0 0; color: var(--muted); font-size: 1.05rem; }
.stage { position: relative; width: 100%; border-radius: 30px; overflow: hidden; padding: 2rem 1.6rem 0 1.6rem; border: 1px solid var(--line);
  background: var(--stage-bg); box-shadow: var(--shadow); transition: opacity .3s, transform .3s; }
.stage::before { content: ""; position: absolute; inset: 0; pointer-events: none; background-image: linear-gradient(var(--grid) 1px, transparent 1px), linear-gradient(90deg, var(--grid) 1px, transparent 1px);
  background-size: 44px 44px; -webkit-mask-image: radial-gradient(ellipse at 50% 55%, #000 35%, transparent 80%); mask-image: radial-gradient(ellipse at 50% 55%, #000 35%, transparent 80%); }
.stage.leaving { opacity: 0; transform: scale(1.015); }
.stage canvas { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; z-index: 5; }
.modes { position: relative; z-index: 2; display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.1rem; }
.modebtn { position: relative; cursor: pointer; border-radius: 24px; padding: 1.15rem 1rem 1.2rem; text-align: center; outline: none; overflow: hidden;
  background: var(--tile-bg); border: 1px solid var(--tile-line); backdrop-filter: blur(6px);
  transition: transform .28s cubic-bezier(.2,.8,.2,1), box-shadow .28s, border-color .28s; animation: rise .7s both; }
.modebtn:nth-child(2) { animation-delay: .07s; } .modebtn:nth-child(3) { animation-delay: .14s; } .modebtn:nth-child(4) { animation-delay: .21s; }
@keyframes rise { from { opacity: 0; transform: translateY(18px); } to { opacity: 1; transform: none; } }
.modebtn::before { content: ""; position: absolute; left: 14%; right: 14%; top: 0; height: 3px; border-radius: 0 0 4px 4px; background: var(--room); box-shadow: 0 0 22px var(--room); }
.modebtn:hover, .modebtn:focus-visible, .modebtn.target { transform: translateY(-7px); border-color: color-mix(in srgb, var(--room) 65%, transparent);
  box-shadow: var(--shadow), 0 0 46px color-mix(in srgb, var(--room) 26%, transparent); }
.modebtn .pad { position: relative; width: 96px; height: 96px; margin: .9rem auto 1rem; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: var(--room);
  border: 2px solid var(--room); background: radial-gradient(circle, color-mix(in srgb, var(--room) 24%, var(--panel)), var(--panel) 72%);
  box-shadow: 0 0 0 9px color-mix(in srgb, var(--room) 9%, transparent), 0 0 34px color-mix(in srgb, var(--room) 32%, transparent); transition: box-shadow .3s; }
.modebtn .pad::after { content: ""; position: absolute; inset: -14px; border-radius: 50%; border: 1px dashed color-mix(in srgb, var(--room) 55%, transparent); animation: spin 18s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.modebtn .pad svg { width: 42px; height: 42px; }
.modebtn .t { font-size: 1.3rem; font-weight: 800; color: var(--title); letter-spacing: -.02em; }
.modebtn .s { color: var(--muted); font-size: .9rem; margin-top: .15rem; }
.modebtn .badge { position: absolute; top: 14px; right: 14px; background: color-mix(in srgb, var(--room) 18%, var(--panel)); color: var(--room); border: 1px solid color-mix(in srgb, var(--room) 50%, transparent);
  border-radius: 999px; padding: .12rem .65rem; font-size: .78rem; font-weight: 700; }
.modebtn.glow .badge { animation: pulse 2s ease-in-out infinite; }
@keyframes pulse { 0%,100% { box-shadow: 0 0 0 0 color-mix(in srgb, var(--room) 60%, transparent); } 50% { box-shadow: 0 0 0 8px color-mix(in srgb, var(--room) 0%, transparent); } }
.modebtn .key { position: absolute; top: 14px; left: 14px; font-size: .72rem; color: var(--muted); border: 1px solid var(--tile-line); border-radius: 6px; padding: 0 .4rem; background: var(--surface-2); }
.modebtn.pressed { transform: translateY(2px) scale(.975); border-color: var(--room); }
.modebtn.pressed .pad { box-shadow: 0 0 0 16px color-mix(in srgb, var(--room) 26%, transparent), 0 0 70px var(--room); }
.startmat { position: relative; z-index: 1; height: 168px; display: flex; align-items: center; justify-content: center; }
.startmat i { display: block; width: 98px; height: 98px; border-radius: 50%; border: 2px dashed var(--mat-line); background: radial-gradient(circle, color-mix(in srgb, var(--accent) 8%, transparent), transparent 70%); }
.startmat span { position: absolute; bottom: 1.1rem; font-size: .68rem; letter-spacing: .32em; color: var(--muted); opacity: .7; }
.quicklinks { display: flex; flex-wrap: wrap; gap: .6rem; justify-content: center; align-items: center; }
.quicklinks .navlink { border: 1px solid var(--line); background: var(--surface); }
.sectionhead { display: flex; align-items: baseline; gap: .8rem; margin-top: 1.4rem; }
.sectionhead h2 { margin: 0; font-size: 1.7rem; font-weight: 800; }
.guidegrid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.1rem; width: 100%; align-items: start; }
@media (max-width: 1000px) { .modes { grid-template-columns: repeat(2, 1fr); } .guidegrid { grid-template-columns: 1fr; } }
@media (max-width: 520px) { .modes { gap: .7rem; } .modebtn .pad { width: 76px; height: 76px; } .modebtn .pad svg { width: 34px; height: 34px; } .modebtn .t { font-size: 1.05rem; } .modebtn .s { font-size: .78rem; } .stage { padding: 1.2rem .8rem 0 .8rem; } .modebtn .key { display: none; } }
@media (max-width: 560px) { .app-header .navlink { display: none; } .app-header { padding: 0 .6rem; } }
@media (prefers-reduced-motion: reduce) { .modebtn, .modebtn .pad::after { animation: none; } }

/* ---- German words ---- */
.art { font-weight: 700; padding: 0 .1rem; }
.art-der { color: var(--der); } .art-die { color: var(--die); } .art-das { color: var(--das); }
.art-pill { display: inline-block; font-weight: 700; color: #06101F; border-radius: 10px; padding: .05rem .6rem; font-size: 1.1rem; }
.art-pill.der { background: var(--der); } .art-pill.die { background: var(--die); } .art-pill.das { background: var(--das); }
.big-word { font-size: 3.1rem; font-weight: 800; line-height: 1.1; text-align: center; word-break: break-word; letter-spacing: -.03em; }
.mid-word { font-size: 1.7rem; font-weight: 800; letter-spacing: -.02em; }
.forms { display: grid; grid-template-columns: auto auto; gap: .2rem 1.2rem; font-size: 1.15rem; margin-top: .6rem; }
.forms .k { color: var(--muted); text-align: right; font-size: .85rem; align-self: center; }

/* ---- flip cards ---- */
.flip-scene { perspective: 1500px; width: min(640px, 92vw); height: 360px; margin: .4rem auto; cursor: pointer; user-select: none; }
.flip-card { position: relative; width: 100%; height: 100%; transition: transform .6s cubic-bezier(.2,.8,.2,1); transform-style: preserve-3d; }
.flip-card.flipped { transform: rotateY(180deg); }
.flip-face { position: absolute; inset: 0; backface-visibility: hidden; -webkit-backface-visibility: hidden; border-radius: 28px; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 1.5rem; gap: .4rem; box-shadow: var(--shadow); border: 1px solid var(--line); }
.flip-face.front { background: linear-gradient(180deg, var(--surface-2), var(--surface)); border-top: 4px solid var(--room, var(--accent)); }
.flip-face.back { background: linear-gradient(160deg, #12306B, #0A1B3F); color: #fff; transform: rotateY(180deg); border-top: 4px solid var(--accent-2); }
.flip-face.back .big-word, .flip-face.back .mid-word { color: #fff; }
.flip-face.back .muted, .flip-face.back .eyebrow { color: #B7C7E6; }
.flip-hint { position: absolute; bottom: .9rem; left: 0; right: 0; text-align: center; font-size: .78rem; color: var(--muted); }
.flip-face.back .flip-hint { color: #B7C7E6; }

/* ---- test ---- */
.prompt-card { background: var(--surface); border: 1px solid var(--line); border-radius: 26px; box-shadow: var(--shadow); padding: 1.6rem 1.5rem; text-align: center; width: 100%; max-width: 780px; border-top: 4px solid var(--room, var(--accent)); }
.eyebrow { color: var(--muted); font-size: .78rem; text-transform: uppercase; letter-spacing: .09em; }
.answer-box { width: min(520px, 100%); }
.answer-box .q-field__native { font-size: 1.35rem; }
.fb { border-radius: 20px; padding: 1.1rem 1.4rem; width: 100%; max-width: 780px; border: 1px solid var(--line); border-left-width: 7px; }
.fb.ok { background: var(--good-bg); border-left-color: var(--good); }
.fb.bad { background: var(--bad-bg); border-left-color: var(--bad); }
.fb .head { font-size: 1.25rem; font-weight: 800; }
.fb .expected { font-size: 1.9rem; font-weight: 800; margin: .1rem 0; letter-spacing: -.02em; }
.verdict { border-radius: 12px; padding: .35rem .8rem; font-weight: 600; display: inline-block; }
.verdict.in { background: var(--good-bg); color: var(--good); } .verdict.out { background: rgba(245,185,76,.16); color: var(--warn); } .verdict.back { background: var(--bad-bg); color: var(--bad); }
.kbd { border: 1px solid var(--line); border-bottom-width: 2px; border-radius: 6px; padding: 0 .4rem; font-size: .78rem; color: var(--muted); background: var(--surface-2); }
.charbtn { min-width: 2.4rem !important; }
.pointsburst { display: inline-block; background: linear-gradient(90deg, #4F8CFF, #2DD4A8); color: #04101F; border-radius: 999px; padding: .25rem 1rem; font-weight: 800; animation: pop .6s cubic-bezier(.2,1.6,.4,1) both; }
@keyframes pop { from { transform: scale(.4); opacity: 0; } to { transform: scale(1); opacity: 1; } }

/* ---- guide ---- */
.guide-card { width: min(820px, 94vw); max-height: 88vh; border-radius: 24px !important; background: var(--surface) !important; color: var(--ink); border: 1px solid var(--line); }
.guide-step { display: flex; gap: .8rem; align-items: flex-start; padding: .5rem 0; }
.guide-step .no { width: 2rem; height: 2rem; border-radius: 50%; color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 800; flex: none; }
.pointrow { display: flex; align-items: center; gap: .9rem; padding: .55rem .9rem; border-radius: 14px; background: var(--surface-2); border: 1px solid var(--line); }
.pointrow .pts { font-size: 1.5rem; font-weight: 800; color: var(--accent-2); min-width: 3.6rem; text-align: right; }

/* ---- tables and inputs ---- */
.headerline { font-family: ui-monospace, "Cascadia Code", Consolas, monospace; font-size: .92rem; padding: .6rem .9rem; border-radius: 12px; background: var(--surface-2); border: 1px solid var(--line); overflow-x: auto; white-space: nowrap; }
.mono { font-family: ui-monospace, "Cascadia Code", Consolas, monospace; }
.req { color: var(--bad); font-weight: 700; } .opt { color: var(--muted); }
.q-table__container { background: var(--surface); border: 1px solid var(--line); border-radius: 16px; box-shadow: none; }
.q-table thead th { color: var(--muted); font-weight: 600; text-transform: uppercase; font-size: .72rem; letter-spacing: .05em; }
.segmented { border: 1px solid var(--line); border-radius: 10px; background: var(--surface); }
.q-field--outlined .q-field__control { background: var(--surface); }
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
    ui.colors(primary="#3B7BFF", secondary="#1C2944", accent="#4F8CFF", positive="#34D399", negative="#E0314B",
              info="#6EA8FF", warning="#F5B94C")
