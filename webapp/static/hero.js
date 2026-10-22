/* The opening page: a small top-view character stands on the START mat. Click a mode button (or press 1-4) and it runs to the
   button, jumps onto it, and the mode starts. Plain canvas over the page's own buttons; without this script the buttons still work. */
(function () {
  "use strict";

  const RUN_SPEED = 760, JUMP_TIME = 0.56, LAND_TIME = 0.22, HOLD = 0.34, SCALE = 1.55;
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const ease = (u) => (u < 0.5 ? 2 * u * u : 1 - Math.pow(-2 * u + 2, 2) / 2);
  const rgb = (hex) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));

  function rrect(c, x, y, w, h, r) {
    r = Math.min(r, w / 2, h / 2);
    c.beginPath(); c.moveTo(x + r, y); c.arcTo(x + w, y, x + w, y + h, r); c.arcTo(x + w, y + h, x, y + h, r);
    c.arcTo(x, y + h, x, y, r); c.arcTo(x, y, x + w, y, r); c.closePath();
  }

  function start() {
    const stage = document.getElementById("hero-stage");
    const canvas = stage && stage.querySelector("canvas");
    if (!canvas || stage.dataset.running) return;
    stage.dataset.running = "1";
    const ctx = canvas.getContext("2d");
    const buttons = Array.from(stage.querySelectorAll(".modebtn"));
    const mat = stage.querySelector(".startmat i");
    const reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    let vw = 0, vh = 0;

    const resize = () => {
      const r = stage.getBoundingClientRect(); vw = r.width; vh = r.height;
      const cw = Math.round(vw * dpr), ch = Math.round(vh * dpr);
      if (canvas.width !== cw || canvas.height !== ch) { canvas.width = cw; canvas.height = ch; }       // resizing clears the canvas
    };
    new ResizeObserver(resize).observe(stage); resize();

    // positions of things, relative to the stage (read every frame so the layout can change freely)
    const centre = (el) => { const r = el.getBoundingClientRect(), s = stage.getBoundingClientRect(); return { x: r.left - s.left + r.width / 2, y: r.top - s.top + r.height / 2 }; };
    const padOf = (btn) => centre(btn.querySelector(".pad"));
    const colorOf = (btn) => getComputedStyle(btn).getPropertyValue("--room").trim() || "#4F8CFF";
    const home = () => centre(mat);

    const me = { x: 0, y: 0, face: -Math.PI / 2, stride: 0, run: false, lift: 0, squash: 0 };
    let job = null, hovered = null, now = 0, last = performance.now(), dustT = 0;
    const dust = [], rings = [], sparks = [];
    const h0 = home(); me.x = h0.x; me.y = h0.y;

    // ---- the run -> jump -> land -> start sequence
    function go(btn) {
      if (job || stage.classList.contains("leaving")) return;
      const url = btn.dataset.url; if (!url) return;
      if (reduced) { window.location.href = url; return; }
      const to = padOf(btn), dx = to.x - me.x, dy = to.y - me.y, dist = Math.hypot(dx, dy) || 1;
      const back = Math.min(120, dist * 0.55), ux = dx / dist, uy = dy / dist;
      const take = { x: to.x - ux * back, y: to.y - uy * back };
      const runLen = Math.hypot(take.x - me.x, take.y - me.y);
      job = { btn, url, to, from: { x: me.x, y: me.y }, take, phase: "run", t: 0, runTime: Math.max(0.3, runLen / RUN_SPEED), color: colorOf(btn) };
      buttons.forEach((b) => b.classList.toggle("target", b === btn));
    }

    function land(j) {
      j.btn.classList.add("pressed");
      rings.push({ x: j.to.x, y: j.to.y, t: 0, color: j.color }, { x: j.to.x, y: j.to.y, t: -0.12, color: j.color });
      for (let i = 0; i < 18; i++) { const a = (i / 18) * 6.283 + Math.random() * 0.3, v = 120 + Math.random() * 160; sparks.push({ x: j.to.x, y: j.to.y, vx: Math.cos(a) * v, vy: Math.sin(a) * v, life: 0.7, color: j.color }); }
    }

    function update(dt) {
      if (!job) {
        const h = home(); me.x += (h.x - me.x) * Math.min(1, dt * 12); me.y += (h.y - me.y) * Math.min(1, dt * 12);       // follows the layout while idle
        const want = hovered ? Math.atan2(padOf(hovered).y - me.y, padOf(hovered).x - me.x) : -Math.PI / 2;
        let d = want - me.face; d = Math.atan2(Math.sin(d), Math.cos(d)); me.face += d * Math.min(1, dt * 8);
        me.run = false; me.lift = 0; return;
      }
      const j = job; j.t += dt;
      if (j.phase === "run") {
        const u = clamp(j.t / j.runTime, 0, 1), e = ease(u);
        me.x = j.from.x + (j.take.x - j.from.x) * e; me.y = j.from.y + (j.take.y - j.from.y) * e;
        me.face = Math.atan2(j.to.y - me.y, j.to.x - me.x); me.run = u < 1; me.stride += dt * 22; me.lift = 0;
        dustT += dt; if (dustT > 0.035 && u < 1) { dustT = 0; dust.push({ x: me.x, y: me.y + 6, life: 0.45, r: 5 + Math.random() * 4 }); }
        if (u >= 1) { j.phase = "jump"; j.t = 0; j.from = { x: me.x, y: me.y }; }
      } else if (j.phase === "jump") {
        const u = clamp(j.t / JUMP_TIME, 0, 1), e = 1 - Math.pow(1 - u, 2);
        me.x = j.from.x + (j.to.x - j.from.x) * e; me.y = j.from.y + (j.to.y - j.from.y) * e;
        me.lift = Math.sin(Math.PI * u); me.run = false; me.stride += dt * 8;
        if (u >= 1) { j.phase = "land"; j.t = 0; me.lift = 0; land(j); }
      } else if (j.phase === "land") {
        const u = clamp(j.t / LAND_TIME, 0, 1); me.squash = Math.sin(Math.PI * u); me.x = j.to.x; me.y = j.to.y;
        if (u >= 1) { j.phase = "hold"; j.t = 0; me.squash = 0; }
      } else if (j.phase === "hold") {
        if (j.t >= HOLD) { j.phase = "leave"; j.t = 0; stage.classList.add("leaving"); }
      } else if (j.phase === "leave") {
        if (j.t >= 0.3) { window.location.href = j.url; job = { phase: "gone", t: 0 }; }
      }
    }

    // ---- drawing
    function drawPerson() {
      const sw = me.run ? Math.sin(me.stride) : Math.sin(now * 2) * 0.12, grow = 1 + 0.5 * me.lift - 0.1 * me.squash, breathe = 1 + 0.012 * Math.sin(now * 2.4);
      const s = SCALE * grow * breathe;
      ctx.save(); ctx.translate(me.x, me.y - me.lift * 46);
      ctx.fillStyle = "rgba(0,0,0," + (0.42 - 0.2 * me.lift) + ")";                                  // the shadow stays on the floor while the body rises
      ctx.beginPath(); ctx.ellipse(2, 8 + me.lift * 46 * 0.6, 17 * SCALE * (1 - 0.25 * me.lift), 12 * SCALE * (1 - 0.25 * me.lift), 0, 0, 7); ctx.fill();
      ctx.rotate(me.face + Math.PI / 2); ctx.scale(s, s * (1 + 0.08 * me.squash));
      ctx.fillStyle = "#E7C6A0";                                                                      // hands swing with the stride (or reach up in the jump)
      const reach = me.lift * 7;
      ctx.beginPath(); ctx.arc(-17, -sw * 7 - reach, 4.6, 0, 7); ctx.fill(); ctx.beginPath(); ctx.arc(17, sw * 7 - reach, 4.6, 0, 7); ctx.fill();
      const body = ctx.createLinearGradient(-16, 0, 16, 0); body.addColorStop(0, "#1D3B8B"); body.addColorStop(0.5, "#3B7BFF"); body.addColorStop(1, "#1D3B8B");
      ctx.fillStyle = body; rrect(ctx, -16, -9, 32, 19, 9); ctx.fill();
      ctx.fillStyle = "#8DB6FF"; ctx.fillRect(-2, -9, 4, 19);
      ctx.fillStyle = "#1B1B26"; ctx.beginPath(); ctx.arc(0, 0, 10.5, 0, 7); ctx.fill();                // hair
      ctx.fillStyle = "#EBCBA6"; ctx.beginPath(); ctx.arc(0, -2.4, 9, 0, 7); ctx.fill();
      ctx.fillStyle = "#1B1B26"; ctx.beginPath(); ctx.arc(0, 2.4, 9, 0, 3.2); ctx.fill();
      ctx.restore();
    }

    function frame(t) {
      requestAnimationFrame(frame);
      const dt = Math.min(0.05, Math.max(0, (t - last) / 1000)); last = t; now = t / 1000;
      if (document.hidden) return;
      update(dt);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.clearRect(0, 0, vw, vh);
      for (let i = dust.length - 1; i >= 0; i--) {
        const p = dust[i]; p.life -= dt; if (p.life <= 0) { dust.splice(i, 1); continue; }
        ctx.fillStyle = "rgba(160,190,255," + (p.life * 0.35) + ")"; ctx.beginPath(); ctx.arc(p.x, p.y, p.r * (1.4 - p.life), 0, 7); ctx.fill();
      }
      for (let i = rings.length - 1; i >= 0; i--) {
        const r = rings[i]; r.t += dt; if (r.t < 0) continue; if (r.t > 0.7) { rings.splice(i, 1); continue; }
        const [cr, cg, cb] = rgb(r.color.startsWith("#") ? r.color : "#4F8CFF"), u = r.t / 0.7;
        ctx.strokeStyle = "rgba(" + cr + "," + cg + "," + cb + "," + (1 - u) + ")"; ctx.lineWidth = 4 * (1 - u) + 1; ctx.beginPath(); ctx.arc(r.x, r.y, 46 + u * 90, 0, 7); ctx.stroke();
      }
      for (let i = sparks.length - 1; i >= 0; i--) {
        const p = sparks[i]; p.life -= dt; if (p.life <= 0) { sparks.splice(i, 1); continue; }
        p.x += p.vx * dt; p.y += p.vy * dt; p.vx *= 0.94; p.vy *= 0.94;
        const c = rgb(p.color.startsWith("#") ? p.color : "#4F8CFF"); ctx.fillStyle = "rgba(" + c[0] + "," + c[1] + "," + c[2] + "," + p.life + ")"; ctx.beginPath(); ctx.arc(p.x, p.y, 2.6 * p.life + 1, 0, 7); ctx.fill();
      }
      drawPerson();
    }
    requestAnimationFrame(frame);

    // ---- input: the capture handler runs before the page's own click handler, which is only the fallback
    const pick = (el) => el && el.closest && el.closest(".modebtn");
    stage.addEventListener("click", (e) => { const b = pick(e.target); if (b) { e.stopPropagation(); e.preventDefault(); go(b); } }, true);
    stage.addEventListener("keydown", (e) => { const b = pick(e.target); if (b && (e.key === "Enter" || e.key === " ")) { e.stopPropagation(); e.preventDefault(); go(b); } }, true);
    stage.addEventListener("pointerover", (e) => { hovered = pick(e.target) || hovered; });
    stage.addEventListener("pointerout", (e) => { if (pick(e.target) === hovered && !pick(e.relatedTarget)) hovered = null; });
    buttons.forEach((b) => { b.addEventListener("focus", () => { hovered = b; }); b.addEventListener("blur", () => { if (hovered === b) hovered = null; }); });
    window.addEventListener("keydown", (e) => {
      if (e.ctrlKey || e.metaKey || e.altKey || /^(input|textarea|select)$/i.test((document.activeElement || {}).tagName || "")) return;
      const n = parseInt(e.key, 10); if (n >= 1 && n <= buttons.length) go(buttons[n - 1]);
    });
    window.addEventListener("pageshow", (e) => { if (e.persisted) window.location.reload(); });          // coming back with the browser's back button
    window.__wortschatzHero = { go: (key) => { const b = buttons.find((x) => x.dataset.key === key); if (b) go(b); }, state: () => ({ phase: job && job.phase, x: me.x, y: me.y }) };
  }

  // NiceGUI builds the page after this file loads, so wait for the stage to appear.
  (function wait(tries) {
    if (document.getElementById("hero-stage") && document.querySelector("#hero-stage canvas")) return start();
    if (tries < 200) setTimeout(() => wait(tries + 1), 50);
  })(0);
})();
