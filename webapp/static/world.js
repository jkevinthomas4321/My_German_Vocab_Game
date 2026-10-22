/* The Wortschatz campus: a top-down map you walk around. Six rooms off one corridor; step on a glowing pad to enter.
   Plain canvas, no libraries. Settings arrive in window.WORTSCHATZ_WORLD (see webapp/pages/home.py). */
(function () {
  "use strict";

  const T = 48, COLS = 34, ROWS = 22, W = COLS * T, H = ROWS * T;
  const SPEED = 235, RADIUS = 13, REACH = 58;

  // rect = [x, y, w, h] in tiles
  const ROOMS = {
    learn:   { name: "Learn room",         color: "#5B8DBF", rect: [1, 1, 11, 7] },
    guide:   { name: "Info hall",          color: "#C9AE74", rect: [13, 1, 8, 7] },
    test:    { name: "Test room",          color: "#44A08A", rect: [22, 1, 11, 7] },
    second:  { name: "Second-chance room", color: "#CC7456", rect: [1, 14, 11, 7] },
    library: { name: "Word library",       color: "#8197B0", rect: [13, 14, 8, 7] },
    diary:   { name: "Diary",              color: "#D1A24C", rect: [22, 14, 11, 7] },
  };
  const CORRIDOR = { name: "Corridor", color: "#6E7FA0", rect: [1, 9, 32, 4] };
  const DOORS = [[5, 8], [16, 8], [27, 8], [5, 13], [16, 13], [27, 13]];       // top-left tile of each 2-wide doorway

  // pad: where you stand to enter. (x, y) are in tiles, so 6, 4.5 is the middle of the doorway column.
  const STATIONS = [
    { key: "learn",    room: "learn",   x: 6,  y: 4.5, label: "Start learning",       url: "/learn" },
    { key: "test",     room: "test",    x: 28, y: 4.5, label: "Start a revision test", url: "/test" },
    { key: "second",   room: "second",  x: 6,  y: 17.5, label: "Retry missed words",   url: "/second-chance" },
    { key: "diary",    room: "diary",   x: 28, y: 17.5, label: "Open my diary",        url: "/diary" },
    { key: "guide",    room: "guide",   x: 15, y: 3.6, label: "Read the guide",        action: "guide" },
    { key: "progress", room: "guide",   x: 19, y: 3.6, label: "See my progress",       url: "/stats" },
    { key: "library",  room: "library", x: 17, y: 17.5, label: "Manage word lists",    url: "/words" },
  ];

  // props: [type, x, y, w, h] in tiles; all solid
  const PROPS = [
    ["shelf", 2, 1, 4, 1], ["shelf", 7, 1, 4, 1], ["shelf", 1, 3, 1, 3], ["desk", 2, 6, 3, 1], ["desk", 8, 6, 3, 1], ["plant", 11, 1, 1, 1], ["plant", 1, 1, 1, 1],
    ["board", 24, 1, 7, 1], ["examdesk", 23, 3, 2, 1], ["examdesk", 23, 5, 2, 1], ["examdesk", 31, 3, 2, 1], ["examdesk", 31, 5, 2, 1], ["plant", 22, 1, 1, 1],
    ["sofa", 2, 19, 4, 1], ["shelf", 8, 14, 3, 1], ["table", 9, 18, 2, 1], ["plant", 1, 14, 1, 1], ["plant", 11, 20, 1, 1],
    ["bed", 23, 15, 3, 2], ["locker", 30, 14, 3, 1], ["desk", 30, 19, 3, 1], ["plant", 22, 20, 1, 1],
    ["terminal", 14, 1, 2, 1], ["terminal", 18, 1, 2, 1], ["holo", 16, 4, 2, 1], ["plant", 13, 7, 1, 1], ["plant", 20, 7, 1, 1],
    ["shelf", 13, 15, 1, 5], ["shelf", 20, 15, 1, 5], ["crate", 14, 19, 1, 1], ["crate", 15, 19, 1, 1], ["crate", 19, 19, 1, 1],
  ];

  const PALETTE = { ink: "#E9E4D6", brass: "#C9A15A", navy: "#0F1623" };
  const BOOKS = ["#7B2D3B", "#35506B", "#2F5D50", "#B8893A", "#5A3E6B", "#8A5A3C", "#3B6D78", "#A4553D"];

  // ---------------------------------------------------------------- small helpers
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const rgb = (hex) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));
  const mix = (a, b, t) => { const x = rgb(a), y = rgb(b); return "rgb(" + x.map((v, i) => Math.round(v + (y[i] - v) * t)).join(",") + ")"; };
  const alpha = (hex, a) => "rgba(" + rgb(hex).join(",") + "," + a + ")";
  function rrect(c, x, y, w, h, r) {
    r = Math.min(r, w / 2, h / 2);
    c.beginPath(); c.moveTo(x + r, y); c.arcTo(x + w, y, x + w, y + h, r); c.arcTo(x + w, y + h, x, y + h, r);
    c.arcTo(x, y + h, x, y, r); c.arcTo(x, y, x + w, y, r); c.closePath();
  }
  function seeded(n) { let s = n * 9301 + 49297; return () => { s = (s * 9301 + 49297) % 233280; return s / 233280; }; }

  // ---------------------------------------------------------------- the map
  const floor = Array.from({ length: ROWS }, () => Array(COLS).fill(null));         // room key, "corridor", "door" or null
  const solid = Array.from({ length: ROWS }, () => Array(COLS).fill(false));
  const fill = (rect, tag) => { for (let y = rect[1]; y < rect[1] + rect[3]; y++) for (let x = rect[0]; x < rect[0] + rect[2]; x++) floor[y][x] = tag; };
  Object.entries(ROOMS).forEach(([k, r]) => fill(r.rect, k));
  fill(CORRIDOR.rect, "corridor");
  DOORS.forEach(([x, y]) => { floor[y][x] = "door"; floor[y][x + 1] = "door"; });
  PROPS.forEach(([, x, y, w, h]) => { for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) solid[y + j][x + i] = true; });
  const isFloor = (x, y) => x >= 0 && y >= 0 && x < COLS && y < ROWS && floor[y][x] !== null;
  const blocked = (x, y) => !isFloor(x, y) || solid[y][x];
  const roomAt = (px, py) => {
    const tag = (isFloor(Math.floor(px / T), Math.floor(py / T)) && floor[Math.floor(py / T)][Math.floor(px / T)]) || null;
    return tag === "corridor" || tag === "door" ? CORRIDOR : ROOMS[tag] || null;
  };

  // ---------------------------------------------------------------- the static layer: floors, walls, props, painted names
  function buildStatic(scale) {
    const cv = document.createElement("canvas"); cv.width = W * scale; cv.height = H * scale;
    const c = cv.getContext("2d"); c.scale(scale, scale);
    c.fillStyle = "#070B12"; c.fillRect(0, 0, W, H);

    // floors
    for (let y = 0; y < ROWS; y++) for (let x = 0; x < COLS; x++) {
      const tag = floor[y][x]; if (!tag) continue;
      const base = tag === "corridor" || tag === "door" ? "#1B2332" : mix(ROOMS[tag].color, "#151C2A", 0.9);
      c.fillStyle = (x + y) % 2 ? base : mix(base, "#FFFFFF", 0.035); c.fillRect(x * T, y * T, T, T);
      c.strokeStyle = "rgba(255,255,255,.045)"; c.lineWidth = 1; c.strokeRect(x * T + .5, y * T + .5, T - 1, T - 1);
      if (tag === "corridor") {                                                                   // grated metal
        c.strokeStyle = "rgba(255,255,255,.05)"; c.beginPath();
        for (let i = 6; i < T; i += 12) { c.moveTo(x * T + i, y * T + 4); c.lineTo(x * T + i - 4, y * T + T - 4); }
        c.stroke();
      }
    }
    // coloured light pools
    c.globalCompositeOperation = "lighter";
    Object.values(ROOMS).forEach((r) => {
      const [rx, ry, rw, rh] = r.rect, cx = (rx + rw / 2) * T, cy = (ry + rh / 2) * T, rad = Math.max(rw, rh) * T * 0.62;
      const g = c.createRadialGradient(cx, cy, 10, cx, cy, rad); g.addColorStop(0, alpha(r.color, 0.30)); g.addColorStop(1, alpha(r.color, 0));
      c.fillStyle = g; c.fillRect(rx * T, ry * T, rw * T, rh * T);
    });
    c.globalCompositeOperation = "source-over";

    // soft shadow where a wall meets the floor
    for (let y = 0; y < ROWS; y++) for (let x = 0; x < COLS; x++) {
      if (!isFloor(x, y)) continue;
      const g = (x0, y0, x1, y1, rx, ry, rw, rh) => { const gr = c.createLinearGradient(x0, y0, x1, y1); gr.addColorStop(0, "rgba(0,0,0,.45)"); gr.addColorStop(1, "rgba(0,0,0,0)"); c.fillStyle = gr; c.fillRect(rx, ry, rw, rh); };
      const px = x * T, py = y * T;
      if (!isFloor(x, y - 1)) g(0, py, 0, py + 18, px, py, T, 18);
      if (!isFloor(x, y + 1)) g(0, py + T, 0, py + T - 10, px, py + T - 10, T, 10);
      if (!isFloor(x - 1, y)) g(px, 0, px + 14, 0, px, py, 14, T);
      if (!isFloor(x + 1, y)) g(px + T, 0, px + T - 14, 0, px + T - 14, py, 14, T);
    }

    // walls: bevelled metal blocks next to the floor, black void further away
    for (let y = 0; y < ROWS; y++) for (let x = 0; x < COLS; x++) {
      if (isFloor(x, y)) continue;
      let near = false;
      for (let j = -1; j <= 1; j++) for (let i = -1; i <= 1; i++) if (isFloor(x + i, y + j)) near = true;
      if (!near) continue;
      const px = x * T, py = y * T, g = c.createLinearGradient(px, py, px, py + T);
      g.addColorStop(0, "#334058"); g.addColorStop(1, "#1E2739"); c.fillStyle = g; c.fillRect(px, py, T, T);
      c.fillStyle = "rgba(255,255,255,.06)"; c.fillRect(px + 3, py + 3, T - 6, 3);
      c.strokeStyle = "rgba(0,0,0,.55)"; c.lineWidth = 2; c.strokeRect(px + 1, py + 1, T - 2, T - 2);
      [[8, 8], [T - 8, 8], [8, T - 8], [T - 8, T - 8]].forEach(([dx, dy]) => { c.fillStyle = "#0E1420"; c.beginPath(); c.arc(px + dx, py + dy, 2.6, 0, 7); c.fill(); c.fillStyle = "rgba(255,255,255,.18)"; c.fillRect(px + dx - 1, py + dy - 1.6, 1.4, 1); });
      c.strokeStyle = "rgba(201,161,90,.55)"; c.lineWidth = 2;                                      // brass trim on the floor side
      if (isFloor(x, y + 1)) { c.beginPath(); c.moveTo(px, py + T - 1); c.lineTo(px + T, py + T - 1); c.stroke(); }
      if (isFloor(x, y - 1)) { c.beginPath(); c.moveTo(px, py + 1); c.lineTo(px + T, py + 1); c.stroke(); }
      if (isFloor(x - 1, y)) { c.beginPath(); c.moveTo(px + 1, py); c.lineTo(px + 1, py + T); c.stroke(); }
      if (isFloor(x + 1, y)) { c.beginPath(); c.moveTo(px + T - 1, py); c.lineTo(px + T - 1, py + T); c.stroke(); }
    }

    // hazard stripes on the door thresholds
    DOORS.forEach(([dx, dy]) => {
      c.save(); c.beginPath(); c.rect(dx * T, dy * T + T / 2 - 7, T * 2, 14); c.clip();
      c.fillStyle = "#1A1F2B"; c.fillRect(dx * T, dy * T, T * 2, T);
      c.fillStyle = "#C9A15A";
      for (let i = -T; i < T * 3; i += 18) { c.beginPath(); c.moveTo(dx * T + i, dy * T + T); c.lineTo(dx * T + i + 9, dy * T + T); c.lineTo(dx * T + i + 9 + T, dy * T); c.lineTo(dx * T + i + T, dy * T); c.fill(); }
      c.restore();
    });

    // names painted on the floor, like markings on a station deck
    c.textAlign = "center"; c.textBaseline = "middle";
    Object.values(ROOMS).forEach((r) => {
      const [rx, ry, rw, rh] = r.rect;
      c.font = "800 26px Inter, 'Segoe UI', Roboto, sans-serif"; c.fillStyle = alpha(r.color, 0.20);
      c.save(); c.translate((rx + rw / 2) * T, (ry + rh - 0.45) * T); if (c.letterSpacing !== undefined) c.letterSpacing = "4px"; c.fillText(r.name.toUpperCase(), 0, 0); c.restore();
    });
    c.font = "800 22px Inter, 'Segoe UI', Roboto, sans-serif"; c.fillStyle = "rgba(255,255,255,.07)";
    if (c.letterSpacing !== undefined) c.letterSpacing = "14px";
    c.fillText("WORTSCHATZ", 17 * T, 11 * T); if (c.letterSpacing !== undefined) c.letterSpacing = "0px";

    // door signs painted on the corridor floor, with a lane arrow, so you can tell which door leads where
    c.font = "800 15px Inter, 'Segoe UI', Roboto, sans-serif"; if (c.letterSpacing !== undefined) c.letterSpacing = "3px";
    [["learn", 6, 8], ["guide", 17, 8], ["test", 28, 8], ["second", 6, 13], ["library", 17, 13], ["diary", 28, 13]].forEach(([k, dx, dy]) => {
      const up = dy === 8, y = (up ? dy + 1.5 : dy - 0.5) * T;
      c.fillStyle = alpha(ROOMS[k].color, 0.55); c.fillText((up ? "▲ " : "▼ ") + ROOMS[k].name.toUpperCase(), dx * T, y);
    });
    if (c.letterSpacing !== undefined) c.letterSpacing = "0px";
    c.strokeStyle = "rgba(201,161,90,.16)"; c.lineWidth = 3; c.setLineDash([22, 16]);
    c.beginPath(); c.moveTo(2 * T, 11 * T); c.lineTo(32 * T, 11 * T); c.stroke(); c.setLineDash([]);

    // rugs under the pads
    STATIONS.forEach((s) => {
      const r = ROOMS[s.room]; c.fillStyle = alpha(r.color, 0.10); c.beginPath(); c.arc(s.x * T, s.y * T, 64, 0, 7); c.fill();
      c.strokeStyle = alpha(r.color, 0.35); c.lineWidth = 2; c.setLineDash([3, 8]); c.beginPath(); c.arc(s.x * T, s.y * T, 64, 0, 7); c.stroke(); c.setLineDash([]);
    });

    // props
    [...PROPS].sort((a, b) => a[2] - b[2]).forEach((p) => drawProp(c, p[0], p[1] * T, p[2] * T, p[3] * T, p[4] * T));
    return cv;
  }

  function drawProp(c, type, x, y, w, h) {
    c.save();
    c.shadowColor = "rgba(0,0,0,.55)"; c.shadowBlur = 14; c.shadowOffsetX = 4; c.shadowOffsetY = 7;
    const rnd = seeded(Math.round(x + y * 7));
    if (type === "shelf") {
      const wood = c.createLinearGradient(x, y, x, y + h); wood.addColorStop(0, "#5A4332"); wood.addColorStop(1, "#3A2B21");
      c.fillStyle = wood; rrect(c, x + 3, y + 3, w - 6, h - 6, 5); c.fill(); c.shadowColor = "transparent";
      const horizontal = w >= h, len = horizontal ? w : h, n = Math.floor(len / 9);
      for (let i = 0; i < n; i++) {
        const col = BOOKS[Math.floor(rnd() * BOOKS.length)]; c.fillStyle = col;
        if (horizontal) c.fillRect(x + 8 + i * ((w - 16) / n), y + 10, (w - 16) / n - 1.5, h - 20); else c.fillRect(x + 10, y + 8 + i * ((h - 16) / n), w - 20, (h - 16) / n - 1.5);
      }
      c.strokeStyle = "rgba(201,161,90,.6)"; c.lineWidth = 1.5; rrect(c, x + 3, y + 3, w - 6, h - 6, 5); c.stroke();
    } else if (type === "desk" || type === "examdesk" || type === "table") {
      const wood = c.createLinearGradient(x, y, x + w, y + h); wood.addColorStop(0, type === "examdesk" ? "#7A6A56" : "#6A5039"); wood.addColorStop(1, type === "examdesk" ? "#5C4F40" : "#4B3827");
      c.fillStyle = wood; rrect(c, x + 3, y + 6, w - 6, h - 12, 8); c.fill(); c.shadowColor = "transparent";
      c.strokeStyle = "rgba(255,255,255,.14)"; c.lineWidth = 1.5; rrect(c, x + 3, y + 6, w - 6, h - 12, 8); c.stroke();
      if (type === "desk") {
        c.fillStyle = "#0E1420"; rrect(c, x + 14, y + 12, 30, 22, 3); c.fill(); c.fillStyle = "rgba(120,190,255,.55)"; rrect(c, x + 17, y + 14, 24, 14, 2); c.fill();
        c.fillStyle = "#F0EADB"; c.fillRect(x + w - 54, y + 14, 22, 26); c.fillStyle = "#C9A15A"; c.beginPath(); c.arc(x + w - 18, y + 20, 7, 0, 7); c.fill();
      } else if (type === "examdesk") {
        c.fillStyle = "#F0EADB"; c.save(); c.translate(x + 30, y + h / 2); c.rotate(-0.08); c.fillRect(-14, -14, 28, 28); c.restore();
        c.strokeStyle = "#7B2D3B"; c.lineWidth = 2; c.beginPath(); c.moveTo(x + 24, y + h / 2); c.lineTo(x + 34, y + h / 2 + 4); c.lineTo(x + 40, y + h / 2 - 8); c.stroke();
        c.fillStyle = "#C9A15A"; c.fillRect(x + w - 26, y + h / 2 - 3, 18, 5);
      } else { c.fillStyle = "#F0EADB"; c.fillRect(x + 12, y + 14, 20, 20); c.fillStyle = "#35506B"; c.beginPath(); c.arc(x + w - 24, y + h / 2, 9, 0, 7); c.fill(); }
    } else if (type === "board") {
      c.fillStyle = "#20463B"; rrect(c, x + 4, y + 6, w - 8, h - 12, 4); c.fill(); c.shadowColor = "transparent";
      c.strokeStyle = "#C9A15A"; c.lineWidth = 3; rrect(c, x + 4, y + 6, w - 8, h - 12, 4); c.stroke();
      c.fillStyle = "rgba(240,234,219,.9)"; c.font = "700 26px Georgia, serif"; c.textAlign = "center"; c.textBaseline = "middle"; c.fillText("A+", x + w * 0.22, y + h / 2);
      c.strokeStyle = "rgba(240,234,219,.6)"; c.lineWidth = 2; c.beginPath(); c.moveTo(x + w * 0.42, y + h / 2); c.lineTo(x + w * 0.62, y + h / 2); c.moveTo(x + w * 0.42, y + h / 2 + 8); c.lineTo(x + w * 0.55, y + h / 2 + 8); c.stroke();
      c.strokeStyle = "#7FD8B0"; c.lineWidth = 4; c.beginPath(); c.moveTo(x + w * 0.74, y + h / 2); c.lineTo(x + w * 0.78, y + h / 2 + 9); c.lineTo(x + w * 0.88, y + h / 2 - 10); c.stroke();
    } else if (type === "sofa") {
      c.fillStyle = "#6B2A3A"; rrect(c, x + 3, y + 4, w - 6, h - 8, 12); c.fill(); c.shadowColor = "transparent";
      c.fillStyle = "#8A3A4C"; for (let i = 0; i < 3; i++) { rrect(c, x + 10 + i * ((w - 20) / 3), y + 12, (w - 20) / 3 - 4, h - 22, 8); c.fill(); }
    } else if (type === "bed") {
      c.fillStyle = "#2C3446"; rrect(c, x + 3, y + 3, w - 6, h - 6, 8); c.fill(); c.shadowColor = "transparent";
      c.fillStyle = "#E8E2D2"; rrect(c, x + 10, y + 10, w - 20, h - 20, 8); c.fill();
      c.fillStyle = "#F7F3E8"; rrect(c, x + 16, y + 16, 28, h - 32, 8); c.fill(); rrect(c, x + 16, y + 16, 28, 0.001, 1); c.fill();
      c.fillStyle = "#A9812F"; rrect(c, x + 52, y + 10, w - 62, h - 20, 6); c.fill(); c.fillStyle = "rgba(255,255,255,.18)"; c.fillRect(x + 52, y + 30, w - 62, 4);
    } else if (type === "locker") {
      c.fillStyle = "#3A4558"; rrect(c, x + 3, y + 3, w - 6, h - 6, 4); c.fill(); c.shadowColor = "transparent";
      const n = Math.round(w / 32); for (let i = 0; i < n; i++) {
        const lx = x + 8 + i * ((w - 16) / n); c.fillStyle = "#2B3547"; rrect(c, lx, y + 8, (w - 16) / n - 5, h - 16, 3); c.fill();
        c.fillStyle = "rgba(255,255,255,.18)"; for (let k = 0; k < 3; k++) c.fillRect(lx + 6, y + 14 + k * 4, (w - 16) / n - 17, 1.5);
      }
    } else if (type === "terminal") {
      c.fillStyle = "#222C3E"; rrect(c, x + 3, y + 3, w - 6, h - 6, 6); c.fill(); c.shadowColor = "transparent";
      c.fillStyle = "#0A1019"; rrect(c, x + 9, y + 9, w - 18, h - 20, 4); c.fill();
      const col = x < 16 * T ? "#C9AE74" : "#44A08A"; c.fillStyle = alpha(col, 0.9);
      if (x < 16 * T) { c.font = "800 30px Georgia, serif"; c.textAlign = "center"; c.textBaseline = "middle"; c.fillText("?", x + w / 2, y + h / 2 - 1); }
      else for (let i = 0; i < 6; i++) c.fillRect(x + 16 + i * 12, y + h - 18 - (6 + ((i * 7) % 5) * 4), 8, 6 + ((i * 7) % 5) * 4);
    } else if (type === "holo") {
      c.fillStyle = "#222C3E"; rrect(c, x + 6, y + 6, w - 12, h - 12, 16); c.fill(); c.shadowColor = "transparent";
      const g = c.createRadialGradient(x + w / 2, y + h / 2, 2, x + w / 2, y + h / 2, 34); g.addColorStop(0, "rgba(201,174,116,.9)"); g.addColorStop(1, "rgba(201,174,116,0)");
      c.fillStyle = g; c.beginPath(); c.arc(x + w / 2, y + h / 2, 34, 0, 7); c.fill();
    } else if (type === "crate") {
      c.fillStyle = "#7A5A3A"; rrect(c, x + 6, y + 6, w - 12, h - 12, 3); c.fill(); c.shadowColor = "transparent";
      c.strokeStyle = "#4C3822"; c.lineWidth = 2; c.strokeRect(x + 10, y + 10, w - 20, h - 20); c.beginPath(); c.moveTo(x + 10, y + 10); c.lineTo(x + w - 10, y + h - 10); c.moveTo(x + w - 10, y + 10); c.lineTo(x + 10, y + h - 10); c.stroke();
    } else if (type === "plant") {
      c.fillStyle = "#4A3426"; c.beginPath(); c.arc(x + w / 2, y + h / 2, 14, 0, 7); c.fill(); c.shadowColor = "transparent";
      for (let i = 0; i < 9; i++) { const a = (i / 9) * 6.283; c.fillStyle = i % 2 ? "#3F8A5C" : "#2F6B4A"; c.beginPath(); c.ellipse(x + w / 2 + Math.cos(a) * 11, y + h / 2 + Math.sin(a) * 11, 10, 5, a, 0, 7); c.fill(); }
    }
    c.restore();
  }

  // ---------------------------------------------------------------- icons on the pads
  function icon(c, key, x, y, col) {
    c.save(); c.translate(x, y); c.strokeStyle = col; c.fillStyle = col; c.lineWidth = 3; c.lineCap = "round"; c.lineJoin = "round";
    if (key === "learn") { c.beginPath(); c.moveTo(0, -9); c.lineTo(0, 11); c.moveTo(0, -9); c.quadraticCurveTo(-9, -13, -16, -8); c.lineTo(-16, 10); c.quadraticCurveTo(-9, 6, 0, 11); c.quadraticCurveTo(9, 6, 16, 10); c.lineTo(16, -8); c.quadraticCurveTo(9, -13, 0, -9); c.stroke(); }
    else if (key === "test") { c.beginPath(); c.moveTo(-12, 1); c.lineTo(-4, 9); c.lineTo(13, -9); c.stroke(); }
    else if (key === "second") { c.beginPath(); c.arc(0, 1, 11, -2.4, 3.2); c.stroke(); c.beginPath(); c.moveTo(-14, -9); c.lineTo(-8, -9); c.lineTo(-8, -3); c.stroke(); }
    else if (key === "diary") { c.strokeRect(-11, -13, 22, 26); c.beginPath(); c.moveTo(-5, -13); c.lineTo(-5, 13); c.stroke(); c.fillRect(2, -7, 6, 2); c.fillRect(2, -1, 6, 2); }
    else if (key === "guide") { c.font = "800 26px Georgia, serif"; c.textAlign = "center"; c.textBaseline = "middle"; c.fillText("?", 0, 1); }
    else if (key === "progress") { c.fillRect(-13, 2, 6, 10); c.fillRect(-3, -6, 6, 18); c.fillRect(7, -12, 6, 24); }
    else if (key === "library") { c.strokeRect(-13, -11, 26, 7); c.strokeRect(-13, -2, 26, 7); c.strokeRect(-13, 7, 26, 5); }
    c.restore();
  }

  // ---------------------------------------------------------------- the game
  function start(cfg) {
    const canvas = document.getElementById("world"); if (!canvas || canvas.dataset.running) return;
    canvas.dataset.running = "1";
    const wrap = canvas.parentElement, roomChip = wrap.querySelector("#world-room"), prompt = wrap.querySelector("#world-prompt");
    const ctx = canvas.getContext("2d");
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const layer = buildStatic(dpr);
    let vw = 0, vh = 0, zoom = 1;

    const resize = () => {
      const r = wrap.getBoundingClientRect(); vw = Math.max(280, r.width); vh = Math.max(300, r.height);
      const cw = Math.round(vw * dpr), ch = Math.round(vh * dpr);
      if (canvas.width !== cw || canvas.height !== ch) { canvas.width = cw; canvas.height = ch; }          // resizing clears the canvas, so only when it changed
      zoom = clamp(vw / 900, 0.8, 1.25);
    };
    new ResizeObserver(resize).observe(wrap); resize();

    // where to start: next to the pad we last used, otherwise the middle of the corridor
    let from = null; try { from = sessionStorage.getItem("wortschatz.pad"); sessionStorage.removeItem("wortschatz.pad"); } catch (e) { /* storage may be blocked */ }
    const home = STATIONS.find((s) => s.key === from);
    const me = { x: home ? home.x * T : 17 * T, y: home ? home.y * T + 70 : 10.5 * T, face: Math.PI / 2, stride: 0, moving: false };
    if (home) me.y = Math.min(me.y, (CORRIDOR.rect[1] + CORRIDOR.rect[3] - 0.5) * T);
    if (home && blocked(Math.floor(me.x / T), Math.floor(me.y / T))) { me.x = home.x * T; me.y = home.y * T + 52; }
    const cam = { x: me.x, y: me.y };
    const keys = new Set();
    let path = [], target = null, near = null, leaving = false, t0 = performance.now(), last = t0;
    const dust = Array.from({ length: 46 }, (_, i) => { const r = seeded(i + 3); return { x: r() * W, y: r() * H, s: 0.4 + r() * 1.4, v: 4 + r() * 10, p: r() * 6 }; });

    const stationBadge = (s) => (cfg.badges || {})[s.key] || "";
    const urgent = (s) => (cfg.urgent || []).includes(s.key);

    // ---- walking
    const hits = (px, py) => {
      for (let y = Math.floor((py - RADIUS) / T); y <= Math.floor((py + RADIUS) / T); y++) for (let x = Math.floor((px - RADIUS) / T); x <= Math.floor((px + RADIUS) / T); x++) if (blocked(x, y)) return true;
      return false;
    };
    function step(dx, dy) { if (!hits(me.x + dx, me.y)) me.x += dx; if (!hits(me.x, me.y + dy)) me.y += dy; }

    function findPath(tx, ty) {                                   // breadth-first over tiles, then walked tile by tile
      const sx = Math.floor(me.x / T), sy = Math.floor(me.y / T); let gx = Math.floor(tx / T), gy = Math.floor(ty / T);
      if (blocked(gx, gy)) { let best = null; for (let r = 1; r < 4 && !best; r++) for (let j = -r; j <= r; j++) for (let i = -r; i <= r; i++) if (!blocked(gx + i, gy + j) && (!best || Math.hypot(i, j) < Math.hypot(best[0], best[1]))) best = [i, j]; if (!best) return []; gx += best[0]; gy += best[1]; }
      const prev = new Map(), id = (x, y) => y * COLS + x, queue = [[sx, sy]]; prev.set(id(sx, sy), null);
      while (queue.length) {
        const [x, y] = queue.shift(); if (x === gx && y === gy) break;
        for (const [i, j] of [[1, 0], [-1, 0], [0, 1], [0, -1], [1, 1], [1, -1], [-1, 1], [-1, -1]]) {
          const nx = x + i, ny = y + j; if (blocked(nx, ny) || prev.has(id(nx, ny))) continue;
          if (i && j && (blocked(x + i, y) || blocked(x, y + j))) continue;
          prev.set(id(nx, ny), [x, y]); queue.push([nx, ny]);
        }
      }
      if (!prev.has(id(gx, gy))) return [];
      const out = []; for (let cur = [gx, gy]; cur; cur = prev.get(id(cur[0], cur[1]))) out.unshift([(cur[0] + 0.5) * T, (cur[1] + 0.5) * T]);
      out.shift(); return out;
    }

    // ---- entering
    function enter(s) {
      if (leaving) return;
      if (s.action === "guide") { const b = document.getElementById("open-guide"); if (b) b.click(); return; }
      leaving = true; wrap.classList.add("leaving");
      try { sessionStorage.setItem("wortschatz.pad", s.key); } catch (e) { /* ignore */ }
      setTimeout(() => { window.location.href = s.url; }, 320);
    }
    prompt.addEventListener("click", () => near && enter(near));

    // ---- input
    const typing = () => /^(input|textarea|select)$/i.test((document.activeElement || {}).tagName || "");
    window.addEventListener("keydown", (e) => {
      if (typing() || e.ctrlKey || e.metaKey || e.altKey) return;
      const k = e.key.toLowerCase();
      if (["arrowup", "arrowdown", "arrowleft", "arrowright", "w", "a", "s", "d"].includes(k)) { keys.add(k); path = []; target = null; e.preventDefault(); }
      else if ((k === "e" || k === "enter" || k === " ") && near) { e.preventDefault(); enter(near); }
    });
    window.addEventListener("keyup", (e) => keys.delete(e.key.toLowerCase()));
    window.addEventListener("blur", () => keys.clear());
    canvas.addEventListener("pointerdown", (e) => {
      const r = canvas.getBoundingClientRect(), wx = (e.clientX - r.left) / zoom + cam.x - vw / zoom / 2, wy = (e.clientY - r.top) / zoom + cam.y - vh / zoom / 2;
      const s = STATIONS.find((p) => Math.hypot(wx - p.x * T, wy - p.y * T) < 60);
      target = s || null; path = findPath(s ? s.x * T : wx, s ? s.y * T : wy);
    });

    // ---- drawing
    function drawDoor(d, t, open) {
      const [dx, dy] = d, w = T * 2, y = dy * T, x = dx * T, slide = open * (T * 0.9);
      ctx.fillStyle = "#2B364C"; ctx.strokeStyle = "rgba(201,161,90,.8)"; ctx.lineWidth = 2;
      ctx.fillRect(x, y + T / 2 - 9, w / 2 - slide, 18); ctx.strokeRect(x, y + T / 2 - 9, w / 2 - slide, 18);
      ctx.fillRect(x + w / 2 + slide, y + T / 2 - 9, w / 2 - slide, 18); ctx.strokeRect(x + w / 2 + slide, y + T / 2 - 9, w / 2 - slide, 18);
      ctx.fillStyle = "rgba(124,255,200," + (0.5 + 0.4 * Math.sin(t * 3 + dx)) + ")"; ctx.fillRect(x + 4, y + T / 2 - 2, 4, 4); ctx.fillRect(x + w - 8, y + T / 2 - 2, 4, 4);
    }
    function drawPad(s, t) {
      const r = ROOMS[s.room], x = s.x * T, y = s.y * T, active = near === s, pulse = 1 + 0.06 * Math.sin(t * 3 + x);
      const g = ctx.createRadialGradient(x, y, 4, x, y, 72 * pulse); g.addColorStop(0, alpha(r.color, active ? 0.7 : 0.42)); g.addColorStop(1, alpha(r.color, 0));
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, 72 * pulse, 0, 7); ctx.fill();
      ctx.fillStyle = "#101826"; ctx.beginPath(); ctx.arc(x, y, 34, 0, 7); ctx.fill();
      ctx.strokeStyle = r.color; ctx.lineWidth = active ? 5 : 3; ctx.beginPath(); ctx.arc(x, y, 34, 0, 7); ctx.stroke();
      ctx.strokeStyle = alpha("#FFFFFF", 0.5); ctx.lineWidth = 2; ctx.setLineDash([6, 10]); ctx.lineDashOffset = -t * 18; ctx.beginPath(); ctx.arc(x, y, 43, 0, 7); ctx.stroke(); ctx.setLineDash([]);
      icon(ctx, s.key, x, y, "#F4EFE2");
    }
    function drawBadge(s, t) {
      const r = ROOMS[s.room], x = s.x * T, y = s.y * T, text = stationBadge(s);
      if (text) {
        ctx.font = "700 13px Inter, 'Segoe UI', Roboto, sans-serif"; const w = ctx.measureText(text).width + 22, by = y - 64 + (urgent(s) ? Math.sin(t * 4) * 2.5 : 0);
        ctx.fillStyle = urgent(s) ? "#CC7456" : "rgba(11,16,26,.9)"; rrect(ctx, x - w / 2, by - 12, w, 24, 12); ctx.fill();
        ctx.strokeStyle = r.color; ctx.lineWidth = 1.5; rrect(ctx, x - w / 2, by - 12, w, 24, 12); ctx.stroke();
        ctx.fillStyle = "#F4EFE2"; ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.fillText(text, x, by + 0.5);
      }
    }
    function drawPlayer(t) {
      const sw = me.moving ? Math.sin(me.stride) : 0, x = me.x, y = me.y;
      ctx.save(); ctx.translate(x, y);
      const glow = ctx.createRadialGradient(0, 0, 4, 0, 0, 120); glow.addColorStop(0, "rgba(255,236,190,.22)"); glow.addColorStop(1, "rgba(255,236,190,0)");
      ctx.globalCompositeOperation = "lighter"; ctx.fillStyle = glow; ctx.beginPath(); ctx.arc(0, 0, 120, 0, 7); ctx.fill(); ctx.globalCompositeOperation = "source-over";
      ctx.fillStyle = "rgba(0,0,0,.4)"; ctx.beginPath(); ctx.ellipse(2, 5, 17, 13, 0, 0, 7); ctx.fill();
      ctx.rotate(me.face + Math.PI / 2);                                  // the avatar is drawn facing up; turn it towards where it walks
      ctx.fillStyle = "#E7C6A0";                                           // hands swing with the stride
      ctx.beginPath(); ctx.arc(-17, -sw * 7, 4.6, 0, 7); ctx.fill(); ctx.beginPath(); ctx.arc(17, sw * 7, 4.6, 0, 7); ctx.fill();
      const body = ctx.createLinearGradient(-16, 0, 16, 0); body.addColorStop(0, "#1F3556"); body.addColorStop(0.5, "#2D4A78"); body.addColorStop(1, "#1F3556");
      ctx.fillStyle = body; rrect(ctx, -16, -9, 32, 19, 9); ctx.fill();                                // shoulders
      ctx.fillStyle = "#C9A15A"; ctx.fillRect(-2, -9, 4, 19);                                           // brass strap
      ctx.fillStyle = "#3A2A22"; ctx.beginPath(); ctx.arc(0, 0, 10.5, 0, 7); ctx.fill();                // hair
      ctx.fillStyle = "#EBCBA6"; ctx.beginPath(); ctx.arc(0, -2.4, 9, 0, 7); ctx.fill();               // face side
      ctx.fillStyle = "#3A2A22"; ctx.beginPath(); ctx.arc(0, 2.4, 9, 0, 3.2); ctx.fill();
      ctx.restore();
    }

    // ---- main loop
    function frame(now) {
      requestAnimationFrame(frame); if (document.hidden) { last = now; return; }
      const dt = Math.min(0.05, (now - last) / 1000), t = (now - t0) / 1000; last = now;
      let dx = (keys.has("d") || keys.has("arrowright") ? 1 : 0) - (keys.has("a") || keys.has("arrowleft") ? 1 : 0);
      let dy = (keys.has("s") || keys.has("arrowdown") ? 1 : 0) - (keys.has("w") || keys.has("arrowup") ? 1 : 0);
      if (!dx && !dy && path.length) {
        const [px, py] = path[0], d = Math.hypot(px - me.x, py - me.y);
        if (d < 6) { path.shift(); if (!path.length && target) { const s = target; target = null; enter(s); } } else { dx = (px - me.x) / d; dy = (py - me.y) / d; }
      }
      me.moving = !!(dx || dy) && !leaving;
      if (me.moving) {
        const len = Math.hypot(dx, dy); dx /= len; dy /= len; step(dx * SPEED * dt, dy * SPEED * dt);
        let a = Math.atan2(dy, dx) - me.face; a = Math.atan2(Math.sin(a), Math.cos(a)); me.face += a * Math.min(1, dt * 14); me.stride += dt * 13;
      }
      near = null; let best = REACH;
      STATIONS.forEach((s) => { const d = Math.hypot(me.x - s.x * T, me.y - s.y * T); if (d < best) { best = d; near = s; } });
      const room = roomAt(me.x, me.y); if (room && roomChip.dataset.room !== room.name) { roomChip.dataset.room = room.name; roomChip.querySelector("b").textContent = room.name; roomChip.style.setProperty("--room", room.color); }
      prompt.classList.toggle("on", !!near && !leaving);
      if (near) { prompt.querySelector("span").textContent = near.label; prompt.style.setProperty("--room", ROOMS[near.room].color); }

      const k = 1 - Math.pow(0.0015, dt); cam.x += (me.x - cam.x) * k; cam.y += (me.y - cam.y) * k;
      const halfW = vw / zoom / 2, halfH = vh / zoom / 2;
      const cx = W <= halfW * 2 ? W / 2 : clamp(cam.x, halfW, W - halfW), cy = H <= halfH * 2 ? H / 2 : clamp(cam.y, halfH, H - halfH);

      ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.fillStyle = "#070B12"; ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.setTransform(dpr * zoom, 0, 0, dpr * zoom, dpr * (vw / 2 - cx * zoom), dpr * (vh / 2 - cy * zoom));
      ctx.drawImage(layer, 0, 0, W, H);
      DOORS.forEach((d) => { const dist = Math.hypot(me.x - (d[0] + 1) * T, me.y - (d[1] + 0.5) * T); drawDoor(d, t, clamp(1 - (dist - 40) / 90, 0, 1)); });
      STATIONS.forEach((s) => drawPad(s, t));
      dust.forEach((p) => { p.y -= p.v * dt; p.x += Math.sin(t * 0.6 + p.p) * 6 * dt; if (p.y < 0) p.y = H; ctx.fillStyle = "rgba(255,240,210," + (0.10 + 0.08 * Math.sin(t + p.p)) + ")"; ctx.beginPath(); ctx.arc(p.x, p.y, p.s, 0, 7); ctx.fill(); });
      drawPlayer(t);
      STATIONS.forEach((s) => drawBadge(s, t));
    }
    requestAnimationFrame(frame);
    window.__wortschatzWorld = { me, cam, view: () => ({ vw, vh, zoom, dpr }), layer, stations: STATIONS, enter, teleport: (x, y) => { me.x = x * T; me.y = y * T; } };       // used by the tests and the screenshots
  }

  // The page is built by NiceGUI after this file loads, so wait for the canvas to appear.
  (function wait(tries) {
    if (document.getElementById("world") && window.WORTSCHATZ_WORLD) return start(window.WORTSCHATZ_WORLD);
    if (tries < 200) setTimeout(() => wait(tries + 1), 50);
  })(0);
})();
