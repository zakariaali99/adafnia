(() => {
  'use strict';
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const menu = document.querySelector('.menu-toggle');
  const closeMenu = () => {
    const restore = document.body.classList.contains('menu-open') && document.querySelector('#navigation')?.contains(document.activeElement);
    document.body.classList.remove('menu-open');
    menu?.setAttribute('aria-expanded', 'false');
    if (restore) menu?.focus();
  };
  menu?.addEventListener('click', () => {
    const open = !document.body.classList.contains('menu-open');
    document.body.classList.toggle('menu-open', open);
    menu.setAttribute('aria-expanded', String(open));
    if (open) {
      const navigation = document.querySelector('#navigation');
      const focusFirstLink = () => {
        if (document.body.classList.contains('menu-open') && document.activeElement === menu) navigation?.querySelector('a')?.focus();
      };
      // Visibility transitions must finish before links can receive focus.
      setTimeout(focusFirstLink, reduced ? 0 : 320);
    }
  });
  document.addEventListener('keydown', (event) => { if (event.key === 'Escape') { closeMenu(); leaveIntro(); } });
  document.addEventListener('keydown', (event) => {
    if (event.key !== 'Tab' || !document.body.classList.contains('menu-open')) return;
    const controls = [...document.querySelectorAll('#navigation a, .header-actions a, .menu-toggle')].filter(element => element.getClientRects().length);
    const first = controls[0], last = controls[controls.length - 1];
    if (!first) return;
    if ((!event.shiftKey && document.activeElement === last) || (event.shiftKey && document.activeElement === first) || !controls.includes(document.activeElement)) {
      event.preventDefault();
      (event.shiftKey ? last : first).focus();
    }
  });
  document.querySelectorAll('#navigation a').forEach(link => {
    if (link.pathname === location.pathname) link.setAttribute('aria-current', 'page');
    link.addEventListener('click', closeMenu);
  });
  const intro = document.querySelector('#intro');
  let timer;
  let introInitiator;
  function leaveIntro() {
    if (!intro || intro.hidden) return;
    clearTimeout(timer);
    intro.classList.add('is-leaving');
    intro.setAttribute('aria-hidden', 'true');
    document.querySelectorAll('.skip-link, main, header, footer').forEach(element => element.removeAttribute('inert'));
    if (introInitiator && introInitiator !== document.body && introInitiator.isConnected) introInitiator.focus();
    else document.querySelector('.brand')?.focus({preventScroll:true});
    setTimeout(() => { intro.hidden = true; }, reduced ? 0 : 650);
  }
  function playIntro() {
    if (!intro || reduced) return;
    introInitiator = document.activeElement;
    intro.hidden = false;
    intro.classList.remove('is-leaving');
    intro.setAttribute('aria-hidden', 'false');
    document.querySelectorAll('.skip-link, main, header, footer').forEach(element => element.setAttribute('inert', ''));
    intro.querySelector('[data-skip-intro]')?.focus({preventScroll:true});
    timer = setTimeout(leaveIntro, 3900);
  }
  if (intro) {
    let seen = false;
    try { seen = sessionStorage.getItem('adafnia-intro') === 'seen'; sessionStorage.setItem('adafnia-intro', 'seen'); } catch {}
    if (!seen && !location.search.includes('nointro')) playIntro();
    document.querySelector('[data-skip-intro]')?.addEventListener('click', leaveIntro);
  }
  document.querySelectorAll('[data-replay-intro]').forEach(button => {
    if (!intro || reduced) button.hidden = true;
    button.addEventListener('click', () => { window.scrollTo({ top: 0, behavior: 'instant' }); playIntro(); });
  });
  if (!reduced && 'IntersectionObserver' in window) {
    document.body.classList.add('motion-ready');
    const observer = new IntersectionObserver(entries => entries.forEach(entry => {
      if (entry.isIntersecting) { entry.target.classList.add('visible'); observer.unobserve(entry.target); }
    }), { threshold: 0.08 });
    document.querySelectorAll('[data-reveal]').forEach(element => observer.observe(element));
  }
  const specifications = document.querySelector('.spec-section');
  if (specifications) {
    const print = document.createElement('button');
    print.type = 'button';
    print.className = 'button button-secondary section-link';
    print.textContent = document.body.dataset.lang === 'ar' ? 'طباعة المواصفات / PDF' : 'Print specifications / PDF';
    print.addEventListener('click', () => window.print());
    specifications.append(print);
  }
  document.querySelectorAll('[data-print]').forEach(button => button.addEventListener('click', () => window.print()));
  document.querySelectorAll('form[data-submit]').forEach(form => form.addEventListener('submit', () => {
    if (!form.checkValidity()) return;
    const button = form.querySelector('button[type=submit]');
    if (button) { button.disabled = true; button.textContent = document.body.dataset.lang === 'ar' ? 'جارٍ الإرسال…' : 'Sending…'; }
  }));
  const filters = document.querySelector('[data-spec-filters]');
  if (filters) {
    const rows = [...document.querySelectorAll('[data-variant]')];
    const noResults = document.querySelector('[data-no-variants]');
    const applyFilters = () => {
      const diameter = filters.querySelector('[name=diameter]')?.value;
      const pressure = filters.querySelector('[name=pressure]')?.value;
      let count = 0;
      rows.forEach(row => {
        const show = (!diameter || Number(row.dataset.diameter) === Number(diameter)) && (!pressure || Number(row.dataset.pressure) === Number(pressure));
        row.hidden = !show;
        if (show) count++;
      });
      if (noResults) noResults.hidden = count !== 0;
    };
    filters.addEventListener('change', applyFilters);
    filters.addEventListener('reset', () => setTimeout(applyFilters, 0));
  }
})();
