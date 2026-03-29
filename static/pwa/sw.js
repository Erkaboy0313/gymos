const CACHE_NAME = "gymos-v1";
const OFFLINE_URL = "/static_root/pwa/offline.html";

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll([
      OFFLINE_URL
    ]))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") {
    return;
  }

  event.respondWith(
    fetch(event.request).catch(async () => {
      if (event.request.mode === "navigate") {
        const cache = await caches.open(CACHE_NAME);
        return await cache.match(OFFLINE_URL);
      }
      throw new Error("Network error");
    })
  );
});