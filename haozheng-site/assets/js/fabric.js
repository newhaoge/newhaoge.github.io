/* Hero background: a two-tier spine-leaf cluster fabric.
   Pale blue traffic is scale-up (inside a pod, over the local bus);
   amber traffic is scale-out (leaf -> spine -> leaf), the path a
   gradient all-reduce takes across the cluster.

   Tuning knobs live in layout(): POD (accelerators per pod), pitch
   (spacing), and the row positions leafY / spineY. Colours are the
   rgba() literals in renderStill() and spawn().                     */
(function(){
  "use strict";
  if (!document.getElementById('mesh')) return;

  var mesh = (function(){
    var canvas = document.getElementById('mesh');
    var ctx = canvas.getContext('2d');
    var motion = window.matchMedia('(prefers-reduced-motion: reduce)');
    var reduce = motion.matches;
    var W = 0, H = 0, dpr = 1;
    var leaves = [], spines = [], pods = [], busY = 0;
    var still = null, stillCtx = null;
    var packets = [], raf = null, last = 0, spawnAt = 0, active = true, visible = true;

    var POD = 4;

    function layout(){
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      var r = canvas.getBoundingClientRect();
      W = r.width; H = r.height;
      if (!W || !H) return;
      canvas.width  = Math.round(W * dpr);
      canvas.height = Math.round(H * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      var pitch  = W < 640 ? 40 : 54;
      var podGap = pitch * 0.75;
      function spanFor(n){ return (n-1)*pitch + Math.floor((n-1)/POD)*podGap; }
      var n = POD;
      while (spanFor(n + 1) < W + pitch * 1.4) n += 1;

      var span   = spanFor(n);
      var startX = (W - span) / 2;
      var leafY  = H - Math.min(70, H * 0.14);
      busY       = leafY + Math.min(22, H * 0.045);
      var spineY = Math.max(34, H * 0.15);

      leaves = [];
      for (var i = 0; i < n; i++){
        leaves.push({ x: startX + i*pitch + Math.floor(i/POD)*podGap, y: leafY, pod: Math.floor(i/POD) });
      }
      pods = [];
      for (var i2 = 0; i2 < leaves.length; i2 += POD){
        pods.push(leaves.slice(i2, i2 + POD));
      }

      var sc = Math.max(3, Math.min(7, Math.round(leaves.length / POD)));
      spines = [];
      for (var j = 0; j < sc; j++){
        spines.push({ x: startX + (sc === 1 ? span/2 : span * j / (sc - 1)), y: spineY });
      }

      renderStill();
      packets = [];
      if (reduce) blit();
    }

    /* the fabric itself never moves, so draw it once and blit each frame */
    function renderStill(){
      still = document.createElement('canvas');
      still.width = Math.round(W * dpr); still.height = Math.round(H * dpr);
      stillCtx = still.getContext('2d');
      var c = stillCtx;
      c.setTransform(dpr, 0, 0, dpr, 0, 0);
      c.clearRect(0, 0, W, H);

      // leaf-to-spine fabric
      c.lineWidth = 1;
      c.strokeStyle = 'rgba(114,122,238,0.14)';
      c.beginPath();
      for (var i = 0; i < leaves.length; i++){
        for (var j = 0; j < spines.length; j++){
          c.moveTo(leaves[i].x, leaves[i].y - 7);
          c.lineTo(spines[j].x, spines[j].y + 4);
        }
      }
      c.stroke();

      // scale-up bus inside each pod
      c.strokeStyle = 'rgba(122,132,242,0.34)';
      c.lineWidth = 1.3;
      c.beginPath();
      for (var k = 0; k < pods.length; k++){
        var pod = pods[k];
        if (pod.length < 2) continue;
        c.moveTo(pod[0].x, busY);
        c.lineTo(pod[pod.length-1].x, busY);
        for (var m = 0; m < pod.length; m++){
          c.moveTo(pod[m].x, pod[m].y + 6);
          c.lineTo(pod[m].x, busY);
        }
      }
      c.stroke();

      // spine switches
      for (var s = 0; s < spines.length; s++){
        c.fillStyle = 'rgba(150,162,182,0.34)';
        c.fillRect(spines[s].x - 15, spines[s].y - 3, 30, 6);
        c.fillStyle = 'rgba(190,200,215,0.30)';
        c.fillRect(spines[s].x - 15, spines[s].y - 3, 30, 1.4);
      }

      // accelerators, drawn as a stack of memory bars
      for (var a = 0; a < leaves.length; a++){
        var x = leaves[a].x, y = leaves[a].y;
        c.fillStyle = 'rgba(178,190,209,0.20)';
        c.fillRect(x - 9, y - 6, 18, 12);
        c.fillStyle = 'rgba(208,218,234,0.36)';
        c.fillRect(x - 9, y - 6, 18, 2);
      }
    }

    function blit(){
      ctx.clearRect(0, 0, W, H);
      if (still) ctx.drawImage(still, 0, 0, W, H);
    }

    function pick(n){ return (Math.random() * n) | 0; }

    function spawn(tries){
      if (leaves.length < 2) return;
      tries = tries || 0;
      var retry = function(){ if (tries < 6) spawn(tries + 1); };
      var scaleUp = pods.length > 0 && Math.random() < 0.4;
      if (scaleUp){
        var pod = pods[pick(pods.length)];
        if (pod.length < 2) return retry();
        var a = pick(pod.length), b = pick(pod.length);
        if (a === b) return retry();
        packets.push({
          pts: [{x:pod[a].x, y:pod[a].y+6}, {x:pod[a].x, y:busY},
                {x:pod[b].x, y:busY},       {x:pod[b].x, y:pod[b].y+6}],
          leg: 0, t: 0, speed: 150, head: 'rgba(176,192,255,0.95)', tail: '150,170,255'
        });
      } else {
        var i = pick(leaves.length), k = pick(leaves.length);
        if (leaves[i].pod === leaves[k].pod) return retry();
        var j = pick(spines.length);
        packets.push({
          pts: [{x:leaves[i].x, y:leaves[i].y-7}, {x:spines[j].x, y:spines[j].y+4},
                {x:leaves[k].x, y:leaves[k].y-7}],
          leg: 0, t: 0, speed: 190, head: 'rgba(240,196,94,0.95)', tail: '232,179,61'
        });
      }
    }

    function draw(dt){
      blit();
      for (var i = packets.length - 1; i >= 0; i--){
        var p = packets[i];
        var a = p.pts[p.leg], b = p.pts[p.leg + 1];
        if (!b){ packets.splice(i, 1); continue; }
        var len = Math.hypot(b.x - a.x, b.y - a.y);
        p.t += (dt * p.speed) / (len || 1);
        while (p.t >= 1){
          p.t -= 1; p.leg += 1;
          a = p.pts[p.leg]; b = p.pts[p.leg + 1];
          if (!b) break;
          len = Math.hypot(b.x - a.x, b.y - a.y);
        }
        if (!b){ packets.splice(i, 1); continue; }
        var hx = a.x + (b.x - a.x) * p.t, hy = a.y + (b.y - a.y) * p.t;
        var s  = Math.max(0, p.t - 0.3);
        var sx = a.x + (b.x - a.x) * s,  sy = a.y + (b.y - a.y) * s;

        var g = ctx.createLinearGradient(sx, sy, hx, hy);
        g.addColorStop(0, 'rgba(' + p.tail + ',0)');
        g.addColorStop(1, 'rgba(' + p.tail + ',0.7)');
        ctx.strokeStyle = g; ctx.lineWidth = 1.7;
        ctx.beginPath(); ctx.moveTo(sx, sy); ctx.lineTo(hx, hy); ctx.stroke();

        ctx.fillStyle = p.head;
        ctx.fillRect(hx - 2.4, hy - 2.4, 4.8, 4.8);
      }
    }

    function tick(now){
      raf = requestAnimationFrame(tick);
      if (!active || !visible){ last = now; return; }
      var dt = Math.min((now - last) / 1000, 0.05); last = now;
      if (now > spawnAt && packets.length < 9){ spawn(); spawnAt = now + 460 + Math.random() * 700; }
      draw(dt);
    }

    function start(){
      if (raf === null && !reduce){ last = performance.now(); raf = requestAnimationFrame(tick); }
    }

    window.addEventListener('resize', function(){
      clearTimeout(layout._t); layout._t = setTimeout(layout, 160);
    });
    document.addEventListener('visibilitychange', function(){ visible = !document.hidden; });
    if ('IntersectionObserver' in window){
      new IntersectionObserver(function(entries){
        active = entries[0].isIntersecting;
        if (active) last = performance.now();
      }).observe(canvas);
    }
    function motionChange(event){
      reduce = event.matches;
      if (reduce){
        if (raf !== null) cancelAnimationFrame(raf);
        raf = null; packets = []; blit();
      } else {
        start();
      }
    }
    if (motion.addEventListener) motion.addEventListener('change', motionChange);
    else if (motion.addListener) motion.addListener(motionChange);

    return {
      init: function(){ layout(); start(); },
      setActive: function(v){ active = v; if (v) layout(); }
    };
  })();

  mesh.init();
})();
