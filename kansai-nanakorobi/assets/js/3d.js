/* 版3：立体の動き。カードはマウスの位置で傾き 光が走る。だるまは視線を追う。ヒーロー背景は視差で動く */
(function () {
  "use strict";
  if (!(window.SITE && window.SITE.look3d)) return;
  document.body.classList.add("look3d");
  var fine = window.matchMedia("(hover:hover) and (pointer:fine)").matches;
  var reduce = window.matchMedia("(prefers-reduced-motion:reduce)").matches;
  if (!fine || reduce) return;

  function tiltAll() {
    document.querySelectorAll(".value,.activity,.member:not(.slot),.steps li,.contact-card,.hq-box").forEach(function (el) { el.classList.add("tilt"); });
    document.addEventListener("mousemove", function (e) {
      var el = e.target.closest && e.target.closest(".tilt"); if (!el) return;
      var r = el.getBoundingClientRect();
      var x = (e.clientX - r.left) / r.width, y = (e.clientY - r.top) / r.height;
      el.style.setProperty("--ry", ((x - .5) * 10).toFixed(2) + "deg");
      el.style.setProperty("--rx", ((.5 - y) * 8).toFixed(2) + "deg");
      el.style.setProperty("--mx", (x * 100).toFixed(1) + "%");
      el.style.setProperty("--my", (y * 100).toFixed(1) + "%");
      el.style.setProperty("--glow", "1");
    });
    document.addEventListener("mouseout", function (e) {
      var el = e.target.closest && e.target.closest(".tilt"); if (!el || (e.relatedTarget && el.contains(e.relatedTarget))) return;
      ["--rx", "--ry", "--glow"].forEach(function (p) { el.style.removeProperty(p); });
    });
  }

  function daruma() {
    var hero = document.querySelector(".hero"), art = document.querySelector(".hero-art img, .hero-art svg");
    if (!hero || !art) return;
    hero.addEventListener("mousemove", function (e) {
      var r = hero.getBoundingClientRect();
      var x = (e.clientX - r.left) / r.width - .5, y = (e.clientY - r.top) / r.height - .5;
      art.style.setProperty("--ry", (x * 28).toFixed(2) + "deg");
      art.style.setProperty("--rx", (-y * 16).toFixed(2) + "deg");
      hero.style.setProperty("--px", (-x * 30).toFixed(1) + "px");
      hero.style.setProperty("--py", (-y * 20).toFixed(1) + "px");
    });
    hero.addEventListener("mouseleave", function () { ["--rx", "--ry"].forEach(function (p) { art.style.removeProperty(p); }); hero.style.removeProperty("--px"); hero.style.removeProperty("--py"); });
  }

  function start() { tiltAll(); daruma(); }
  /* main.js がカードを流し込んだ後に動かす（main.js は DOMContentLoaded で流し込む） */
  if (document.readyState === "complete") start(); else window.addEventListener("load", start);
})();
