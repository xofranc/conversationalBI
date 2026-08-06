/**
 * Architecture diagram — horizontal GSAP-powered SVG flow
 *
 * Layout: single-row nodes with top/bottom curved feedback loops.
 * All motion is driven by GSAP (no manual requestAnimationFrame).
 */

import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

const NS = 'http://www.w3.org/2000/svg';

const COLORS = {
  rail: '#12161C',
  railLine: '#28303C',
  petrol: '#0E5E6F',
  petrolDark: '#0A3F4A',
  teal: '#3E8FA3',
  amber: '#C77B21',
  amberSoft: '#D69A4F',
  white: '#F4F6F9',
  soft: '#A9B4C2',
};

const NODES = [
  {
    id: 'clients',
    label: 'Clientes',
    sub: 'Web · iOS',
    stroke: COLORS.teal,
    fill: `url(#arch-grad-client)`,
    icon: clientIcon,
    detail: 'Interfaz de consola en Vite + Chart.js y app móvil en SwiftUI con Charts.',
  },
  {
    id: 'auth',
    label: 'Supabase Auth',
    sub: 'JWT RS256',
    stroke: COLORS.amber,
    fill: `url(#arch-grad-auth)`,
    icon: shieldIcon,
    detail: 'Autenticación sin contraseñas propias: validación de JWT contra JWKS público de Supabase.',
  },
  {
    id: 'api',
    label: 'Django API',
    sub: 'Render · LLMClient',
    stroke: COLORS.teal,
    fill: `url(#arch-grad-api)`,
    icon: serverIcon,
    detail: 'Backend con Django REST. Enruta intenciones a SQL, pronósticos, anomalías y segmentación.',
  },
  {
    id: 'postgres',
    label: 'Postgres',
    sub: 'schema ds_<id>',
    stroke: COLORS.teal,
    fill: `url(#arch-grad-data)`,
    icon: databaseIcon,
    detail: 'Cada dataset aislado en su propio schema. Consultas de análisis corren bajo rol de solo lectura.',
  },
  {
    id: 'engine',
    label: 'Motor',
    sub: 'statsmodels · sklearn',
    stroke: COLORS.amber,
    fill: `url(#arch-grad-engine)`,
    icon: chipIcon,
    detail: 'Ejecuta SQL generado, pronósticos, detección de anomalías y análisis de factores.',
  },
  {
    id: 'receipt',
    label: 'Recibo',
    sub: 'SQL · método · tiempo',
    stroke: COLORS.teal,
    fill: `url(#arch-grad-receipt)`,
    icon: receiptIcon,
    detail: 'Cada respuesta trae su trazabilidad: SQL, motor estadístico, parámetros y tiempo de ejecución.',
  },
];

const EDGES = [
  { from: 'clients', to: 'auth', lane: 'center' },
  { from: 'auth', to: 'api', lane: 'center' },
  { from: 'api', to: 'postgres', lane: 'center' },
  { from: 'postgres', to: 'engine', lane: 'center' },
  { from: 'engine', to: 'api', lane: 'bottom', label: 'resultado' },
  { from: 'api', to: 'receipt', lane: 'center' },
  { from: 'receipt', to: 'clients', lane: 'top', label: 'respuesta' },
];

function svgEl(type, attrs = {}) {
  const el = document.createElementNS(NS, type);
  Object.entries(attrs).forEach(([k, v]) => el.setAttribute(k, v));
  return el;
}

