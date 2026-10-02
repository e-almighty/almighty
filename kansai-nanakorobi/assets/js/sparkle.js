/* 版5：マウスの軌跡にキラキラ（星の粒）を散らす。カードに乗ると多めに。タッチ端末・動きを減らす設定では出さない */
(function () {
  "use strict";
  var canvas = document.getElementById("sparkle"); if (!canvas) return;
  if (window.matchMedia("(prefers-reduced-motion:reduce)").matches) { canvas.remove(); return; }
  if (!window.matchMedia("(hover:hover) and (pointer:fine)").matches) { canvas.remove(); return; }
  var ctx = canvas.getContext("2d"), parts = [], W, H, dpr = Math.min(window.devicePixelRatio || 1, 2);
  var COLORS = ["#ffffff", "#fff2b0", "#f2c94c", "#9cc4ff", "#4a90ff"];
  function size() { W = canvas.width = innerWidth * dpr; H = canvas.height = innerHeight * dpr; }
  size(); addEventListener("resize", size);
  var last = { x: 0, y: 0, t: 0 };
  function spawn(x, y, n, big) {
    for (var i = 0; i < n; i++) {
      var a = Math.random() * Math.PI * 2, sp = (0.4 + Math.random() * 1.6) * dpr;
      parts.push({ x: x * dpr, y: y * dpr, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp - 0.6 * dpr, life: 1, decay: 0.012 + Math.random() * 0.02, r: (big ? 3 : 2) * dpr * (0.6 + Math.random()), c: COLORS[(Math.random() * COLORS.length) | 0], rot: Math.random() * Math.PI, spin: (Math.random() - .5) * .2 });
    }
    if (parts.length > 400) parts.splice(0, parts.length - 400);
  }
  addEventListener("mousemove", function (e) {
    var now = performance.now(), dx = e.clientX - last.x, dy = e.clientY - last.y, d = Math.sqrt(dx * dx + dy * dy);
    var onCard = e.target.closest && e.target.closest(".tilt,.btn,.stat,.chip,.daruma-stage");
    if (d > 6 || now - last.t > 80) { spawn(e.clientX, e.clientY, onCard ? 4 : 2, !!onCard); last = { x: e.clientX, y: e.clientY, t: now }; }
  }, { passive: true });
  addEventListener("click", function (e) { spawn(e.clientX, e.clientY, 24, true); });
  function star(x, y, r, rot) {
    ctx.beginPath();
    for (var i = 0; i < 8; i++) { var rr = i % 2 ? r * .38 : r, t = rot + i * Math.PI / 4; ctx.lineTo(x + Math.cos(t) * rr, y + Math.sin(t) * rr); }
    ctx.closePath();
  }
  function tick() {
    ctx.clearRect(0, 0, W, H);
    ctx.globalCompositeOperation = "lighter";
    for (var i = parts.length - 1; i >= 0; i--) {
      var p = parts[i]; p.x += p.vx; p.y += p.vy; p.vy += 0.03 * dpr; p.life -= p.decay; p.rot += p.spin;
      if (p.life <= 0) { parts.splice(i, 1); continue; }
      ctx.globalAlpha = Math.max(0, p.life);
      ctx.fillStyle = p.c; ctx.shadowColor = p.c; ctx.shadowBlur = 8 * dpr;
      star(p.x, p.y, p.r * (0.5 + p.life), p.rot); ctx.fill();
    }
    ctx.globalAlpha = 1; ctx.shadowBlur = 0; ctx.globalCompositeOperation = "source-over";
    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
})();
