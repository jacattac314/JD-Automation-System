// PWA Initialization and Install Prompt Handler

let deferredPrompt;
let isInstalled = false;

// Check if running in Electron
const isElectron = typeof window.electronAPI !== 'undefined';

// Check if app is already installed
if (window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true) {
    isInstalled = true;
    console.log('[PWA] Running as installed app');
}

// Register service worker (only in browser, not in Electron)
if ('serviceWorker' in navigator && !isElectron) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/service-worker.js')
            .then((registration) => {
                console.log('[PWA] Service Worker registered:', registration.scope);

                // Check for updates periodically
                setInterval(() => {
                    registration.update();
                }, 60000); // Check every minute

                // Handle service worker updates
                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing;

                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            // New service worker available
                            showUpdateNotification();
                        }
                    });
                });
            })
            .catch((error) => {
                console.error('[PWA] Service Worker registration failed:', error);
            });

        // Handle service worker messages
        navigator.serviceWorker.addEventListener('message', (event) => {
            console.log('[PWA] Message from service worker:', event.data);
        });
    });
} else if (isElectron) {
    console.log('[PWA] Running in Electron, skipping service worker registration');
} else {
    console.log('[PWA] Service Workers not supported');
}

// Listen for install prompt
window.addEventListener('beforeinstallprompt', (e) => {
    console.log('[PWA] Install prompt triggered');

    // Prevent the default prompt
    e.preventDefault();

    // Store the event for later use
    deferredPrompt = e;

    // Show custom install banner if not already installed
    if (!isInstalled && !isElectron) {
        showPWAInstallBanner();
    }
});

// Listen for app installed event
window.addEventListener('appinstalled', () => {
    console.log('[PWA] App was installed');
    isInstalled = true;
    hidePWAInstallBanner();
    showToast('success', 'App Installed', 'JD Automation has been installed to your device');
    deferredPrompt = null;
});

// Show PWA install banner
function showPWAInstallBanner() {
    const banner = document.getElementById('pwa-install-banner');
    if (banner) {
        // Check if user dismissed it recently (within 7 days)
        const dismissedTime = localStorage.getItem('pwa-banner-dismissed');
        if (dismissedTime) {
            const daysSinceDismissed = (Date.now() - parseInt(dismissedTime)) / (1000 * 60 * 60 * 24);
            if (daysSinceDismissed < 7) {
                console.log('[PWA] Banner dismissed recently, not showing');
                return;
            }
        }

        banner.style.display = 'block';
        setTimeout(() => {
            banner.classList.add('show');
        }, 100);
    }
}

// Hide PWA install banner
function hidePWAInstallBanner() {
    const banner = document.getElementById('pwa-install-banner');
    if (banner) {
        banner.classList.remove('show');
        setTimeout(() => {
            banner.style.display = 'none';
        }, 300);
    }
}

// Install PWA
async function installPWA() {
    if (!deferredPrompt) {
        console.log('[PWA] No install prompt available');
        showToast('info', 'Already Installed', 'App is already installed or browser does not support installation');
        return;
    }

    // Show the install prompt
    deferredPrompt.prompt();

    // Wait for the user's response
    const { outcome } = await deferredPrompt.userChoice;
    console.log(`[PWA] User response: ${outcome}`);

    if (outcome === 'accepted') {
        showToast('success', 'Installing...', 'JD Automation is being installed');
    } else {
        showToast('info', 'Installation Cancelled', 'You can install later from your browser menu');
    }

    // Clear the deferred prompt
    deferredPrompt = null;
    hidePWAInstallBanner();
}

// Dismiss PWA prompt
function dismissPWAPrompt() {
    localStorage.setItem('pwa-banner-dismissed', Date.now().toString());
    hidePWAInstallBanner();
    showToast('info', 'Reminder Dismissed', 'You can install later from Settings or your browser menu');
}

// Show update notification
function showUpdateNotification() {
    const updateToast = showToast(
        'info',
        'Update Available',
        'A new version is available. Click to update.',
        0  // Don't auto-dismiss
    );

    updateToast.style.cursor = 'pointer';
    updateToast.onclick = () => {
        // Tell service worker to skip waiting
        if (navigator.serviceWorker.controller) {
            navigator.serviceWorker.controller.postMessage({ type: 'SKIP_WAITING' });
        }

        // Reload the page
        window.location.reload();
    };
}

// Add install button to settings page
document.addEventListener('DOMContentLoaded', () => {
    // Add PWA install section to settings if not in Electron
    if (!isElectron && !isInstalled) {
        const settingsBody = document.querySelector('#settings-view .card-body');
        if (settingsBody) {
            const pwaSection = document.createElement('div');
            pwaSection.className = 'settings-section';
            pwaSection.innerHTML = `
                <h3>Progressive Web App</h3>
                <div class="form-group">
                    <p>Install JD Automation as a standalone app on your device for quick access.</p>
                    <button class="btn btn-primary" onclick="installPWA()">
                        📱 Install as App
                    </button>
                </div>
            `;
            settingsBody.appendChild(pwaSection);
        }
    }

    // Show app version in footer if in Electron
    if (isElectron && window.electronAPI && window.electronAPI.getAppVersion) {
        window.electronAPI.getAppVersion().then(version => {
            console.log('[Electron] App version:', version);
            const footer = document.querySelector('.sidebar-footer');
            if (footer) {
                const versionDiv = document.createElement('div');
                versionDiv.className = 'app-version';
                versionDiv.style.fontSize = '0.75rem';
                versionDiv.style.opacity = '0.7';
                versionDiv.style.marginTop = '8px';
                versionDiv.textContent = `v${version}`;
                footer.appendChild(versionDiv);
            }
        });
    }
});

// Detect online/offline status
window.addEventListener('online', () => {
    console.log('[PWA] Back online');
    showToast('success', 'Online', 'Connection restored');
});

window.addEventListener('offline', () => {
    console.log('[PWA] Gone offline');
    showToast('warning', 'Offline', 'You are now offline. Some features may be limited.');
});

// Log PWA status
console.log('[PWA] Initialization complete', {
    isElectron,
    isInstalled,
    serviceWorkerSupported: 'serviceWorker' in navigator,
    displayMode: window.matchMedia('(display-mode: standalone)').matches ? 'standalone' : 'browser'
});
