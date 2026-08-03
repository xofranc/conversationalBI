import './styles.css';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

const REDUCED = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const SVGNS = 'http://www.w3.org/2000/svg';

/* ── Datos de la demostración: preguntas reales de la consola ──────── */
const SCENES = [
  {
    label: 'consulta · llm → sql',
    question: 'Ventas totales por ciudad',
    answer: 'Bogotá lidera con $4,2 M, seguida de Medellín ($3,1 M) y Cali ($2,4 M).',
    receipt: {
      meta: 'recibo · 0.42s',
      badge: 'kimi-k2.7-code',
      badgeClass: 'model',
      code: 'SELECT ciudad, SUM(monto) AS total\nFROM ventas\nGROUP BY ciudad\nORDER BY total DESC;',
    },
    viz: 'bars',
  },
  {
    label: 'análisis · anomaly',
    question: '¿Hay anomalías en los montos?',
    answer: 'Encontré 3 montos atípicos (IsolationForest, 5% de contaminación); el mayor supera 4 veces la mediana.',
    receipt: {
      meta: 'recibo · 0.31s',
      badge: 'motor análisis',
      badgeClass: 'model',
      code: '-- método: IsolationForest sobre 2 columnas numéricas\n-- 3 filas con el score_anomalia más alto',
    },
    viz: 'scatter',
  },
  {
    label: 'análisis · forecast',
    question: 'Pronóstico de ventas para los próximos meses',
    answer: 'Tras el cierre de junio se esperan entre $3,4 M y $4,0 M mensuales el próximo trimestre.',
    receipt: {
      meta: 'recibo · 0.57s',
      badge: 'motor análisis',
      badgeClass: 'model',
      code: "-- método: ExponentialSmoothing(trend='add')\n-- banda ±1.96σ · 6 períodos hacia adelante",
    },
    viz: 'forecast',
  },
];

/* ── Utilidades DOM/SVG ─────────────────────────────────────────────── */
function el(tag, className) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  return node;
}

function svgEl(tag, attrs = {}) {
  const node = document.createElementNS(SVGNS, tag);
  Object.entries(attrs).forEach(([k, v]) => node.setAttribute(k, v));
  return node;
}

const MONO_FONT = 'JetBrains Mono, ui-monospace, monospace';

/* Catmull-Rom → Bézier: la curva serena de una serie temporal */
function smoothPath(pts) {
  if (pts.length < 3) return `M ${pts.map((p) => p.join(' ')).join(' L ')}`;
  let d = `M ${pts[0][0]} ${pts[0][1]}`;
  for (let i = 0; i < pts.length - 1; i += 1) {
    const p0 = pts[Math.max(0, i - 1)];
    const p1 = pts[i];
    const p2 = pts[i + 1];
    const p3 = pts[Math.min(pts.length - 1, i + 2)];
    const c1x = p1[0] + (p2[0] - p0[0]) / 6;
    const c1y = p1[1] + (p2[1] - p0[1]) / 6;
    const c2x = p2[0] - (p3[0] - p1[0]) / 6;
    const c2y = p2[1] - (p3[1] - p1[1]) / 6;
    d += ` C ${c1x.toFixed(1)} ${c1y.toFixed(1)} ${c2x.toFixed(1)} ${c2y.toFixed(1)} ${p2[0]} ${p2[1]}`;
  }
  return d;
}

/* ── Recibo (misma voz que el de la consola) ────────────────────────── */
function buildReceipt(r) {
  const box = el('div', 'sql-receipt');
  const bar = el('div', 'receipt-bar');
  const meta = el('span');
  meta.textContent = r.meta;
  const badge = el('span', `sql-badge ${r.badgeClass}`);
  badge.textContent = r.badge;
  bar.append(meta, badge);
  const pre = el('pre');
  pre.textContent = r.code;
  box.append(bar, pre);
  return box;
}

