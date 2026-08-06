/**
 * Architecture diagram — interactive SVG flow
 * Renders a data-flow diagram into any container with the given selector.
 */

import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

const NS = 'http://www.w3.org/2000/svg';

const COLORS = {
  rail: '#12161C',
  railLine: '#28303C',
  petrol: '#0E5E6F',
  teal: '#3E8FA3',
  amber: '#C77B21',
  red: '#B3402E',
  white: '#F4F6F9',
  soft: '#A9B4C2',
};

const NODES = [
  {
    id: 'clients',
    label: 'Clientes',
    sub: 'Web · iOS',
    x: 0,
    y: 0,
    stroke: COLORS.teal,
    fill: COLORS.rail,
    icon: clientIcon,
    detail: 'Interfaz de consola en Vite + Chart.js y app móvil en SwiftUI con Charts.',
  },
  {
    id: 'auth',
    label: 'Supabase Auth',
    sub: 'JWT RS256',
    x: 1,
    y: 0,
    stroke: COLORS.amber,
    fill: COLORS.rail,
    icon: shieldIcon,
    detail: 'Autenticación sin contraseñas propias: validación de JWT contra JWKS público de Supabase.',
  },
  {
    id: 'api',
    label: 'Django API',
    sub: 'Render · LLMClient',
    x: 2,
    y: 0,
    stroke: COLORS.teal,
    fill: COLORS.petrol,
    icon: serverIcon,
    detail: 'Backend con Django REST. Enruta intenciones a SQL, pronósticos, anomalías y segmentación.',
  },
  {
    id: 'postgres',
    label: 'Supabase Postgres',
    sub: 'schema ds_<id>',
    x: 3,
    y: 0,
    stroke: COLORS.teal,
    fill: COLORS.rail,
    icon: databaseIcon,
    detail: 'Cada dataset aislado en su propio schema. Consultas de análisis corren bajo rol de solo lectura.',
  },
  {
    id: 'engine',
    label: 'Motor de análisis',
    sub: 'statsmodels · scikit-learn',
    x: 4,
    y: 0,
    stroke: COLORS.amber,
    fill: COLORS.petrol,
    icon: chipIcon,
    detail: 'Ejecuta SQL generado, pronósticos, detección de anomalías y análisis de factores.',
  },
  {
    id: 'receipt',
    label: 'Recibo verificable',
    sub: 'SQL · método · tiempo',
    x: 5,
    y: 0,
    stroke: COLORS.teal,
    fill: COLORS.rail,
    icon: receiptIcon,
    detail: 'Cada respuesta trae su trazabilidad: SQL, motor estadístico, parámetros y tiempo de ejecución.',
  },
];

const EDGES = [
  { from: 'clients', to: 'auth' },
  { from: 'auth', to: 'api' },
  { from: 'api', to: 'postgres', label: 'consulta' },
  { from: 'postgres', to: 'engine', label: 'datos' },
  { from: 'engine', to: 'api', label: 'resultado', curve: 'bottom' },
  { from: 'api', to: 'receipt', label: 'respuesta' },
  { from: 'receipt', to: 'clients', curve: 'bottom' },
];

function svgEl(type, attrs = {}) {
  const el = document.createElementNS(NS, type);
  Object.entries(attrs).forEach(([k, v]) => el.setAttribute(k, v));
  return el;
}

function clientIcon(g) {
  g.appendChild(svgEl('rect', { x: 6, y: 6, width: 18, height: 14, rx: 2, fill: 'none', stroke: 'currentColor', 'stroke-width': 1.5 }));
  g.appendChild(svgEl('path', { d: 'M10 28h10M15 20v8', fill: 'none', stroke: 'currentColor', 'stroke-width': 1.5, 'stroke-linecap': 'round' }));
  g.appendChild(svgEl('rect', { x: 22, y: 2, width: 8, height: 14, rx: 2, fill: 'none', stroke: 'currentColor', 'stroke-width': 1.5 }));
}

function shieldIcon(g) {
  g.appendChild(svgEl('path', { d: 'M15 4l9 4v6c0 5.5-4 10-9 11-5-1-9-5.5-9-11V8l9-4z', fill: 'none', stroke: 'currentColor', 'stroke-width': 1.5, 'stroke-linejoin': 'round' }));
  g.appendChild(svgEl('path', { d: 'M11 15l3 3 5-6', fill: 'none', stroke: 'currentColor', 'stroke-width': 1.5, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }));
}

