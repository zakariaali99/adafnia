/* Adafnia public site behaviour: header, mobile menu, intro, scroll reveals, size picker. */
(function () {
  'use strict';

  var root = document.documentElement;
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var hasGsap = typeof window.gsap !== 'undefined';

  /* ---------- header: transparent over the hero, solid after scrolling ---------- */
  var header = document.getElementById('siteHeader');
  function setHeader() { header.classList.toggle('solid', window.scrollY > 40); }
  window.addEventListener('scroll', setHeader, { passive: true });
  setHeader();

  /* ---------- mobile menu ---------- */
  var menuBtn = document.getElementById('menuBtn');
  function closeMenu(focusButton) {
    document.body.classList.remove('nav-open');
    menuBtn.setAttribute('aria-expanded', 'false');
    if (focusButton) menuBtn.focus();
  }
  menuBtn.addEventListener('click', function () {
    var open = document.body.classList.toggle('nav-open');
    menuBtn.setAttribute('aria-expanded', String(open));
  });
  document.querySelectorAll('#mainNav a').forEach(function (a) {
    a.addEventListener('click', function () { closeMenu(false); });
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && document.body.classList.contains('nav-open')) closeMenu(true);
  });

  /* ---------- scroll reveals ---------- */
  function startMotion() {
    if (!hasGsap || reduce) { root.classList.add('no-motion'); return; }
    gsap.registerPlugin(ScrollTrigger);
    var heroImg = document.querySelector('.hero-bg img');
    if (heroImg) {
      gsap.to(heroImg, { scale: 1, duration: 2.2, ease: 'power2.out' });
      gsap.to(heroImg, { yPercent: 8, ease: 'none', scrollTrigger: { trigger: '.hero', start: 'top top', end: 'bottom top', scrub: true } });
    }
    ScrollTrigger.batch('.rv', {
      start: 'top 92%', once: true,
      onEnter: function (els) { gsap.to(els, { opacity: 1, y: 0, duration: .9, ease: 'power3.out', stagger: .08 }); }
    });
  }

  /* ---------- intro (homepage only, once per session) ---------- */
  var intro = document.getElementById('intro');
  var params = new URLSearchParams(window.location.search);
  var seen = false;
  try { seen = sessionStorage.getItem('adafnia-intro') === '1'; } catch (e) { /* storage blocked */ }
  var playIntro = intro && hasGsap && !reduce && !params.has('nointro') && (params.has('intro') || !seen);

  if (!playIntro) {
    root.classList.add('no-intro');
    if (intro) intro.remove();
    startMotion();
  } else {
    try { sessionStorage.setItem('adafnia-intro', '1'); } catch (e) { /* storage blocked */ }
    document.body.style.overflow = 'hidden';
    var ripples = gsap.utils.toArray('.rp');
    var mark = document.getElementById('introMark');
    var headMark = document.getElementById('headerMark');
    var delta;
    gsap.set(headMark, { opacity: 0 });
    gsap.set('#drop1', { x: 282, y: -140, scale: 1.7, transformOrigin: '50% 100%' });
    gsap.set('#drop2', { x: 322, y: -220, scale: 1.7, transformOrigin: '50% 100%' });

    var finish = function () {
      gsap.set(headMark, { opacity: 1 });
      gsap.to(intro, { opacity: 0, duration: .2, onComplete: function () { intro.remove(); } });
      document.body.style.overflow = '';
      startMotion();
    };

    gsap.timeline({ defaults: { ease: 'power2.out' }, onComplete: finish })
      .to('#drop1', { opacity: 1, duration: .15 })
      .to('#drop1', { y: 410, duration: .5, ease: 'power2.in' }, '<')
      .to('#drop1', { scaleY: .4, opacity: 0, duration: .12 }, '>')
      .fromTo(ripples.slice(0, 2), { attr: { rx: 10, ry: 3 }, opacity: .9 }, { attr: { rx: 220, ry: 44 }, opacity: 0, duration: 1.1, stagger: .16, ease: 'power1.out' }, '<')
      .to('#drop2', { opacity: 1, duration: .15 }, '-=1.05')
      .to('#drop2', { y: 405, duration: .5, ease: 'power2.in' }, '<')
      .to('#drop2', { scaleY: .4, opacity: 0, duration: .12 }, '>')
      .fromTo(ripples.slice(2), { attr: { rx: 10, ry: 3 }, opacity: .9 }, { attr: { rx: 260, ry: 52 }, opacity: 0, duration: 1.2, stagger: .16, ease: 'power1.out' }, '<')
      .to(mark, { clipPath: 'inset(0% 0 0 0)', duration: 1, ease: 'power2.inOut' }, '-=1.1')
      .to('#introName', { opacity: 1, duration: .4 }, '-=.3')
      .to('#introName', { opacity: 0, duration: .25 }, '+=.5')
      .add(function () {
        var from = mark.getBoundingClientRect();
        var to = headMark.getBoundingClientRect();
        delta = {
          x: (to.left + to.width / 2) - (from.left + from.width / 2),
          y: (to.top + to.height / 2) - (from.top + from.height / 2),
          s: to.height / from.height
        };
      })
      .to(mark, { x: function () { return delta.x; }, y: function () { return delta.y; }, scale: function () { return delta.s; }, duration: .8, ease: 'power3.inOut' })
      .to(intro, { backgroundColor: 'rgba(255,255,255,0)', duration: .45 }, '-=.45');
  }

  /* ---------- size picker (product page) ---------- */
  var dataEl = document.getElementById('variantData');
  if (!dataEl) return;
  var variants = JSON.parse(dataEl.textContent);
  var picker = document.getElementById('sizePicker');
  var labels = JSON.parse(document.getElementById('pickerLabels').textContent);
  var num = function (v) { return v === null || v === '' ? null : Number(v); };
  var fmt = function (v, digits) { return v === null ? '—' : v.toFixed(digits); };
  var diameters = Array.from(new Set(variants.map(function (v) { return num(v.d); }))).sort(function (a, b) { return a - b; });
  var pressures = Array.from(new Set(variants.map(function (v) { return num(v.p); }).filter(function (p) { return p !== null; }))).sort(function (a, b) { return a - b; });
  var state = {
    d: diameters.indexOf(110) >= 0 ? 110 : diameters[Math.floor(diameters.length / 2)],
    p: pressures.indexOf(16) >= 0 ? 16 : pressures[pressures.length - 1]
  };
  var find = function (d, p) { return variants.find(function (v) { return num(v.d) === d && (p === undefined || num(v.p) === p); }); };

  function chips(el, values, unit, key) {
    el.innerHTML = values.map(function (v) {
      return '<button type="button" class="chip" data-v="' + v + '">' + v + (unit ? ' ' + unit : '') + '</button>';
    }).join('');
    el.addEventListener('click', function (e) {
      var b = e.target.closest('button');
      if (!b) return;
      state[key] = Number(b.dataset.v);
      render();
    });
  }
  var diaEl = document.getElementById('pickDia');
  var pnEl = document.getElementById('pickPn');
  chips(diaEl, diameters, '', 'd');
  if (pressures.length) chips(pnEl, pressures, labels.bar, 'p');
  else pnEl.closest('.picker').hidden = true;

  function render() {
    diaEl.querySelectorAll('button').forEach(function (b) { b.setAttribute('aria-pressed', String(Number(b.dataset.v) === state.d)); });
    pnEl.querySelectorAll('button').forEach(function (b) {
      var p = Number(b.dataset.v);
      b.setAttribute('aria-pressed', String(p === state.p));
      b.classList.toggle('dim', !find(state.d, p));
    });
    var v = pressures.length ? find(state.d, state.p) : find(state.d);
    document.getElementById('rTitle').innerHTML = '<bdi>Ø ' + state.d + '</bdi> ' + labels.mm + (pressures.length ? ' · <bdi>' + state.p + '</bdi> ' + labels.bar : '');
    document.getElementById('rSub').textContent = v && v.sdr ? 'SDR ' + num(v.sdr) : '';
    document.getElementById('rValues').hidden = !v;
    document.getElementById('rNA').hidden = !!v;
    if (v) {
      document.getElementById('rWall').innerHTML = fmt(num(v.wall), 1) + '<small>' + labels.mm + '</small>';
      var inner = num(v.wall) === null ? null : state.d - 2 * num(v.wall);
      document.getElementById('rInner').innerHTML = fmt(inner, 1) + '<small>' + labels.mm + '</small>';
      var w = num(v.weight);
      document.getElementById('rWeight').innerHTML = (w === null ? '—' : w < 1 ? w.toFixed(3) : w.toFixed(2)) + '<small>' + labels.kgm + '</small>';
      var msg = labels.waMsg + ' ' + labels.product + ' Ø ' + state.d + ' ' + labels.mm + (pressures.length ? labels.sep + state.p + ' ' + labels.bar : '') + (v.sdr ? labels.sep + 'SDR ' + num(v.sdr) : '');
      var wa = document.getElementById('rWa');
      if (wa) wa.href = 'https://wa.me/' + labels.wa + '?text=' + encodeURIComponent(msg);
      document.getElementById('rQuote').href = labels.contact + '?product=' + v.product + '&variant=' + v.id;
    }
    document.querySelectorAll('#sizesTable tbody tr').forEach(function (tr) {
      tr.classList.toggle('on', Number(tr.dataset.d) === state.d && (!pressures.length || Number(tr.dataset.p) === state.p));
    });
  }
  document.querySelectorAll('#sizesTable tbody tr').forEach(function (tr) {
    tr.addEventListener('click', function () {
      state.d = Number(tr.dataset.d);
      if (tr.dataset.p) state.p = Number(tr.dataset.p);
      render();
      picker.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' });
    });
  });
  render();
})();
