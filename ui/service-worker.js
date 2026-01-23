// JD Automation System - Service Worker
// Provides offline support and caching for PWA

const CACHE_VERSION = 'jd-automation-v1.0.0';
const CACHE_NAME = `${CACHE_VERSION}-static`;
const DATA_CACHE_NAME = `${CACHE_VERSION}-data`;

// Files to cache on install
const STATIC_CACHE_URLS = [
    '/',
    '/index.html',
    '/styles.css',
    '/app.js',
    '/manifest.json',
    '/icons/icon-192x192.png',
    '/icons/icon-512x512.png'
];

// API endpoints that should use network-first strategy
const API_ENDPOINTS = [
    '/api/create-repo',
    '/api/validate-token',
    '/api/generate-spec',
    '/api/push-files',
    '/api/analyze-jd',
    '/health'
];

// Install event - cache static resources
self.addEventListener('install', (event) => {
    console.log('[Service Worker] Installing...');

    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('[Service Worker] Caching static files');
                // Don't fail if some files are missing
                return Promise.allSettled(
                    STATIC_CACHE_URLS.map(url =>
                        cache.add(url).catch(err => {
                            console.warn(`[Service Worker] Failed to cache ${url}:`, err);
                        })
                    )
                );
            })
            .then(() => {
                console.log('[Service Worker] Installed successfully');
                // Activate immediately
                return self.skipWaiting();
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('[Service Worker] Activating...');

    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName.startsWith('jd-automation-') && cacheName !== CACHE_NAME && cacheName !== DATA_CACHE_NAME) {
                        console.log('[Service Worker] Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            console.log('[Service Worker] Activated successfully');
            // Take control immediately
            return self.clients.claim();
        })
    );
});

// Fetch event - serve from cache when possible
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip cross-origin requests
    if (url.origin !== location.origin && !url.hostname.includes('127.0.0.1')) {
        return;
    }

    // API requests - network first, fall back to cache
    if (API_ENDPOINTS.some(endpoint => url.pathname.startsWith(endpoint))) {
        event.respondWith(networkFirstStrategy(request));
        return;
    }

    // Static files - cache first, fall back to network
    event.respondWith(cacheFirstStrategy(request));
});

// Cache-first strategy (for static assets)
async function cacheFirstStrategy(request) {
    const cachedResponse = await caches.match(request);

    if (cachedResponse) {
        console.log('[Service Worker] Serving from cache:', request.url);
        return cachedResponse;
    }

    try {
        const networkResponse = await fetch(request);

        // Cache successful responses
        if (networkResponse && networkResponse.status === 200) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }

        return networkResponse;
    } catch (error) {
        console.error('[Service Worker] Fetch failed:', error);

        // Return offline page if available
        const offlineResponse = await caches.match('/offline.html');
        if (offlineResponse) {
            return offlineResponse;
        }

        // Return generic offline response
        return new Response(
            '<html><body><h1>Offline</h1><p>You are currently offline. Please check your connection.</p></body></html>',
            {
                headers: { 'Content-Type': 'text/html' }
            }
        );
    }
}

// Network-first strategy (for API calls)
async function networkFirstStrategy(request) {
    try {
        const networkResponse = await fetch(request);

        // Cache successful responses
        if (networkResponse && networkResponse.status === 200) {
            const cache = await caches.open(DATA_CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }

        return networkResponse;
    } catch (error) {
        console.log('[Service Worker] Network failed, trying cache:', request.url);

        const cachedResponse = await caches.match(request);

        if (cachedResponse) {
            console.log('[Service Worker] Serving API response from cache');
            return cachedResponse;
        }

        // Return error response
        return new Response(
            JSON.stringify({
                success: false,
                error: 'offline',
                message: 'You are currently offline. This action requires an internet connection.'
            }),
            {
                status: 503,
                headers: { 'Content-Type': 'application/json' }
            }
        );
    }
}

// Handle messages from clients
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }

    if (event.data && event.data.type === 'CLEAR_CACHE') {
        event.waitUntil(
            caches.keys().then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => {
                        if (cacheName.startsWith('jd-automation-')) {
                            console.log('[Service Worker] Clearing cache:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            }).then(() => {
                event.ports[0].postMessage({ success: true });
            })
        );
    }
});

// Background sync for failed requests (if supported)
self.addEventListener('sync', (event) => {
    console.log('[Service Worker] Background sync:', event.tag);

    if (event.tag === 'sync-runs') {
        event.waitUntil(syncFailedRuns());
    }
});

async function syncFailedRuns() {
    // Implement sync logic for failed automation runs
    console.log('[Service Worker] Syncing failed runs...');
    // This would retry any failed requests stored in IndexedDB
    return Promise.resolve();
}

// Push notifications (for future use)
self.addEventListener('push', (event) => {
    console.log('[Service Worker] Push received:', event);

    const options = {
        body: event.data ? event.data.text() : 'Automation completed!',
        icon: '/icons/icon-192x192.png',
        badge: '/icons/icon-72x72.png',
        vibrate: [200, 100, 200],
        tag: 'jd-automation',
        requireInteraction: false
    };

    event.waitUntil(
        self.registration.showNotification('JD Automation System', options)
    );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
    console.log('[Service Worker] Notification click:', event);

    event.notification.close();

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then((clientList) => {
                // Focus existing window if available
                for (const client of clientList) {
                    if (client.url === '/' && 'focus' in client) {
                        return client.focus();
                    }
                }
                // Open new window if no existing window
                if (clients.openWindow) {
                    return clients.openWindow('/');
                }
            })
    );
});

console.log('[Service Worker] Script loaded');