/* ── Figuras de la demo (SVG, viewBox 340×180) ──────────────────────── */
function buildBars(group) {
  const data = [
    ['bogotá', 4.2], ['medellín', 3.1], ['cali', 2.4], ['b/quilla', 1.6], ['b/manga', 0.9],
  ];
  const BASE = 148;
  const bars = [];
  const labels = [];

  group.appendChild(svgEl('line', { x1: 20, y1: BASE, x2: 320, y2: BASE, stroke: '#28303C', 'stroke-width': 1 }));

  data.forEach(([city, val], i) => {
    const h = (val / 4.2) * 104;
    const x = 26 + i * 62;
    const rect = svgEl('rect', {
      x, y: BASE - h, width: 40, height: h, rx: 3,
      fill: i === 0 ? '#C77B21' : '#3E8FA3',
    });
    const value = svgEl('text', {
      x: x + 20, y: BASE - h - 7, 'text-anchor': 'middle', 'font-size': 9.5,
      'font-family': MONO_FONT, fill: i === 0 ? '#C77B21' : '#A7B0BC',
    });
    value.textContent = `$${String(val).replace('.', ',')} M`;
    const name = svgEl('text', {
      x: x + 20, y: BASE + 14, 'text-anchor': 'middle', 'font-size': 8,
      'font-family': MONO_FONT, fill: '#7d8894',
    });
    name.textContent = city;
    group.append(rect, value, name);
    bars.push(rect);
    labels.push(value, name);
  });

  const tl = gsap.timeline();
  tl.from(bars, {
    scaleY: 0, transformOrigin: '50% 100%', duration: 0.55, stagger: 0.08, ease: 'power3.out',
  });
  tl.from(labels, { opacity: 0, duration: 0.3, stagger: 0.03 }, '-=0.35');
  return tl;
}

function buildScatter(group) {
  const normal = [
    [60, 128], [82, 118], [95, 132], [118, 108], [130, 122], [148, 100], [160, 112],
    [178, 92], [190, 104], [205, 86], [218, 96], [232, 80], [244, 90], [258, 74],
  ];
  const outliers = [[70, 40], [290, 52], [255, 150]];

  group.appendChild(svgEl('line', { x1: 40, y1: 155, x2: 320, y2: 155, stroke: '#28303C', 'stroke-width': 1 }));
  group.appendChild(svgEl('line', { x1: 40, y1: 25, x2: 40, y2: 155, stroke: '#28303C', 'stroke-width': 1 }));

  const dots = normal.map(([cx, cy]) => svgEl('circle', { cx, cy, r: 4.5, fill: '#3E8FA3' }));
  const marks = outliers.map(([cx, cy]) => svgEl('circle', {
    cx, cy, r: 6.5, fill: '#C77B21', stroke: '#12161C', 'stroke-width': 1.5,
  }));
  group.append(...dots, ...marks);

  const tl = gsap.timeline();
  tl.from(dots, {
    scale: 0, transformOrigin: '50% 50%', duration: 0.35, ease: 'back.out(2)',
    stagger: { each: 0.035, from: 'random' },
  });
  tl.from(marks, {
    scale: 0, transformOrigin: '50% 50%', duration: 0.5, ease: 'back.out(2.5)', stagger: 0.12,
  }, '-=0.1');
  return tl;
}

