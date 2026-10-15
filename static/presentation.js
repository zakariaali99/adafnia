(() => {
  'use strict';
  const hero = document.querySelector('.industrial-hero');
  const header = document.querySelector('.header');
  if (hero && header && 'IntersectionObserver' in window) {
    const observer = new IntersectionObserver(([entry]) => header.classList.toggle('is-solid', !entry.isIntersecting), {rootMargin:'-85px 0px 0px 0px',threshold:0});
    observer.observe(hero);
    window.addEventListener('pagehide', () => observer.disconnect(), {once:true});
  }
  document.querySelectorAll('[data-project-city]').forEach(link => {
    const markers = [...document.querySelectorAll('.map-marker[data-city]')];
    const highlight = () => markers.forEach(marker => marker.classList.toggle('is-active', marker.dataset.city === link.dataset.projectCity));
    const clear = () => markers.forEach(marker => marker.classList.remove('is-active'));
    link.addEventListener('pointerenter', highlight);
    link.addEventListener('pointerleave', clear);
    link.addEventListener('focus', highlight);
    link.addEventListener('blur', clear);
  });
  document.querySelectorAll('[data-process]').forEach(explorer => {
    const tabs = [...explorer.querySelectorAll('[role=tab]')];
    const panels = [...explorer.querySelectorAll('[role=tabpanel]')];
    const tablist = explorer.querySelector('[role=tablist]');
    const narrow = window.matchMedia('(max-width:767px)');
    const setOrientation = () => tablist.setAttribute('aria-orientation', narrow.matches ? 'horizontal' : 'vertical');
    setOrientation();
    narrow.addEventListener('change', setOrientation);
    function select(tab) {
      tabs.forEach(item => {const selected=item===tab;item.setAttribute('aria-selected',String(selected));item.tabIndex=selected?0:-1;});
      panels.forEach(panel => {panel.hidden=panel.id!==tab.getAttribute('aria-controls');});
    }
    tabs.forEach((tab, index) => {
      tab.addEventListener('click', () => select(tab));
      tab.addEventListener('keydown', event => {
        const horizontal = narrow.matches;
        const forward = horizontal ? (document.documentElement.dir==='rtl'?'ArrowLeft':'ArrowRight') : 'ArrowDown';
        const backward = horizontal ? (document.documentElement.dir==='rtl'?'ArrowRight':'ArrowLeft') : 'ArrowUp';
        let target;
        if(event.key===forward) target=tabs[(index+1)%tabs.length];
        else if(event.key===backward) target=tabs[(index-1+tabs.length)%tabs.length];
        else if(event.key==='Home') target=tabs[0];
        else if(event.key==='End') target=tabs[tabs.length-1];
        if(target){event.preventDefault();select(target);target.focus();}
      });
    });
  });
})();
