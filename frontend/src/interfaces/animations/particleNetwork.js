/**
 * Data Flow Network — scoped to a single container element.
 *
 * Layers:
 *   0  faint grid (dashboard feel)
 *   1  hub nodes — large, slow, pulsing rings
 *   2  signal particles — small, fast, drift between hubs
 *   3  data packets — bright dots travelling along connection lines
 *   4  cursor glow — radial bloom that follows the mouse
 */

const REDUCED = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/* ── Palette ─────────────────────────────────────────────────────────── */
const PETROL = [14, 94, 111];
const TEAL = [62, 143, 163];
const AMBER = [199, 123, 33];
const INK = [92, 102, 114];

/* ── Tuning ──────────────────────────────────────────────────────────── */
const CFG = {
  gridSpacing: 56,
  gridAlpha: 0.04,

  hubCount: () => (W < 640 ? 14 : W < 1024 ? 22 : 32),
  hubMinR: 2.2,
  hubMaxR: 4,
  hubSpeed: 0.09,
  hubConnectDist: 200,
  hubPulseMaxR: 45,
  hubPulseDuration: 1800,

  signalCount: () => (W < 640 ? 30 : W < 1024 ? 50 : 80),
  signalMinR: 0.6,
  signalMaxR: 1.3,
  signalSpeed: 0.4,
  signalConnectDist: 90,

  packetSpeed: 1.4,
  packetMaxPerLine: 2,
  packetSpawnChance: 0.006,

  mouseAttractDist: 220,
  mouseAttractForce: 0.0007,
  mouseRepelDist: 55,
  mouseRepelForce: 0.018,
  glowRadius: 260,

  damping: 0.97,
};

let W, H;

/* ── Helpers ─────────────────────────────────────────────────────────── */
function rand(min, max) { return Math.random() * (max - min) + min; }
function dist(a, b) { const dx = a.x - b.x, dy = a.y - b.y; return Math.sqrt(dx * dx + dy * dy); }

function wrapEdge(p) {
  if (p.x < -20) p.x = W + 20;
  else if (p.x > W + 20) p.x = -20;
  if (p.y < -20) p.y = H + 20;
  else if (p.y > H + 20) p.y = -20;
}

/* ── Factories ───────────────────────────────────────────────────────── */
function createHub() {
  return {
    x: rand(30, W - 30),
    y: rand(30, H - 30),
    vx: (Math.random() - 0.5) * CFG.hubSpeed,
    vy: (Math.random() - 0.5) * CFG.hubSpeed,
    r: rand(CFG.hubMinR, CFG.hubMaxR),
    color: Math.random() < 0.55 ? PETROL : TEAL,
    alpha: rand(0.3, 0.6),
    pulseStart: -9999,
    pulseActive: false,
  };
}

function createSignal() {
  return {
    x: rand(0, W),
    y: rand(0, H),
    vx: (Math.random() - 0.5) * CFG.signalSpeed,
    vy: (Math.random() - 0.5) * CFG.signalSpeed,
    r: rand(CFG.signalMinR, CFG.signalMaxR),
    color: Math.random() < 0.25 ? AMBER : INK,
    alpha: rand(0.1, 0.28),
  };
}

function createPacket(ax, ay, bx, by) {
  const t = Math.random();
  return {
    x: ax + (bx - ax) * t,
    y: ay + (by - ay) * t,
    ax, ay, bx, by,
    t,
    r: 1.6,
    alpha: 0.85,
    speed: CFG.packetSpeed * (0.6 + Math.random() * 0.8),
  };
}

