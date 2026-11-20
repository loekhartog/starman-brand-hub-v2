/*
  Thinking orbs — <thinking-orb state="thinking" size="56"></thinking-orb>

  A small canvas component that draws an orb made of dots. Each state is a
  different arrangement and motion of the same dots, so changing the `state`
  attribute morphs one into the next.

  Attributes
    state  idle | thinking | working | searching | listening | planning | solving | shaping
    size   diameter in px (default 48)
  Colour   inherits the CSS `color` of the element.
*/
(() => {
  const TAU = Math.PI * 2;
  const hash = n => { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
  const ease = k => k * k * (3 - 2 * k);
  const clamp = k => Math.max(0, Math.min(1, k));
  const sph = (lat, lon, r = 1) => { const c = Math.cos(lat) * r; return [c * Math.sin(lon), Math.sin(lat) * r, c * Math.cos(lon)]; };
  const rotX = (p, a) => { const c = Math.cos(a), s = Math.sin(a); return [p[0], p[1] * c - p[2] * s, p[1] * s + p[2] * c]; };
  const rotY = (p, a) => { const c = Math.cos(a), s = Math.sin(a); return [p[0] * c + p[2] * s, p[1], -p[0] * s + p[2] * c]; };
  const rotZ = (p, a) => { const c = Math.cos(a), s = Math.sin(a); return [p[0] * c - p[1] * s, p[0] * s + p[1] * c, p[2]]; };
  const grid = (i, N) => {
    const rows = Math.max(5, Math.round(Math.sqrt(N / 2))), cols = Math.ceil(N / rows);
    const r = Math.floor(i / cols), c = i % cols;
    const lat = ((r + .5) / rows - .5) * Math.PI, crowd = Math.cos(lat);
    // thin the rows near the poles so the dots keep an even spacing
    const on = crowd > .6 || (crowd > .3 ? c % 2 === 0 : c % 4 === 0) ? 1 : 0;
    return { v: (r + .5) / rows, lat, lon: (c + (r % 2) * .5) / cols * TAU, on };
  };
  const fib = (i, N) => { const y = 1 - (i + .5) / N * 2, r = Math.sqrt(1 - y * y), a = i * 2.39996323; return [Math.cos(a) * r, y, Math.sin(a) * r]; };

  // a loose cloud: every dot on its own tilted orbit
  const cloud = (i, t) => {
    const rr = .3 + .68 * hash(i), sp = (.35 + hash(i + 9) * 1.1) * (hash(i + 5) > .5 ? 1 : -1), a = hash(i + 3) * TAU + t * sp;
    return rotY(rotX([Math.cos(a) * rr, Math.sin(a) * rr, 0], hash(i + 1) * Math.PI), hash(i + 2) * Math.PI);
  };

  // outline shapes for "shaping", walked by arc length from the top centre
  const outline = [
    u => [Math.sin(u * TAU), -Math.cos(u * TAU)],
    u => { const s = ((u + .125) % 1) * 4, k = Math.floor(s), f = (s - k) * 2 - 1, q = .8; return [[f * q, -q], [q, f * q], [-f * q, q], [-q, -f * q]][k]; },
    u => { const P = [[0, -1], [.92, .62], [-.92, .62]], s = (u % 1) * 3, k = Math.floor(s), f = s - k, a = P[k], b = P[(k + 1) % 3]; return [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f]; },
  ];

  // each state: (i, N, t) -> [x, y, z, dotScale, alpha], coordinates in a unit sphere
  const STATES = {
    idle(i, N, t) {
      const big = N >= 150, M = big ? 46 : 16, K = big ? 3 : 1, j = i % M, k = Math.floor(i / M) % K;
      const a = j / M * TAU + t * .3, r = .86 + .07 * Math.sin(a * 3 + t * 1.6) + .05 * Math.sin(a * 2 - t * 1.1) + (k - (K - 1) / 2) * .055;
      return [Math.cos(a) * r, Math.sin(a) * r, .6, big ? .6 : .8, i < M * K ? 1 : 0];
    },
    // a tilted crown of fine vertical strokes whose rim rises and falls as it turns
    thinking(i, N, t) {
      const cols = N < 80 ? 14 : N < 200 ? 30 : 46, rows = Math.floor(N / cols), c = i % cols, r = Math.floor(i / cols) / Math.max(1, rows - 1);
      const lon = c / cols * TAU + t * .7, mid = .12 + .2 * Math.sin(lon * 2 - t * 1.3);
      let p = sph(mid + (r - .5) * (N < 80 ? .5 : .62), lon);
      p = rotZ(rotX(p, .5 + .18 * Math.sin(t * .8)), .22 * Math.cos(t * .8));
      return [p[0], -p[1], p[2], N < 80 ? .8 : N < 200 ? .78 : .6, i < cols * rows ? 1 : 0];
    },
    working(i, N, t) {
      const p = cloud(i, t), on = hash(i + 13) < (N < 80 ? 14 : 40) / N ? 1 : 0;
      return [p[0], p[1], p[2], .45 + 1.0 * hash(i + 11) ** 2, on * (.55 + .45 * (.5 + .5 * Math.sin(t * (2 + 3 * hash(i + 7)) + i)))];
    },
    searching(i, N, t) {
      const g = grid(i, N), p = rotX(sph(g.lat, g.lon + t * .35), .4);
      const lit = Math.max(0, p[0] * Math.sin(t * 1.5) + p[1] * .25 * Math.sin(t * .7) + p[2] * Math.cos(t * 1.5)) ** 3;
      return [p[0], p[1], p[2], .6 + 1.0 * lit, g.on * (.68 + .32 * lit)];
    },
    listening(i, N, t) {
      const g = grid(i, N), pulse = Math.sin(t * 3.2 - g.v * 5.5), p = rotX(sph(g.lat, g.lon + t * .25, .9 + .1 * pulse), .3);
      return [p[0], p[1], p[2], .65 + .5 * Math.max(0, pulse), g.on * (.55 + .45 * pulse)];
    },
    planning(i, N, t) {
      const M = N < 80 ? 6 : 10, per = Math.floor(N / M), m = i % M, row = Math.floor(i / M), k = row / Math.max(1, per - 1);
      const w = .5 + .5 * Math.sin(k * 6 - t * 3 + m * .7), p = rotX(sph((k - .5) * Math.PI * .9, m / M * TAU + t * .5), .2);
      return [p[0], p[1], p[2], .5 + .8 * w, i < M * per && (N < 80 || row % 2 === 0) ? .35 + .65 * w : 0];
    },
    solving(i, N, t) {
      const ph = (t * .3) % 1, f = ph < .45 ? ease(ph / .45) : ph < .75 ? 1 : 1 - ease((ph - .75) / .25);
      const a = cloud(i, t), b = rotX(rotY(fib(i, N), t * .5), .3);
      return [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f, .5 + .4 * hash(i + 11), .45 + .55 * f * (.6 + .4 * hash(i + 4))];
    },
    shaping(i, N, t) {
      const M = N < 80 ? 20 : 32, u = (i % M) / M, s = t * .55, k = Math.floor(s) % 3, f = ease(clamp(((s % 1) - .5) / .5));
      const a = outline[k](u), b = outline[(k + 1) % 3](u), q = .86;
      return [(a[0] + (b[0] - a[0]) * f) * q, (a[1] + (b[1] - a[1]) * f) * q, .5, .8, i < M ? 1 : 0];
    },
  };

  const still = matchMedia('(prefers-reduced-motion: reduce)');
  const live = new Set();
  let running = false;
  function loop(now) {
    live.forEach(o => o.draw(now / 1000));
    running = live.size > 0;
    if (running) requestAnimationFrame(loop);
  }
  const kick = () => { if (!running && live.size) { running = true; requestAnimationFrame(loop); } };

  class ThinkingOrb extends HTMLElement {
    static observedAttributes = ['state', 'size'];
    #cv = document.createElement('canvas');
    #from = null; #t0 = 0; #state = 'idle'; #seen; #color = '#fff'; #tick = 0; #off = Math.random() * 20;

    constructor() {
      super();
      this.attachShadow({ mode: 'open' }).innerHTML = '<style>:host{display:inline-block;flex:none;vertical-align:middle;line-height:0}canvas{display:block}</style>';
      this.shadowRoot.append(this.#cv);
      this.#seen = new IntersectionObserver(([e]) => { e.isIntersecting ? live.add(this) : live.delete(this); kick(); });
    }
    connectedCallback() {
      if (!this.hasAttribute('role')) { this.setAttribute('role', 'img'); this.setAttribute('aria-label', this.#state); }
      this.#resize(); this.#seen.observe(this);
    }
    disconnectedCallback() { this.#seen.disconnect(); live.delete(this); }
    attributeChangedCallback(name, old, val) {
      if (name === 'size') return this.#resize();
      const next = STATES[val] ? val : 'idle';
      if (next === this.#state) return;
      // morph only when the state changes later, not when the element first appears
      if (old !== null) { this.#from = this.#state; this.#t0 = performance.now() / 1000; }
      this.#state = next;
      if (this.getAttribute('role') === 'img') this.setAttribute('aria-label', next);
    }
    get size() { return +this.getAttribute('size') || 48; }
    #resize() {
      const s = this.size, d = Math.min(devicePixelRatio || 1, 3);
      this.#cv.width = this.#cv.height = Math.round(s * d);
      this.#cv.style.width = this.#cv.style.height = s + 'px';
      this.draw(performance.now() / 1000);
    }
    draw(now) {
      const cv = this.#cv, ctx = cv.getContext('2d'), W = cv.width, size = this.size;
      if (this.#tick++ % 30 === 0 && this.isConnected) this.#color = getComputedStyle(this).color;
      const N = size < 28 ? 40 : size < 72 ? 150 : 322;
      const t = (still.matches ? now * .3 : now) + this.#off;
      const k = this.#from ? ease(clamp((now - this.#t0) / .7)) : 1;
      if (k >= 1) this.#from = null;
      const small = size < 28, R = W * (small ? .42 : .4), base = Math.max(W * .015, (W / size) * (small ? .95 : 1));
      ctx.clearRect(0, 0, W, W);
      ctx.fillStyle = this.#color;
      for (let i = 0; i < N; i++) {
        let p = STATES[this.#state](i, N, t);
        if (this.#from) { const q = STATES[this.#from](i, N, t); p = p.map((v, j) => q[j] + (v - q[j]) * k); }
        const depth = (p[2] + 1) / 2, a = p[4] * (small ? .5 + .5 * depth : size < 100 ? .58 + .42 * depth : .26 + .74 * depth ** 1.3);
        if (a < .02) continue;
        ctx.globalAlpha = Math.min(1, a);
        ctx.beginPath();
        ctx.arc(W / 2 + p[0] * R, W / 2 + p[1] * R, base * p[3] * (.6 + .4 * depth), 0, TAU);
        ctx.fill();
      }
    }
  }
  customElements.define('thinking-orb', ThinkingOrb);
  window.ThinkingOrb = { states: Object.keys(STATES) };
})();