function buildForecast(group) {
  const realY = [118, 110, 114, 102, 96, 100, 88, 82, 86, 72, 66, 58];
  const predY = [54, 50, 47, 44, 42, 40];
  const x0 = 44;
  const step = 17.6;
  const realPts = realY.map((y, i) => [x0 + i * step, y]);
  const splitX = x0 + (realY.length - 1) * step;
  const predPts = [[splitX, realY[realY.length - 1]], ...predY.map((y, i) => [x0 + (realY.length + i) * step, y])];

  // Banda de confianza: se ensancha hacia el futuro
  const upper = predPts.map(([x, y], i) => [x, y - (5 + i * 1.5)]);
  const lower = predPts.map(([x, y], i) => [x, y + (5 + i * 1.5)]).reverse();
  const band = svgEl('polygon', {
    points: [...upper, ...lower].map((p) => p.join(',')).join(' '),
    fill: 'rgba(199, 123, 33, 0.14)',
  });

  const splitLine = svgEl('line', {
    x1: splitX, y1: 30, x2: splitX, y2: 150, stroke: '#28303C', 'stroke-width': 1, 'stroke-dasharray': '3 4',
  });
  const realTag = svgEl('text', { x: splitX - 8, y: 24, 'text-anchor': 'end', 'font-size': 8.5, 'font-family': MONO_FONT, fill: '#3E8FA3' });
  realTag.textContent = 'real';
  const predTag = svgEl('text', { x: splitX + 8, y: 24, 'font-size': 8.5, 'font-family': MONO_FONT, fill: '#C77B21' });
  predTag.textContent = 'pronóstico';

  const realPath = svgEl('path', {
    d: smoothPath(realPts), fill: 'none', stroke: '#3E8FA3', 'stroke-width': 2.5, 'stroke-linecap': 'round',
  });
  const predPath = svgEl('path', {
    d: smoothPath(predPts), fill: 'none', stroke: '#C77B21', 'stroke-width': 2.5,
    'stroke-linecap': 'round', 'stroke-dasharray': '6 5',
  });
  const dots = realPts.map(([cx, cy]) => svgEl('circle', { cx, cy, r: 2.5, fill: '#3E8FA3' }));

  group.append(band, splitLine, realTag, predTag, realPath, predPath, ...dots);

  const tl = gsap.timeline();
  tl.set(realPath, {
    strokeDasharray: () => realPath.getTotalLength(),
    strokeDashoffset: () => realPath.getTotalLength(),
  });
  tl.to(realPath, { strokeDashoffset: 0, duration: 0.95, ease: 'power2.inOut' });
  tl.from(dots, {
    scale: 0, transformOrigin: '50% 50%', duration: 0.25, stagger: 0.03, ease: 'back.out(2)',
  }, '-=0.6');
  tl.from([splitLine, realTag, predTag], { opacity: 0, duration: 0.3 }, '-=0.1');
  tl.from(band, { opacity: 0, duration: 0.45 }, '-=0.05');
  tl.from(predPath, { opacity: 0, duration: 0.5, ease: 'power2.out' }, '-=0.25');
  return tl;
}

const VIZ = { bars: buildBars, scatter: buildScatter, forecast: buildForecast };

/* ── Una escena completa: pregunta → respuesta → recibo → figura ────── */
function sceneTimeline(scene, chat, svg, sceneLabel) {
  const userWrap = el('div', 'message-wrapper w-full items-end');
  const userBubble = el('div', 'chat-message user');
  const textSpan = el('span');
  const caret = el('span', 'caret');
  userBubble.append(textSpan, caret);
  userWrap.appendChild(userBubble);

  const aiWrap = el('div', 'message-wrapper w-full items-start');
  const aiBubble = el('div', 'chat-message ai');
  aiBubble.textContent = scene.answer;
  const receipt = buildReceipt(scene.receipt);
  aiWrap.append(aiBubble, receipt);

  const vizGroup = svgEl('g');

  const tl = gsap.timeline();
  tl.call(() => {
    sceneLabel.textContent = `// ${scene.label}`;
    chat.appendChild(userWrap);
  });
  tl.from(userWrap, { y: 10, opacity: 0, duration: 0.28, ease: 'power2.out' });

  const typer = { n: 0 };
  tl.to(typer, {
    n: scene.question.length,
    duration: Math.min(1.5, scene.question.length * 0.034),
    ease: 'none',
    onUpdate: () => { textSpan.textContent = scene.question.slice(0, Math.round(typer.n)); },
  });

  tl.call(() => { caret.remove(); chat.appendChild(aiWrap); }, null, '+=0.4');
  tl.from(aiBubble, { y: 10, opacity: 0, duration: 0.3, ease: 'power2.out' });
  tl.from(receipt, { y: 8, opacity: 0, duration: 0.3, ease: 'power2.out' }, '-=0.12');
  tl.call(() => svg.appendChild(vizGroup), null, '+=0.2');
  tl.add(VIZ[scene.viz](vizGroup));

  // Tiempo de lectura y transición a la siguiente escena
  tl.to({}, { duration: 2.6 });
  tl.to([userWrap, aiWrap], { opacity: 0, y: -8, duration: 0.35, ease: 'power2.in' });
  tl.to(vizGroup, { opacity: 0, duration: 0.3 }, '<');
  tl.call(() => { userWrap.remove(); aiWrap.remove(); vizGroup.remove(); });
  return tl;
}

