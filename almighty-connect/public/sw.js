// Service worker for the reception iPad: shows the incoming-call notification while the page is asleep.
// It deliberately has no fetch handler, so pages are never served from a stale cache.
self.addEventListener('install', function () { self.skipWaiting(); });
self.addEventListener('activate', function (event) { event.waitUntil(self.clients.claim()); });
self.addEventListener('push', function (event) {
  var data = {};
  try { data = event.data ? event.data.json() : {}; } catch (e) { data = {}; }
  var title = data.title || '店舗から呼び出しです';
  var options = {
    body: data.body || '受付画面を開いて「応答する」を押してください。',
    tag: 'almighty-call',
    renotify: true,
    requireInteraction: true,
    icon: '/reception-icon.png',
    badge: '/reception-icon.png',
    data: { url: data.url || '/reception' }
  };
  event.waitUntil(self.registration.showNotification(title, options));
});
self.addEventListener('notificationclick', function (event) {
  event.notification.close();
  var url = (event.notification.data && event.notification.data.url) || '/reception';
  event.waitUntil(self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function (list) {
    for (var i = 0; i < list.length; i++) { if ('focus' in list[i]) return list[i].focus(); }
    return self.clients.openWindow(url);
  }));
});
