// パソコン診断ナビ オフライン対応
// 画面やプログラム（html / js / css）は「まずネットから最新を取り 取れなければ保存分を使う」
// 写真やアイコンは「保存分を先に使う」
// 中身を更新したら CACHE の番号を1つ上げる
const CACHE = 'pcshindan-v10';
const ASSETS = [
  './', 'index.html', 'app.js', 'style.css', 'manifest.json',
  'photos/laptop-setup.png', 'photos/support-consultation.png',
  'icons/icon-180.png', 'icons/icon-192.png', 'icons/icon-512.png'
];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(ASSETS)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(key => key !== CACHE).map(key => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const request = event.request;
  const url = new URL(request.url);
  // 集計の送信（別サイトへのPOST）などには手を出さない
  if (request.method !== 'GET' || url.origin !== self.location.origin) return;

  const isImage = /\.(png|jpg|jpeg|webp|svg)$/.test(url.pathname);
  if (isImage) {
    event.respondWith(caches.match(request).then(hit => hit || fetchAndStore(request)));
    return;
  }
  event.respondWith(fetchAndStore(request).catch(() => caches.match(request).then(hit => hit || caches.match('index.html'))));
});

function fetchAndStore(request) {
  return fetch(request).then(response => {
    if (response.ok) {
      const copy = response.clone();
      caches.open(CACHE).then(cache => cache.put(request, copy));
    }
    return response;
  });
}