function clientIcon(g) {
  g.appendChild(svgEl('rect', { x: 6, y: 8, width: 18, height: 14, rx: 2, fill: 'none', stroke: 'currentColor', 'stroke-width': 1.5 }));
  g.appendChild(svgEl('path', { d: 'M10 28h10M15 20v8', fill: 'none', stroke: 'currentColor', 'stroke-width': 1.5, 'stroke-linecap': 'round' }));
  g.appendChild(svgEl('rect', { x: 22, y: 4, width: 8, height: 14, rx: 2, fill: 'none', stroke: 'currentColor', 'stroke-width': 1.5 }));
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

  // Soft gradients
  const gradients = [
    ['arch-grad-client', '#1A2029', '#12161C'],
    ['arch-grad-auth', '#1E2219', '#12161C'],
    ['arch-grad-api', '#0E2E36', '#0A1F24'],
    ['arch-grad-data', '#1A2029', '#12161C'],
    ['arch-grad-engine', '#2A1E10', '#12161C'],
    ['arch-grad-receipt', '#1A2029', '#12161C'],
  ];
  gradients.forEach(([id, from, to]) => {
    const grad = svgEl('linearGradient', { id, x1: '0%', y1: '0%', x2: '0%', y2: '100%' });
    grad.innerHTML = `<stop offset="0%" stop-color="${from}" /><stop offset="100%" stop-color="${to}" />`;
    defs.appendChild(grad);
  });

  // Glow filter
  const glow = svgEl('filter', { id: 'arch-glow', x: '-60%', y: '-60%', width: '220%', height: '220%' });
  glow.innerHTML = `
    <feGaussianBlur stdDeviation="5" result="blur" />
    <feComposite in="SourceGraphic" in2="blur" operator="over" />
  `;
  defs.appendChild(glow);

  // Pulse gradient
  const pulse = svgEl('radialGradient', { id: 'arch-pulse', cx: '50%', cy: '50%', r: '50%' });
  pulse.innerHTML = `
    <stop offset="0%" stop-color="${COLORS.teal}" stop-opacity="1" />
    <stop offset="50%" stop-color="${COLORS.amber}" stop-opacity="0.6" />
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

  const nodeW = 210;
  const nodeH = 110;
  const gapX = 72;
  const startX = 50;
  const startY = 110;
  const cy = startY;

  const totalW = startX * 2 + NODES.length * nodeW + (NODES.length - 1) * gapX;
  const totalH = 240;

  const svg = svgEl('svg', {
    viewBox: `0 0 ${totalW} ${totalH}`,
    class: 'arch-diagram-svg',
    role: 'img',
    'aria-label': 'Diagrama de arquitectura de ConversationalBI',
  });
  svg.style.width = '100%';
  svg.style.height = 'auto';
  svg.style.display = 'block';
  svg.style.minWidth = '1100px';
  svg.appendChild(makeDefs());

  // Panel background
  const panel = svgEl('rect', {
    x: 10, y: 10, width: totalW - 20, height: totalH - 20, rx: 18,
    fill: bgPanel, stroke: panelBorder, 'stroke-width': 1,
  });
  svg.appendChild(panel);

  // Build node positions
  const nodeMap = new Map();
  const nodeGroup = svgEl('g', { class: 'arch-nodes' });

  NODES.forEach((node, i) => {
    const cx = startX + i * (nodeW + gapX) + nodeW / 2;
    nodeMap.set(node.id, { cx, cy });

    const g = svgEl('g', {
      class: 'arch-node',
      'data-id': node.id,
      transform: `translate(${cx - nodeW / 2}, ${cy - nodeH / 2})`,
      style: 'cursor: pointer;',
    });

    // Glow halo
    const halo = svgEl('rect', {
      x: -6, y: -6, width: nodeW + 12, height: nodeH + 12, rx: 20,
      fill: node.stroke, opacity: 0, class: 'arch-node-halo',
    });
    g.appendChild(halo);

    // Card
    const card = svgEl('rect', {
      width: nodeW, height: nodeH, rx: 16,
      fill: node.fill, stroke: node.stroke, 'stroke-width': 1.5,
      class: 'arch-node-card',
    });
    g.appendChild(card);

    // Icon
    const iconGroup = svgEl('g', {
      transform: `translate(20, 33) scale(1.5)`,
      fill: 'none', stroke: 'currentColor', color: node.stroke,
    });
    node.icon(iconGroup);
    g.appendChild(iconGroup);

    // Label
    const label = svgEl('text', {
      x: nodeW - 20, y: 34,
      fill: textColor, 'font-size': 16, 'font-weight': 600,
      'font-family': 'Space Grotesk, sans-serif',
      'text-anchor': 'end', class: 'arch-node-label',
    });
    label.textContent = node.label;
    g.appendChild(label);

    // Sub
    const sub = svgEl('text', {
      x: nodeW - 20, y: 58,
      fill: subColor, 'font-size': 11,
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

    const ax = a.cx + nodeW / 2;
    const ay = a.cy;
    const bx = b.cx - nodeW / 2;
    const by = b.cy;

    let d;
    let labelPos;
    if (edge.lane === 'top') {
      const my = 42;
      d = `M ${ax} ${ay - nodeH / 2} C ${ax + 60} ${my}, ${bx - 60} ${my}, ${bx} ${by - nodeH / 2}`;
      labelPos = { x: (ax + bx) / 2, y: my - 8 };
    } else if (edge.lane === 'bottom') {
      const my = totalH - 42;
      d = `M ${ax} ${ay + nodeH / 2} C ${ax + 60} ${my}, ${bx - 60} ${my}, ${bx} ${by + nodeH / 2}`;
      labelPos = { x: (ax + bx) / 2, y: my + 14 };
    } else {
      d = `M ${ax} ${ay} C ${ax + 48} ${ay}, ${bx - 48} ${by}, ${bx} ${by}`;
      labelPos = { x: (ax + bx) / 2, y: ay - 10 };
    }

    // Base dashed line
    const base = svgEl('path', {
      d, stroke: COLORS.railLine, 'stroke-width': 2,
      'stroke-dasharray': '5 5', class: 'arch-edge-base',
    });
    edgeGroup.appendChild(base);

    // Active line (drawn on scroll)
    const active = svgEl('path', {
      d, stroke: edge.lane === 'center' ? COLORS.teal : COLORS.amber,
      'stroke-width': 2.5, 'stroke-linecap': 'round',
      'stroke-dasharray': 2000, 'stroke-dashoffset': 2000,
      opacity: 0, class: 'arch-edge-active',
    });
    edgeGroup.appendChild(active);
    edgePaths.push({ base, active, d, from: edge.from, to: edge.to, labelPos, label: edge.label });

    // Arrow head
    const head = svgEl('path', {
      d: `M ${bx - 6} ${by - 4} L ${bx} ${by} L ${bx - 6} ${by + 4}`,
      fill: 'none', stroke: edge.lane === 'center' ? COLORS.teal : COLORS.amber,
      'stroke-width': 2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round',
      opacity: 0, class: 'arch-edge-head',
    });
    edgeGroup.appendChild(head);

    if (edge.label) {
      const label = svgEl('text', {
        x: labelPos.x, y: labelPos.y,
        fill: subColor, 'font-size': 10,
        'font-family': 'JetBrains Mono, monospace',
        'text-anchor': 'middle',
        opacity: 0, class: 'arch-edge-label',
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

    const halo = el.querySelector('.arch-node-halo');
    const card = el.querySelector('.arch-node-card');

    const show = (e) => {
      tooltip.innerHTML = `<strong>${node.label}</strong><span>${node.sub}</span><p>${node.detail}</p>`;
      gsap.to(tooltip, { opacity: 1, y: 0, duration: 0.2, ease: 'power2.out' });
      gsap.to(halo, { opacity: 0.22, duration: 0.2 });
      gsap.to(card, { stroke: node.stroke, strokeWidth: 2.5, duration: 0.2 });
      gsap.to(el, { scale: 1.04, transformOrigin: 'center center', duration: 0.25, ease: 'back.out(2)' });
      moveTooltip(e);
    };

    const moveTooltip = (e) => {
      const rect = container.getBoundingClientRect();
      let left = e.clientX - rect.left + 18;
      let top = e.clientY - rect.top + 18;
      const tRect = tooltip.getBoundingClientRect();
      if (left + tRect.width > rect.width) left = rect.width - tRect.width - 12;
      if (top + tRect.height > rect.height) top = e.clientY - rect.top - tRect.height - 12;
      tooltip.style.left = `${left}px`;
      tooltip.style.top = `${top}px`;
    };

    const hide = () => {
      gsap.to(tooltip, { opacity: 0, y: 6, duration: 0.2, ease: 'power2.in' });
      gsap.to(halo, { opacity: 0, duration: 0.2 });
      gsap.to(card, { stroke: node.stroke, strokeWidth: 1.5, duration: 0.2 });
      gsap.to(el, { scale: 1, duration: 0.25, ease: 'power2.out' });
    };

    el.addEventListener('mouseenter', show);
    el.addEventListener('mousemove', moveTooltip);
    el.addEventListener('mouseleave', hide);
  });

  // Animations
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (prefersReduced) {
    edgeGroup.querySelectorAll('.arch-edge-active, .arch-edge-head, .arch-edge-label').forEach((el) => el.setAttribute('opacity', 1));
    return;
  }

  // Intro: nodes slide in from left
  const introTl = gsap.timeline({
    scrollTrigger: {
      trigger: container,
      start: 'top 80%',
      once: true,
    },
  });

  introTl.from(nodeEls, {
    x: -40, opacity: 0, scale: 0.92,
    duration: 0.7, stagger: 0.1,
    ease: 'power3.out',
  });

  // Draw edges
  edgePaths.forEach(({ active, head }, i) => {
    const len = active.getTotalLength();
    gsap.set(active, { strokeDasharray: len, strokeDashoffset: len, opacity: 1 });
    introTl.to(active, {
      strokeDashoffset: 0,
      duration: 0.8,
      ease: 'power2.inOut',
    }, 0.4 + i * 0.12);
    introTl.to(head, { opacity: 1, duration: 0.2 }, '<+0.65');
  });

  // Labels fade in
  introTl.to('.arch-edge-label', { opacity: 1, duration: 0.4, stagger: 0.05 }, '-=0.4');

  // Heartbeat: nodes light up in sequence
  const heartbeatTl = gsap.timeline({
    repeat: -1, repeatDelay: 1.2,
    scrollTrigger: {
      trigger: container,
      start: 'top 75%',
      once: false,
    },
  });

  nodeEls.forEach((el) => {
    const halo = el.querySelector('.arch-node-halo');
    const card = el.querySelector('.arch-node-card');
    const node = NODES.find((n) => n.id === el.dataset.id);
    heartbeatTl
      .to(halo, { opacity: 0.3, duration: 0.25, ease: 'power2.out' }, '<')
      .to(card, { stroke: COLORS.white, strokeWidth: 2.5, duration: 0.25, ease: 'power2.out' }, '<')
      .to(halo, { opacity: 0, duration: 0.25, ease: 'power2.in' }, '+=0.15')
      .to(card, { stroke: node.stroke, strokeWidth: 1.5, duration: 0.25, ease: 'power2.in' }, '<');
  });

  // Data packets flowing along the main loop
  const mainFlow = edgePaths.filter((ep) =>
    ['clients->auth', 'auth->api', 'api->postgres', 'postgres->engine', 'engine->api', 'api->receipt', 'receipt->clients'].includes(`${ep.from}->${ep.to}`)
  );

  const packet = svgEl('circle', { r: 5, fill: 'url(#arch-pulse)', opacity: 0 });
  svg.appendChild(packet);

  const flowTl = gsap.timeline({ repeat: -1, repeatDelay: 0.6 });
  flowTl.to(packet, { opacity: 1, duration: 0.1 });

  mainFlow.forEach((ep) => {
    const len = ep.active.getTotalLength();
    const obj = { t: 0 };
    flowTl.to(obj, {
      t: 1,
      duration: 0.9,
      ease: 'none',
      onUpdate: () => {
        const p = ep.active.getPointAtLength(obj.t * len);
        packet.setAttribute('cx', p.x);
        packet.setAttribute('cy', p.y);
      },
    });
  });

  flowTl.to(packet, { opacity: 0, duration: 0.2 });
}