/* ── Main ────────────────────────────────────────────────────────────── */
function init(canvas, container) {
  const ctx = canvas.getContext("2d");
  let hubs, signals, packets, mouse, lastTime, raf;

  function resize() {
    const rect = container.getBoundingClientRect();
    W = canvas.width = rect.width;
    H = canvas.height = rect.height;
  }

  function populate() {
    hubs = [];
    signals = [];
    packets = [];
    for (let i = 0; i < CFG.hubCount(); i++) hubs.push(createHub());
    for (let i = 0; i < CFG.signalCount(); i++) signals.push(createSignal());
  }

  mouse = { x: -9999, y: -9999, active: false };

  function onMouse(e) {
    const rect = container.getBoundingClientRect();
    mouse.x = e.clientX - rect.left;
    mouse.y = e.clientY - rect.top;
    // Only active when inside the container
    mouse.active = (
      e.clientX >= rect.left && e.clientX <= rect.right &&
      e.clientY >= rect.top && e.clientY <= rect.bottom
    );
  }
  function onMouseLeave() {
    mouse.active = false;
    mouse.x = -9999;
    mouse.y = -9999;
  }

  /* ── Update ──────────────────────────────────────────────────────── */
  function update(dt) {
    const all = hubs.concat(signals);

    for (const p of all) {
      const dx = mouse.x - p.x;
      const dy = mouse.y - p.y;
      const d = Math.sqrt(dx * dx + dy * dy);

      if (d < CFG.mouseRepelDist && d > 0 && mouse.active) {
        const f = (1 - d / CFG.mouseRepelDist) * CFG.mouseRepelForce;
        p.vx -= dx * f;
        p.vy -= dy * f;
      } else if (d < CFG.mouseAttractDist && d > 0 && mouse.active) {
        const f = (1 - d / CFG.mouseAttractDist) * CFG.mouseAttractForce;
        p.vx += dx * f;
        p.vy += dy * f;
      }

      p.vx *= CFG.damping;
      p.vy *= CFG.damping;
      p.x += p.vx;
      p.y += p.vy;
      wrapEdge(p);
    }

    // Hub pulses
    for (const h of hubs) {
      if (!h.pulseActive && Math.random() < 0.001) {
        h.pulseStart = performance.now();
        h.pulseActive = true;
      }
      if (h.pulseActive && performance.now() - h.pulseStart > CFG.hubPulseDuration) {
        h.pulseActive = false;
      }
    }

    // Spawn packets
    for (let i = 0; i < hubs.length; i++) {
      for (let j = i + 1; j < hubs.length; j++) {
        const d = dist(hubs[i], hubs[j]);
        if (d < CFG.hubConnectDist && Math.random() < CFG.packetSpawnChance) {
          const count = packets.filter(
            (pk) => (pk.ax === hubs[i].x && pk.ay === hubs[i].y) ||
                     (pk.ax === hubs[j].x && pk.ay === hubs[j].y)
          ).length;
          if (count < CFG.packetMaxPerLine) {
            const rev = Math.random() < 0.5;
            packets.push(createPacket(
              rev ? hubs[j].x : hubs[i].x,
              rev ? hubs[j].y : hubs[i].y,
              rev ? hubs[i].x : hubs[j].x,
              rev ? hubs[i].y : hubs[j].y,
            ));
          }
        }
      }
    }

    // Advance packets
    for (let i = packets.length - 1; i >= 0; i--) {
      const pk = packets[i];
      pk.t += pk.speed * dt * 0.001;
      if (pk.t >= 1) { packets.splice(i, 1); continue; }
      pk.x = pk.ax + (pk.bx - pk.ax) * pk.t;
      pk.y = pk.ay + (pk.by - pk.ay) * pk.t;
    }
  }

  /* ── Draw ────────────────────────────────────────────────────────── */
  function drawGrid() {
    ctx.strokeStyle = `rgba(62, 143, 163, ${CFG.gridAlpha})`;
    ctx.lineWidth = 0.5;
    for (let x = 0; x < W; x += CFG.gridSpacing) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke();
    }
    for (let y = 0; y < H; y += CFG.gridSpacing) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
    }
  }

  function drawHubConnections() {
    for (let i = 0; i < hubs.length; i++) {
      for (let j = i + 1; j < hubs.length; j++) {
        const d = dist(hubs[i], hubs[j]);
        if (d < CFG.hubConnectDist) {
          const t = 1 - d / CFG.hubConnectDist;
          const alpha = t * 0.16;
          const lw = 0.4 + t * 1;

          const grad = ctx.createLinearGradient(hubs[i].x, hubs[i].y, hubs[j].x, hubs[j].y);
          grad.addColorStop(0, `rgba(${TEAL[0]}, ${TEAL[1]}, ${TEAL[2]}, ${alpha})`);
          grad.addColorStop(1, `rgba(${PETROL[0]}, ${PETROL[1]}, ${PETROL[2]}, ${alpha * 0.5})`);

          ctx.beginPath();
          ctx.moveTo(hubs[i].x, hubs[i].y);
          ctx.lineTo(hubs[j].x, hubs[j].y);
          ctx.strokeStyle = grad;
          ctx.lineWidth = lw;
          ctx.stroke();
        }
      }
    }
  }

  function drawHubs(now) {
    for (const h of hubs) {
      // Glow
      const g = ctx.createRadialGradient(h.x, h.y, 0, h.x, h.y, h.r * 5);
      g.addColorStop(0, `rgba(${h.color[0]}, ${h.color[1]}, ${h.color[2]}, ${h.alpha * 0.3})`);
      g.addColorStop(1, `rgba(${h.color[0]}, ${h.color[1]}, ${h.color[2]}, 0)`);
      ctx.beginPath();
      ctx.arc(h.x, h.y, h.r * 5, 0, Math.PI * 2);
      ctx.fillStyle = g;
      ctx.fill();

      // Pulse ring
      if (h.pulseActive) {
        const progress = (now - h.pulseStart) / CFG.hubPulseDuration;
        const ringR = h.r + CFG.hubPulseMaxR * progress;
        const ringAlpha = (1 - progress) * 0.22;
        ctx.beginPath();
        ctx.arc(h.x, h.y, ringR, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(${TEAL[0]}, ${TEAL[1]}, ${TEAL[2]}, ${ringAlpha})`;
        ctx.lineWidth = 1.2;
        ctx.stroke();
      }

      // Core
      ctx.beginPath();
      ctx.arc(h.x, h.y, h.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${h.color[0]}, ${h.color[1]}, ${h.color[2]}, ${h.alpha})`;
      ctx.fill();
    }
  }

  function drawSignals() {
    for (const s of signals) {
      ctx.beginPath();
      ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${s.color[0]}, ${s.color[1]}, ${s.color[2]}, ${s.alpha})`;
      ctx.fill();
    }

    for (let i = 0; i < signals.length; i++) {
      for (let j = i + 1; j < signals.length; j++) {
        const d = dist(signals[i], signals[j]);
        if (d < CFG.signalConnectDist) {
          const alpha = (1 - d / CFG.signalConnectDist) * 0.06;
          ctx.beginPath();
          ctx.moveTo(signals[i].x, signals[i].y);
          ctx.lineTo(signals[j].x, signals[j].y);
          ctx.strokeStyle = `rgba(${INK[0]}, ${INK[1]}, ${INK[2]}, ${alpha})`;
          ctx.lineWidth = 0.3;
          ctx.stroke();
        }
      }
    }
  }

  function drawPackets() {
    for (const pk of packets) {
      const tailT = Math.max(0, pk.t - 0.07);
      const tx = pk.ax + (pk.bx - pk.ax) * tailT;
      const ty = pk.ay + (pk.by - pk.ay) * tailT;

      const grad = ctx.createLinearGradient(tx, ty, pk.x, pk.y);
      grad.addColorStop(0, `rgba(${AMBER[0]}, ${AMBER[1]}, ${AMBER[2]}, 0)`);
      grad.addColorStop(1, `rgba(${AMBER[0]}, ${AMBER[1]}, ${AMBER[2]}, ${pk.alpha})`);

      ctx.beginPath();
      ctx.moveTo(tx, ty);
      ctx.lineTo(pk.x, pk.y);
      ctx.strokeStyle = grad;
      ctx.lineWidth = pk.r;
      ctx.lineCap = "round";
      ctx.stroke();

      ctx.beginPath();
      ctx.arc(pk.x, pk.y, pk.r * 0.9, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${AMBER[0]}, ${AMBER[1]}, ${AMBER[2]}, ${pk.alpha})`;
      ctx.fill();
    }
  }

  function drawCursorGlow() {
    if (!mouse.active) return;
    const g = ctx.createRadialGradient(mouse.x, mouse.y, 0, mouse.x, mouse.y, CFG.glowRadius);
    g.addColorStop(0, "rgba(62, 143, 163, 0.07)");
    g.addColorStop(0.5, "rgba(14, 94, 111, 0.03)");
    g.addColorStop(1, "rgba(14, 94, 111, 0)");
    ctx.beginPath();
    ctx.arc(mouse.x, mouse.y, CFG.glowRadius, 0, Math.PI * 2);
    ctx.fillStyle = g;
    ctx.fill();
  }

  /* ── Loop ────────────────────────────────────────────────────────── */
  function frame(now) {
    const dt = lastTime ? Math.min(now - lastTime, 50) : 16;
    lastTime = now;

    ctx.clearRect(0, 0, W, H);

    drawGrid();
    drawCursorGlow();
    drawHubConnections();
    drawSignals();
    drawHubs(now);
    drawPackets();

    update(dt);
    raf = requestAnimationFrame(frame);
  }

  /* ── Lifecycle ───────────────────────────────────────────────────── */
  resize();
  populate();
  raf = requestAnimationFrame(frame);

  const onResize = () => {
    resize();
    if (hubs.length !== CFG.hubCount()) populate();
  };
  const onVisChange = () => {
    if (document.hidden) {
      cancelAnimationFrame(raf);
      raf = null;
    } else if (!raf) {
      lastTime = null;
      raf = requestAnimationFrame(frame);
    }
  };

  window.addEventListener("resize", onResize);
  document.addEventListener("mousemove", onMouse);
  document.addEventListener("mouseleave", onMouseLeave);
  document.addEventListener("visibilitychange", onVisChange);

  return () => {
    cancelAnimationFrame(raf);
    window.removeEventListener("resize", onResize);
    document.removeEventListener("mousemove", onMouse);
    document.removeEventListener("mouseleave", onMouseLeave);
    document.removeEventListener("visibilitychange", onVisChange);
  };
}

/**
 * Mount the particle network inside a specific container element.
 * @param {string} selector — CSS selector for the container (e.g. "#producto")
 */
export function mountParticleNetwork(selector = "#producto") {
  if (REDUCED) return;
  const container = document.querySelector(selector);
  if (!container) return;

  container.style.position = "relative";
  container.style.overflow = "hidden";

  const canvas = document.createElement("canvas");
  canvas.id = "particle-canvas";
  Object.assign(canvas.style, {
    position: "absolute",
    top: "0",
    left: "0",
    width: "100%",
    height: "100%",
    pointerEvents: "none",
    zIndex: "0",
  });
  container.prepend(canvas);

  // Ensure content sits above the canvas
  for (const child of container.children) {
    if (child !== canvas) {
      child.style.position = child.style.position || "relative";
      child.style.zIndex = "1";
    }
  }

  init(canvas, container);
}
