import { initCtaTransition } from './ctaTransition.js';

initCtaTransition({
  linkSelector: 'a[href="/roadmap.html"]',
  destination: '/roadmap.html',
  transitionDestination: '/roadmap.html?transition=1',
});