/* Estado final estático (moción reducida): la escena ya resuelta */
function renderStaticScene(scene, chat, svg, sceneLabel) {
  sceneLabel.textContent = `// ${scene.label}`;
  const userWrap = el('div', 'message-wrapper w-full items-end');
  const userBubble = el('div', 'chat-message user');
  userBubble.textContent = scene.question;
  userWrap.appendChild(userBubble);
  const aiWrap = el('div', 'message-wrapper w-full items-start');
  const aiBubble = el('div', 'chat-message ai');
  aiBubble.textContent = scene.answer;
  aiWrap.append(aiBubble, buildReceipt(scene.receipt));
  chat.append(userWrap, aiWrap);
  const vizGroup = svgEl('g');
  svg.appendChild(vizGroup);
  VIZ[scene.viz](vizGroup).progress(1);
}

/* ── Orquestación ───────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  const chat = document.getElementById('demo-chat');
  const svg = document.getElementById('demo-svg');
  const sceneLabel = document.getElementById('demo-scene');

  // Entrada del hero
  if (!REDUCED) {
    const intro = gsap.timeline({ defaults: { ease: 'power3.out' } });
    intro
      .from('[data-hero-line]', { y: 36, opacity: 0, duration: 0.85, stagger: 0.12 }, 0.1)
      .from('[data-hero]', { y: 22, opacity: 0, duration: 0.7, stagger: 0.09 }, 0.25);
  }

  // La consola en miniatura, en loop; en pausa cuando la pestaña no se ve
  if (REDUCED) {
    renderStaticScene(SCENES[0], chat, svg, sceneLabel);
  } else {
    const master = gsap.timeline({ repeat: -1, delay: 1.1 });
    SCENES.forEach((scene) => master.add(sceneTimeline(scene, chat, svg, sceneLabel)));
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) master.pause();
      else master.play();
    });
  }

  // Cinta de preguntas: deriva continua, se detiene bajo el cursor
  const track = document.getElementById('marquee-track');
  if (!REDUCED && track) {
    const drift = gsap.to(track, { xPercent: -50, ease: 'none', duration: 28, repeat: -1 });
    const strip = track.closest('.marquee');
    strip.addEventListener('mouseenter', () => drift.pause());
    strip.addEventListener('mouseleave', () => drift.play());
  }

  if (!REDUCED) {
    // Revelados al hacer scroll
    gsap.utils.toArray('[data-reveal]').forEach((node) => {
      gsap.from(node, {
        y: 26, opacity: 0, duration: 0.7, ease: 'power3.out',
        scrollTrigger: { trigger: node, start: 'top 86%', once: true },
      });
    });
    gsap.utils.toArray('[data-reveal-group]').forEach((group) => {
      gsap.from(group.children, {
        y: 24, opacity: 0, duration: 0.65, ease: 'power3.out', stagger: 0.1,
        scrollTrigger: { trigger: group, start: 'top 84%', once: true },
      });
    });

    // El sello del recibo: una rúbrica que cae sobre el artefacto
    gsap.from('#receipt-stamp', {
      scale: 2.4, opacity: 0, rotation: 6, duration: 0.45, ease: 'back.out(2.2)',
      scrollTrigger: { trigger: '.receipt-artifact', start: 'top 72%', once: true },
    });
  }

  // Cifras del sistema: conteo al entrar en pantalla
  gsap.utils.toArray('[data-count]').forEach((node) => {
    const target = Number(node.dataset.count);
    if (REDUCED) {
      node.textContent = String(target);
      return;
    }
    const counter = { n: 0 };
    gsap.to(counter, {
      n: target,
      duration: 1.1,
      ease: 'power2.out',
      snap: { n: 1 },
      onUpdate: () => { node.textContent = String(Math.round(counter.n)); },
      scrollTrigger: { trigger: node, start: 'top 88%', once: true },
    });
  });
});
