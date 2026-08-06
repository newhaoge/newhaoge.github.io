/* Shared page behaviour. Every block checks that its element exists first,
   so this one file can load on every page.                                */
(function(){
  "use strict";

  /* ---- portrait: falls back to a monogram if the photo is missing ---- */
  (function(){
    var img = document.getElementById('portrait');
    var fb  = document.getElementById('portraitFallback');
    if (!img || !fb) return;
    function fail(){ img.style.display = 'none'; fb.hidden = false; }
    img.addEventListener('error', fail);
    if (img.complete && img.naturalWidth === 0) fail();
  })();

  /* ---- home page: fade the bottom of the news feed until it is scrolled ---- */
  (function(){
    var feed = document.getElementById('feed');
    if (!feed) return;
    var wrap = feed.parentNode;
    function edge(){
      var atEnd = feed.scrollTop + feed.clientHeight >= feed.scrollHeight - 4;
      wrap.className = atEnd ? 'feedwrap at-end' : 'feedwrap';
    }
    feed.addEventListener('scroll', edge);
    window.addEventListener('resize', edge);
    edge();
  })();

  /* ---- news page: year menu, built from the timeline itself ---- */
  (function(){
    var sel = document.getElementById('newsyear');
    if (!sel) return;
    var items = Array.prototype.slice.call(document.querySelectorAll('.timeline > li'));
    var count = document.getElementById('newscount');
    var years = [];

    items.forEach(function(li){
      var t = li.querySelector('time');
      var y = t ? (t.getAttribute('datetime') || '').slice(0, 4) : '';
      li.setAttribute('data-year', y);
      if (y && years.indexOf(y) === -1) years.push(y);
    });
    years.sort().reverse().forEach(function(y){
      var o = document.createElement('option');
      o.value = y; o.textContent = y;
      sel.appendChild(o);
    });

    function apply(){
      var v = sel.value, shown = 0;
      items.forEach(function(li){
        var ok = (v === 'all') || (li.getAttribute('data-year') === v);
        li.hidden = !ok;
        if (ok) shown++;
      });
      if (count) count.textContent = shown + (shown === 1 ? ' update' : ' updates');
    }
    sel.addEventListener('change', apply);
    apply();
  })();

  /* ---- publications page: search box and type filters ---- */
  (function(){
    var list = document.getElementById('publist');
    if (!list) return;
    var pubs    = Array.prototype.slice.call(list.querySelectorAll('.pub'));
    var groups  = Array.prototype.slice.call(list.querySelectorAll('.yeargroup'));
    var buttons = Array.prototype.slice.call(document.querySelectorAll('.filters button'));
    var search  = document.getElementById('pubsearch');
    var count   = document.getElementById('pubcount');
    var empty   = document.getElementById('pubempty');
    var mode = 'all';

    pubs.forEach(function(p){ p._text = p.textContent.toLowerCase(); });

    function apply(){
      var q = (search && search.value || '').trim().toLowerCase();
      var shown = 0;
      pubs.forEach(function(p){
        var typeOk = mode === 'all'
          || (mode === 'top'     && p.dataset.tier === 'top')
          || (mode === 'conf'    && p.dataset.type === 'conf')
          || (mode === 'journal' && p.dataset.type === 'journal')
          || (mode === 'patent'  && p.dataset.type === 'patent');
        var ok = typeOk && (!q || p._text.indexOf(q) !== -1);
        p.hidden = !ok;
        if (ok) shown++;
      });
      groups.forEach(function(g){ g.hidden = !g.querySelector('.pub:not([hidden])'); });
      if (count) count.textContent = shown + (shown === 1 ? ' entry' : ' entries');
      if (empty) empty.hidden = shown !== 0;
    }

    buttons.forEach(function(b){
      b.addEventListener('click', function(){
        mode = b.dataset.filter;
        buttons.forEach(function(x){ x.setAttribute('aria-pressed', String(x === b)); });
        apply();
      });
    });
    if (search) search.addEventListener('input', apply);
    apply();
  })();
})();
