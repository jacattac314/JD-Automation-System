const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
    // Get app version
    getAppVersion: () => ipcRenderer.invoke('get-app-version'),

    // Check for updates
    checkForUpdates: () => ipcRenderer.invoke('check-for-updates'),

    // Platform information
    platform: process.platform,

    // Is this the Electron app?
    isElectron: true
});

// Log that preload script has loaded
console.log('Electron preload script loaded');
