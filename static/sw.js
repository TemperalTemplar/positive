const CACHE_NAME = 'positive-v1';
const STATIC_ASSETS = [
  '/',
  '/login/',
  '/static/manifest.json',
];

// Install — cache static assets
self.addEventListener('install', function(e) {
  e.waitUntil(
    caches.open(CACHE_NAME).then(function(cache) {
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

// Activate — clean old caches
self.addEventListener('activate', function(e) {
  e.waitUntil(
    caches.keys().then(function(keys) {
      return Promise.all(
        keys.filter(function(k) { return k !== CACHE_NAME; })
            .map(function(k) { return caches.delete(k); })
      );
    })
  );
  self.clients.claim();
});

// Fetch — network first, fall back to cache
self.addEventListener('fetch', function(e) {
  // Only handle GET requests
  if (e.request.method !== 'GET') return;
  // Don't cache admin or media
  if (e.request.url.includes('/admin/') || e.request.url.includes('/media/')) return;

  e.respondWith(
    fetch(e.request)
      .then(function(response) {
        // Cache successful responses
        if (response && response.status === 200) {
          var clone = response.clone();
          caches.open(CACHE_NAME).then(function(cache) {
            cache.put(e.request, clone);
          });
        }
        return response;
      })
      .catch(function() {
        // Fall back to cache when offline
        return caches.match(e.request).then(function(cached) {
          if (cached) return cached;
          // Offline fallback for navigation
          if (e.request.mode === 'navigate') {
            return caches.match('/');
          }
        });
      })
  );
});
