/* 七転び八起会  main.js
   site-data.js の内容を画面に流し込む／メニュー／スクロール表示／お問い合わせ文のコピー */
(function () {
  "use strict";
  var S = window.SITE || {};
  var $ = function (sel, root) { return (root || document).querySelector(sel); };
  var h = function (s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); };
  document.documentElement.classList.add("js");

  /* ---- アイコン（活動内容） ---- */
  var ICONS = {
    study: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19V5a2 2 0 0 1 2-2h12v16H6a2 2 0 0 0-2 2z"/><path d="M4 19a2 2 0 0 0 2 2h12"/><path d="M8 7h8M8 11h6"/></svg>',
    party: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M8 21h8M12 17v4"/><path d="M7 4h10l-1 7a4 4 0 0 1-8 0z"/><path d="M5 6H3a3 3 0 0 0 3 5M19 6h2a3 3 0 0 1-3 5"/></svg>',
    market: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l1.5-5h15L21 9"/><path d="M3 9h18v2a3 3 0 0 1-6 0 3 3 0 0 1-6 0 3 3 0 0 1-6 0z"/><path d="M5 13v8h14v-8"/><path d="M10 21v-5h4v5"/></svg>',
    ai: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="3"/><path d="M9 9h6v6H9z"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2"/></svg>',
    match: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="3"/><circle cx="16" cy="16" r="3"/><path d="M11 8h5a3 3 0 0 1 3 3v1M13 16H8a3 3 0 0 1-3-3v-1"/></svg>',
    hq: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 21h18"/><path d="M5 21V7l7-4 7 4v14"/><path d="M9 21v-6h6v6"/><path d="M9 11h2M13 11h2"/></svg>'
  };

  /* ---- 文字の流し込み ---- */
  function fill() {
    var o = S.org || {};
    document.querySelectorAll("[data-text]").forEach(function (el) {
      var path = el.getAttribute("data-text").split(".");
      var v = S; path.forEach(function (k) { v = v == null ? undefined : v[k]; });
      if (v != null && v !== "") {
        if (el.hasAttribute("data-phrases")) { /* 読点で区切って 途中で改行しないようにする */
          el.innerHTML = String(v).split(/(?<=[、。])/).filter(Boolean).map(function (ph) { return '<span class="ph">' + h(ph) + "</span>"; }).join("");
        } else el.textContent = v;
      }
    });
    document.title = o.name + "｜" + o.parent + " " + o.branch;

    /* 本部メニュー（上の細い帯） */
    var hqn = $("#hqnav");
    if (hqn && S.hqNav) hqn.innerHTML = S.hqNav.map(function (n) { return '<li><a href="' + h(n.url) + '" target="_blank" rel="noopener">' + h(n.label) + "</a></li>"; }).join("");

    /* 写真（設定があるときだけ出す） */
    var ph = S.photos || {};
    var hp = $("#hero-photo"); if (hp && ph.hero) { hp.style.backgroundImage = "url('" + ph.hero + "')"; hp.classList.add("has-photo"); }
    var ap = $("#about-photo"); if (ap && ph.about) { ap.innerHTML = '<img src="' + h(ph.about) + '" alt="' + h(o.name) + 'の活動のようす" loading="lazy">'; ap.hidden = false; }
    var sec = document.querySelector('[data-photo="activity"]'); if (sec && ph.activity) { sec.style.setProperty("--photo", "url('" + ph.activity + "')"); sec.classList.add("has-photo"); }

    /* メニュー */
    var nav = $("#nav");
    if (nav && S.nav) nav.innerHTML = S.nav.map(function (n) { return '<li><a href="#' + h(n.id) + '">' + h(n.label) + "</a></li>"; }).join("");

    /* ヒーローの数字 */
    var st = $("#stats");
    if (st && S.stats) st.innerHTML = S.stats.map(function (s) { return '<div class="stat"><b>' + h(s.value) + "<small>" + h(s.unit) + "</small></b><span>" + h(s.label) + "</span></div>"; }).join("");

    /* 理念 */
    var vals = $("#values");
    var KANJI = ["語", "共", "楽"];
    if (vals && S.values) vals.innerHTML = S.values.map(function (v, i) { return '<article class="value reveal"><div class="kanji" aria-hidden="true">' + (KANJI[i] || "") + "</div><h3>" + h(v.title) + "</h3><p>" + h(v.text) + "</p></article>"; }).join("");

    /* 本部リンク */
    var hq = $("#hq-links");
    if (hq && S.hqLinks) hq.innerHTML = S.hqLinks.map(function (l) { return '<a class="chip" href="' + h(l.url) + '" target="_blank" rel="noopener">' + h(l.label) + " ↗</a>"; }).join("");

    /* 活動 */
    var act = $("#activities");
    if (act && S.activities) act.innerHTML = S.activities.map(function (a) { return '<article class="activity reveal"><div class="ico" aria-hidden="true">' + (ICONS[a.icon] || ICONS.study) + "</div><div><h3>" + h(a.title) + "</h3><p>" + h(a.text) + "</p></div></article>"; }).join("");

    /* 会員 */
    var mem = $("#members-list");
    if (mem) {
      var cards = (S.members || []).map(function (m) {
        var links = [];
        if (m.url) links.push('<a class="chip" href="' + h(m.url) + '" target="_blank" rel="noopener">ホームページ ↗</a>');
        if (m.jsaUrl) links.push('<a class="chip" href="' + h(m.jsaUrl) + '" target="_blank" rel="noopener">本部の会員ページ ↗</a>');
        return '<article class="member reveal"><div class="top"><h3>' + h(m.company) + "</h3>" + (m.role ? '<span class="badge">' + h(m.role) + "</span>" : "") + '</div><div class="meta">' + h(m.industry) + (m.area ? "　／　" + h(m.area) : "") + "</div><p>" + h(m.text) + '</p><div class="links">' + links.join("") + "</div></article>";
      });
      var slots = Number(S.memberSlots || 0);
      for (var i = 0; i < slots; i++) cards.push('<article class="member slot reveal"><div><b>あなたの会社をここに</b><p>会員になると この欄で紹介します</p></div></article>');
      mem.innerHTML = cards.join("");
    }

    /* スケジュール */
    var ev = $("#events");
    if (ev && S.events) {
      var list = S.events.slice().sort(function (a, b) { return a.date < b.date ? -1 : 1; });
      ev.innerHTML = list.map(function (e) {
        var ym = e.date.split("-"); var label = ym[0] + "年" + Number(ym[1]) + "月" + (ym[2] ? Number(ym[2]) + "日" : "");
        return '<li class="reveal"><div class="ym">' + h(label) + "</div><h3>" + h(e.title) + (e.status ? '<span class="status" data-s="' + h(e.status) + '">' + h(e.status) + "</span>" : "") + '</h3><div class="place">会場：' + h(e.place) + '</div><div class="note">' + h(e.note) + "</div></li>";
      }).join("");
    }

    /* 入会 */
    var j = S.join || {};
    var who = $("#join-who"); if (who && j.who) who.innerHTML = j.who.map(function (w) { return "<li>" + h(w) + "</li>"; }).join("");
    var steps = $("#join-steps"); if (steps && j.steps) steps.innerHTML = j.steps.map(function (s) { return '<li class="reveal"><div><h3>' + h(s.title) + "</h3><p>" + h(s.text) + "</p></div></li>"; }).join("");

    /* お知らせ */
    var nw = $("#news-list");
    if (nw && S.news) nw.innerHTML = S.news.map(function (n) { return '<li><time datetime="' + h(n.date) + '">' + h(n.date.replace(/-/g, ".")) + '</time><span class="tag">' + h(n.tag) + "</span><span>" + h(n.title) + "</span></li>"; }).join("");

    /* 連絡先 */
    var c = S.contact || {};
    var dl = $("#contact-dl");
    if (dl) {
      var rows = [];
      if (c.address) rows.push(["住所", h(c.address)]);
      if (c.tel) rows.push(["電話", '<span class="tel">' + h(c.tel) + "</span>"]);
      if (c.fax) rows.push(["FAX", h(c.fax)]);
      if (c.hours) rows.push(["受付", h(c.hours)]);
      if (c.email) rows.push(["メール", h(c.email)]);
      if (c.line) rows.push(["LINE", '<a href="' + h(c.line) + '" target="_blank" rel="noopener">公式LINEを開く ↗</a>']);
      dl.innerHTML = rows.map(function (r) { return "<dt>" + r[0] + "</dt><dd>" + r[1] + "</dd>"; }).join("");
    }
    var fl = $("#footer-links");
    if (fl && S.nav) fl.innerHTML = S.nav.map(function (n) { return '<li><a href="#' + h(n.id) + '">' + h(n.label) + "</a></li>"; }).join("");
    var fh = $("#footer-hq");
    if (fh && S.hqLinks) fh.innerHTML = S.hqLinks.map(function (l) { return '<li><a href="' + h(l.url) + '" target="_blank" rel="noopener">' + h(l.label) + "</a></li>"; }).join("");
    var ver = $("#version"); if (ver) ver.innerHTML = "版 <b>" + h(S.version) + "</b>　" + h(S.updated);
    var yr = $("#year"); if (yr) yr.textContent = new Date().getFullYear();
  }

  /* ---- メニュー（スマホ） ---- */
  function menu() {
    var btn = $("#menu-btn"), nav = $("#nav");
    if (!btn || !nav) return;
    btn.addEventListener("click", function () { var open = nav.classList.toggle("is-open"); btn.setAttribute("aria-expanded", open ? "true" : "false"); btn.textContent = open ? "閉じる" : "メニュー"; });
    nav.addEventListener("click", function (e) { if (e.target.tagName === "A") { nav.classList.remove("is-open"); btn.setAttribute("aria-expanded", "false"); btn.textContent = "メニュー"; } });
  }

  /* ---- いま見ている章をメニューで光らせる ---- */
  function spy() {
    var links = Array.prototype.slice.call(document.querySelectorAll("#nav a"));
    if (!("IntersectionObserver" in window) || !links.length) return;
    var map = {};
    links.forEach(function (a) { map[a.getAttribute("href").slice(1)] = a; });
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { links.forEach(function (a) { a.classList.remove("is-active"); }); var a = map[e.target.id]; if (a) a.classList.add("is-active"); } });
    }, { rootMargin: "-40% 0px -55% 0px" });
    Object.keys(map).forEach(function (id) { var el = document.getElementById(id); if (el) io.observe(el); });
  }

  /* ---- スクロールで浮かび上がる ---- */
  function reveal() {
    var els = document.querySelectorAll(".reveal");
    if (!("IntersectionObserver" in window)) { els.forEach(function (el) { el.classList.add("is-in"); }); return; }
    var io = new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("is-in"); io.unobserve(e.target); } }); }, { threshold: .12 });
    els.forEach(function (el, i) { el.style.transitionDelay = (i % 3) * 70 + "ms"; io.observe(el); });
  }

  /* ---- お問い合わせ：本文をつくってコピー ---- */
  function form() {
    var f = $("#contact-form"); if (!f) return;
    var toast = $("#toast");
    function body() {
      var v = function (id) { return ($("#" + id) || {}).value || ""; };
      return ["【七転び八起会 お問い合わせ】", "ご用件：" + v("f-kind"), "お名前：" + v("f-name"), "会社名：" + v("f-company"), "連絡先：" + v("f-contact"), "", v("f-message")].join("\n");
    }
    f.addEventListener("submit", function (e) {
      e.preventDefault();
      var text = body();
      var done = function () { if (toast) toast.textContent = "本文をコピーしました。メールやLINEに貼り付けて送ってください。"; };
      var fail = function () { if (toast) toast.textContent = "コピーできませんでした。下の内容を選んでコピーしてください。"; var ta = $("#f-message"); if (ta) { ta.value = text; ta.focus(); ta.select(); } };
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(done, fail); else fail();
    });
  }

  document.addEventListener("DOMContentLoaded", function () { fill(); menu(); spy(); reveal(); form(); });
})();
