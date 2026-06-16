// SafePath AI - Service Worker for offline support
const CACHE_NAME = 'safepath-v1';
const OFFLINE_URLS = [
    '/',
    '/sos/',
    '/siren/',
    '/fake-call/',
    '/self-defense/',
    '/legal-rights/',
    '/safety-tips/',
    '/static/js/zero_data_sos.js',
];

// Install: cache critical pages
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => cache.addAll(OFFLINE_URLS))
    );
    self.skipWaiting();
});

// Activate: clean old caches
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(keys => 
            Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
        )
    );
    self.clients.claim();
});

// Fetch: network first, fallback to cache
self.addEventListener('fetch', event => {
    event.respondWith(
        fetch(event.request).catch(() => caches.match(event.request))
    );
});