function serverIcon(g) {
  g.appendChild(svgEl('rect', { x: 4, y: 6, width: 22, height: 18, rx: 2, fill: 'none', stroke: 'currentColor', 'stroke-width': 1.5 }));
  g.appendChild(svgEl('circle', { cx: 9, cy: 12, r: 1.5, fill: 'currentColor' }));
  g.appendChild(svgEl('circle', { cx: 9, cy: 18, r: 1.5, fill: 'currentColor' }));
  g.appendChild(svgEl('path', { d: 'M14 12h8M14 18h8', stroke: 'currentColor', 'stroke-width': 1.5, 'stroke-linecap': 'round' }));
}

function databaseIcon(g) {
  g.appendChild(svgEl('ellipse', { cx: 15, cy: 7, rx: 11, ry: 5, fill: 'none', stroke: 'currentColor', 'stroke-width': 1.5 }));
  g.appendChild(svgEl('path', { d: 'M4 7v12c0 2.8 4.9 5 11 5s11-2.2 11-5V7', fill: 'none', stroke: 'currentColor', 'stroke-width': 1.5 }));
  g.appendChild(svgEl('path', { d: 'M4 13c0 2.8 4.9 5 11 5s11-2.2 11-5', fill: 'none', stroke: 'currentColor', 'stroke-width': 1.5 }));
}

function chipIcon(g) {
  g.appendChild(svgEl('rect', { x: 8, y: 8, width: 14, height: 14, rx: 1, fill: 'none', stroke: 'currentColor', 'stroke-width': 1.5 }));
  g.appendChild(svgEl('path', { d: 'M12 8V5M18 8V5M12 27v-3M18 27v-3M8 12H5M8 18H5M25 12h-3M25 18h-3', stroke: 'currentColor', 'stroke-width': 1.5, 'stroke-linecap': 'round' }));
  g.appendChild(svgEl('rect', { x: 12, y: 12, width: 6, height: 6, fill: 'none', stroke: 'currentColor', 'stroke-width': 1.2 }));
}

function receiptIcon(g) {
  g.appendChild(svgEl('path', { d: 'M6 4h18l-2 4 2 4-2 4 2 4-2 4-2-2-2 2-2-2-2 2-2-2-2 2-2-4 2-4-2-4 2-4z', fill: 'none', stroke: 'currentColor', 'stroke-width': 1.5, 'stroke-linejoin': 'round' }));
  g.appendChild(svgEl('path', { d: 'M10 12h10M10 16h8M10 20h6', stroke: 'currentColor', 'stroke-width': 1.2, 'stroke-linecap': 'round' }));
}

function makeDefs() {
  const defs = svgEl('defs');

  const glow = svgEl('filter', { id: 'arch-glow', x: '-50%', y: '-50%', width: '200%', height: '200%' });
  glow.innerHTML = `
    <feGaussianBlur stdDeviation="2.5" result="blur" />
    <feComposite in="SourceGraphic" in2="blur" operator="over" />
  `;
  defs.appendChild(glow);

  const pulse = svgEl('radialGradient', { id: 'arch-pulse', cx: '50%', cy: '50%', r: '50%' });
  pulse.innerHTML = `
    <stop offset="0%" stop-color="${COLORS.teal}" stop-opacity="0.9" />
    <stop offset="100%" stop-color="${COLORS.teal}" stop-opacity="0" />
  `;
  defs.appendChild(pulse);

  return defs;
}

