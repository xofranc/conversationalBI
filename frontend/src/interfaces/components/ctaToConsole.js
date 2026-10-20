import { initCtaTransition } from './ctaTransition.js';

initCtaTransition({
  linkSelector: 'a[href="/app.html?demo=true"]',
  destination: '/app.html',
  transitionDestination: '/app.html?transition=1',
});
