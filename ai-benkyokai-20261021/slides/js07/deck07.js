(() => {
  const slides = Array.from(document.querySelectorAll(".xop-slide"));
  let current = 0;
  const select = document.querySelector("[data-jump]");
  const clamp = (n) => Math.max(0, Math.min(slides.length - 1, n));
  // semantic-layer (1920x1080) を canvas 幅に合わせてスケール（07方式）
  function fit() {
    slides.forEach((s) => {
      const c = s.querySelector(".xop-canvas");
      const layer = s.querySelector(".semantic-layer");
      if (c && layer) layer.style.setProperty("--xs", (c.clientWidth / 1920).toString());
    });
  }
  function show(index) {
    if (!slides.length) return;
    current = clamp(Number(index) || 0);
    slides.forEach((s, i) => s.classList.toggle("is-active", i === current));
    if (select) select.value = String(current);
    requestAnimationFrame(fit);
    history.replaceState(null, "", `#${current + 1}`);
  }
  window.template_show = show;
  window.templateDeck = { show, count: slides.length, current: () => current };
  document.querySelector("[data-prev]")?.addEventListener("click", () => show(current - 1));
  document.querySelector("[data-next]")?.addEventListener("click", () => show(current + 1));
  select?.addEventListener("change", () => show(Number(select.value)));
  window.addEventListener("keydown", (e) => {
    if (e.key === "ArrowRight" || e.key === "PageDown" || e.key === " ") show(current + 1);
    if (e.key === "ArrowLeft" || e.key === "PageUp") show(current - 1);
  });
  window.addEventListener("resize", fit);
  const fromHash = () => { const n = Number(location.hash.replace("#", "")); return Number.isFinite(n) && n > 0 ? n - 1 : 0; };
  show(fromHash());
  fit();
})();