export function renderArchitectureDiagram(containerSelector, { theme = 'dark' } = {}) {
  const container = document.querySelector(containerSelector);
  if (!container) return;
  container.innerHTML = '';

  const isLight = theme === 'light';
  const textColor = isLight ? COLORS.rail : COLORS.white;
  const subColor = isLight ? COLORS.rail : COLORS.soft;
  const bgPanel = isLight ? '#FFFFFF' : COLORS.rail;
  const panelBorder = isLight ? '#D4DADF' : COLORS.railLine;

  const nodeW = 132;
  const nodeH = 76;
  const gapX = 44;
  const gapY = 96;
  const startX = 20;
  const startY = 40;

  const totalW = startX * 2 + NODES.length * nodeW + (NODES.length - 1) * gapX;
  const totalH = startY * 2 + nodeH + gapY;

  const svg = svgEl('svg', {
    viewBox: `0 0 ${totalW} ${totalH}`,
    class: 'arch-diagram-svg',
    role: 'img',
    'aria-label': 'Diagrama de arquitectura de ConversationalBI',
  });
  svg.style.width = '100%';
  svg.style.height = 'auto';
  svg.style.display = 'block';
  svg.appendChild(makeDefs());

  // Panel background
  const panel = svgEl('rect', {
    x: 8, y: 8, width: totalW - 16, height: totalH - 16, rx: 16,
    fill: bgPanel, stroke: panelBorder, 'stroke-width': 1,
  });
  svg.appendChild(panel);

  // Build node map
  const nodeMap = new Map();
  const nodeGroup = svgEl('g', { class: 'arch-nodes' });

  NODES.forEach((node, i) => {
    const cx = startX + i * (nodeW + gapX) + nodeW / 2;
    const cy = startY + nodeH / 2;
    nodeMap.set(node.id, { cx, cy });

    const g = svgEl('g', {
      class: 'arch-node',
      'data-id': node.id,
      transform: `translate(${cx - nodeW / 2}, ${cy - nodeH / 2})`,
      style: 'cursor: pointer;',
    });

    // Glow halo
    const halo = svgEl('rect', {
      x: -4, y: -4, width: nodeW + 8, height: nodeH + 8, rx: 18,
      fill: node.stroke, opacity: 0, class: 'arch-node-halo',
    });
    g.appendChild(halo);

    // Card
    const card = svgEl('rect', {
      width: nodeW, height: nodeH, rx: 14,
      fill: node.fill, stroke: node.stroke, 'stroke-width': 1.5,
      class: 'arch-node-card',
    });
    g.appendChild(card);

    // Icon
    const iconGroup = svgEl('g', {
      transform: `translate(14, ${nodeH / 2 - 12})`,
      fill: 'none', stroke: 'currentColor', color: node.stroke,
    });
    node.icon(iconGroup);
    g.appendChild(iconGroup);

    // Label
    const label = svgEl('text', {
      x: nodeW - 12, y: 22,
      fill: textColor, 'font-size': 12, 'font-weight': 600,
      'font-family': 'Space Grotesk, sans-serif',
      'text-anchor': 'end', class: 'arch-node-label',
    });
    label.textContent = node.label;
    g.appendChild(label);

    // Sub
    const sub = svgEl('text', {
      x: nodeW - 12, y: 40,
      fill: subColor, 'font-size': 9,
      'font-family': 'JetBrains Mono, monospace',
      'text-anchor': 'end', class: 'arch-node-sub',
    });
    sub.textContent = node.sub;
    g.appendChild(sub);

    nodeGroup.appendChild(g);
  });

  // Edges
  const edgeGroup = svgEl('g', { class: 'arch-edges', fill: 'none' });
  const edgePaths = [];

  EDGES.forEach((edge, idx) => {
    const a = nodeMap.get(edge.from);
    const b = nodeMap.get(edge.to);
    if (!a || !b) return;

    let d;
    const ax = a.cx + nodeW / 2;
    const ay = a.cy;
    const bx = b.cx - nodeW / 2;
    const by = b.cy;

    if (edge.curve === 'bottom') {
      const my = Math.max(ay, by) + gapY * 0.65;
      d = `M ${ax} ${ay} C ${ax + gapX * 0.5} ${ay}, ${ax + gapX * 0.5} ${my}, ${(ax + bx) / 2} ${my} S ${bx - gapX * 0.5} ${by}, ${bx} ${by}`;
    } else {
      d = `M ${ax} ${ay} C ${ax + gapX * 0.5} ${ay}, ${bx - gapX * 0.5} ${by}, ${bx} ${by}`;
    }

    const path = svgEl('path', {
      d, stroke: COLORS.railLine, 'stroke-width': 1.5,
      'stroke-dasharray': '4 4', class: 'arch-edge-base',
    });
    edgeGroup.appendChild(path);

    const active = svgEl('path', {
      d, stroke: COLORS.teal, 'stroke-width': 2,
      'stroke-dasharray': '6 12', 'stroke-linecap': 'round',
      opacity: 0, class: 'arch-edge-active',
    });
    edgeGroup.appendChild(active);
    edgePaths.push({ base: path, active, idx, curve: edge.curve });

    if (edge.label) {
      const mid = edge.curve === 'bottom'
        ? { x: (ax + bx) / 2, y: Math.max(ay, by) + gapY * 0.72 }
        : { x: (ax + bx) / 2, y: (ay + by) / 2 - 6 };
      const label = svgEl('text', {
        x: mid.x, y: mid.y,
        fill: subColor, 'font-size': 8,
        'font-family': 'JetBrains Mono, monospace',
        'text-anchor': 'middle',
      });
      label.textContent = edge.label;
      edgeGroup.appendChild(label);
    }
  });

  svg.appendChild(edgeGroup);
  svg.appendChild(nodeGroup);

  // Tooltip
  const tooltip = document.createElement('div');
  tooltip.className = 'arch-tooltip';
  container.appendChild(tooltip);
  container.appendChild(svg);

  // Interactions
  const nodeEls = nodeGroup.querySelectorAll('.arch-node');
  nodeEls.forEach((el) => {
    const node = NODES.find((n) => n.id === el.dataset.id);
    if (!node) return;

    el.addEventListener('mouseenter', () => {
      tooltip.innerHTML = `<strong>${node.label}</strong><span>${node.sub}</span><p>${node.detail}</p>`;
      tooltip.classList.add('is-visible');
      gsap.to(el.querySelector('.arch-node-halo'), { opacity: 0.25, duration: 0.2 });
      gsap.to(el.querySelector('.arch-node-card'), { strokeWidth: 2.5, duration: 0.2 });
    });

    el.addEventListener('mousemove', (e) => {
      const rect = container.getBoundingClientRect();
      tooltip.style.left = `${e.clientX - rect.left + 16}px`;
      tooltip.style.top = `${e.clientY - rect.top + 16}px`;
    });

    el.addEventListener('mouseleave', () => {
      tooltip.classList.remove('is-visible');
      gsap.to(el.querySelector('.arch-node-halo'), { opacity: 0, duration: 0.2 });
      gsap.to(el.querySelector('.arch-node-card'), { strokeWidth: 1.5, duration: 0.2 });
    });
  });

  // Animation
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (!prefersReduced) {
    // Entrance: staggered scale + fade of nodes
    gsap.fromTo(
      nodeEls,
      { opacity: 0, scale: 0.85, transformOrigin: 'center center' },
      {
        opacity: 1,
        scale: 1,
        duration: 0.6,
        stagger: 0.12,
        ease: 'back.out(1.4)',
        scrollTrigger: {
          trigger: container,
          start: 'top 80%',
          once: true,
        },
      }
    );

    // Edge active dashes animation
    edgePaths.forEach(({ active }) => {
      gsap.to(active, {
        strokeDashoffset: -36,
        duration: 1.4,
        repeat: -1,
        ease: 'none',
        paused: true,
      });
      gsap.to(active, {
        opacity: 1,
        duration: 0.4,
        scrollTrigger: {
          trigger: container,
          start: 'top 75%',
          once: true,
          onEnter: () => gsap.to(active, { opacity: 0.7, duration: 0.5, delay: 0.6 }),
        },
      });
    });

    // Looping pulse along the main flow
    const pulse = svgEl('circle', { r: 4, fill: 'url(#arch-pulse)', opacity: 0 });
    svg.appendChild(pulse);

    const mainFlow = [0, 1, 2, 3, 4, 5, 6]; // clients -> auth -> api -> postgres -> engine -> api -> receipt -> clients
    const flowPaths = mainFlow.map((i) => edgePaths[i]?.active).filter(Boolean);

    let currentPathIndex = 0;
    let startTime = null;
    const segmentDuration = 900;
    const pauseDuration = 220;

    function animatePulse(timestamp) {
      if (!startTime) startTime = timestamp;
      const elapsed = timestamp - startTime;
      const cycle = segmentDuration + pauseDuration;
      const phase = elapsed % cycle;
      const path = flowPaths[currentPathIndex];
      const len = path.getTotalLength();

      if (phase < segmentDuration) {
        const t = phase / segmentDuration;
        const point = path.getPointAtLength(t * len);
        pulse.setAttribute('cx', point.x);
        pulse.setAttribute('cy', point.y);
        pulse.setAttribute('opacity', 1);
      } else {
        pulse.setAttribute('opacity', 0);
        if (phase >= cycle - 16) {
          currentPathIndex = (currentPathIndex + 1) % flowPaths.length;
          startTime = null;
        }
      }
      requestAnimationFrame(animatePulse);
    }

    requestAnimationFrame(animatePulse);
  }
}
