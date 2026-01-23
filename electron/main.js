const { app, BrowserWindow, ipcMain, dialog, Menu } = require('electron');
const { autoUpdater } = require('electron-updater');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');
const log = require('electron-log');

// Configure logging
log.transports.file.level = 'info';
autoUpdater.logger = log;

let mainWindow;
let pythonProcess;
const PYTHON_PORT = 8000;
const PYTHON_HOST = '127.0.0.1';

// Determine if we're in development or production
const isDev = !app.isPackaged;

// Get the correct Python executable path
function getPythonPath() {
    if (isDev) {
        // In development, use system Python
        return process.platform === 'win32' ? 'python' : 'python3';
    } else {
        // In production, use bundled Python
        const platform = process.platform;
        if (platform === 'win32') {
            return path.join(process.resourcesPath, 'python', 'python.exe');
        } else if (platform === 'darwin') {
            return path.join(process.resourcesPath, 'python', 'bin', 'python3');
        } else {
            return path.join(process.resourcesPath, 'python', 'bin', 'python3');
        }
    }
}

// Get the application root path
function getAppPath() {
    if (isDev) {
        return path.join(__dirname, '..');
    } else {
        return path.join(process.resourcesPath, 'app');
    }
}

// Start Python backend server
function startPythonServer() {
    return new Promise((resolve, reject) => {
        const pythonPath = getPythonPath();
        const appPath = getAppPath();

        log.info('Starting Python server...');
        log.info('Python path:', pythonPath);
        log.info('App path:', appPath);

        // Start uvicorn server
        pythonProcess = spawn(pythonPath, [
            '-m', 'uvicorn',
            'api.server:app',
            '--host', PYTHON_HOST,
            '--port', PYTHON_PORT.toString()
        ], {
            cwd: appPath,
            env: { ...process.env }
        });

        pythonProcess.stdout.on('data', (data) => {
            log.info(`Python: ${data}`);
        });

        pythonProcess.stderr.on('data', (data) => {
            log.error(`Python Error: ${data}`);
        });

        pythonProcess.on('close', (code) => {
            log.info(`Python process exited with code ${code}`);
            pythonProcess = null;
        });

        // Wait for server to be ready
        const checkServer = setInterval(() => {
            http.get(`http://${PYTHON_HOST}:${PYTHON_PORT}/health`, (res) => {
                if (res.statusCode === 200) {
                    clearInterval(checkServer);
                    log.info('Python server is ready');
                    resolve();
                }
            }).on('error', () => {
                // Server not ready yet, keep checking
            });
        }, 500);

        // Timeout after 30 seconds
        setTimeout(() => {
            clearInterval(checkServer);
            reject(new Error('Python server failed to start'));
        }, 30000);
    });
}

// Stop Python server
function stopPythonServer() {
    if (pythonProcess) {
        log.info('Stopping Python server...');
        pythonProcess.kill();
        pythonProcess = null;
    }
}

// Create the main application window
function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        minWidth: 1000,
        minHeight: 600,
        icon: path.join(__dirname, 'assets', 'icon.png'),
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            nodeIntegration: false,
            contextIsolation: true,
            webSecurity: true
        },
        backgroundColor: '#1a1a2e',
        show: false, // Don't show until ready
        titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default'
    });

    // Load the app
    mainWindow.loadURL(`http://${PYTHON_HOST}:${PYTHON_PORT}`);

    // Show window when ready
    mainWindow.once('ready-to-show', () => {
        mainWindow.show();

        // Check for updates (only in production)
        if (!isDev) {
            setTimeout(() => {
                autoUpdater.checkForUpdatesAndNotify();
            }, 3000);
        }
    });

    // Open DevTools in development
    if (isDev) {
        mainWindow.webContents.openDevTools();
    }

    // Handle window close
    mainWindow.on('closed', () => {
        mainWindow = null;
    });

    // Create menu
    createMenu();
}

// Create application menu
function createMenu() {
    const template = [
        {
            label: 'File',
            submenu: [
                { role: 'quit' }
            ]
        },
        {
            label: 'Edit',
            submenu: [
                { role: 'undo' },
                { role: 'redo' },
                { type: 'separator' },
                { role: 'cut' },
                { role: 'copy' },
                { role: 'paste' },
                { role: 'selectAll' }
            ]
        },
        {
            label: 'View',
            submenu: [
                { role: 'reload' },
                { role: 'forceReload' },
                { type: 'separator' },
                { role: 'resetZoom' },
                { role: 'zoomIn' },
                { role: 'zoomOut' },
                { type: 'separator' },
                { role: 'togglefullscreen' }
            ]
        },
        {
            label: 'Help',
            submenu: [
                {
                    label: 'About',
                    click: () => {
                        dialog.showMessageBox(mainWindow, {
                            type: 'info',
                            title: 'JD Automation System',
                            message: 'JD Automation System',
                            detail: `Version: ${app.getVersion()}\n\nTransform job descriptions into fully implemented projects.`,
                            buttons: ['OK']
                        });
                    }
                },
                {
                    label: 'Check for Updates',
                    click: () => {
                        if (!isDev) {
                            autoUpdater.checkForUpdates();
                        } else {
                            dialog.showMessageBox(mainWindow, {
                                type: 'info',
                                title: 'Updates',
                                message: 'Auto-update is disabled in development mode',
                                buttons: ['OK']
                            });
                        }
                    }
                }
            ]
        }
    ];

    // Add DevTools toggle in development
    if (isDev) {
        template.push({
            label: 'Developer',
            submenu: [
                { role: 'toggleDevTools' }
            ]
        });
    }

    const menu = Menu.buildFromTemplate(template);
    Menu.setApplicationMenu(menu);
}

// Auto-updater events
autoUpdater.on('checking-for-update', () => {
    log.info('Checking for updates...');
});

autoUpdater.on('update-available', (info) => {
    log.info('Update available:', info.version);
    dialog.showMessageBox(mainWindow, {
        type: 'info',
        title: 'Update Available',
        message: `A new version ${info.version} is available!`,
        detail: 'The update will be downloaded in the background.',
        buttons: ['OK']
    });
});

autoUpdater.on('update-not-available', () => {
    log.info('No updates available');
});

autoUpdater.on('error', (err) => {
    log.error('Error in auto-updater:', err);
});

autoUpdater.on('download-progress', (progressObj) => {
    const message = `Download speed: ${progressObj.bytesPerSecond} - Downloaded ${progressObj.percent.toFixed(2)}%`;
    log.info(message);
});

autoUpdater.on('update-downloaded', (info) => {
    log.info('Update downloaded:', info.version);
    dialog.showMessageBox(mainWindow, {
        type: 'info',
        title: 'Update Ready',
        message: 'Update downloaded. Restart to apply?',
        buttons: ['Restart', 'Later']
    }).then((result) => {
        if (result.response === 0) {
            autoUpdater.quitAndInstall();
        }
    });
});

// App lifecycle events
app.whenReady().then(async () => {
    try {
        log.info('App starting...');
        await startPythonServer();
        createWindow();
    } catch (error) {
        log.error('Failed to start app:', error);
        dialog.showErrorBox(
            'Startup Error',
            `Failed to start the application: ${error.message}\n\nPlease check the logs for more details.`
        );
        app.quit();
    }
});

app.on('window-all-closed', () => {
    stopPythonServer();
    app.quit();
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});

app.on('before-quit', () => {
    stopPythonServer();
});

// IPC handlers
ipcMain.handle('get-app-version', () => {
    return app.getVersion();
});

ipcMain.handle('check-for-updates', () => {
    if (!isDev) {
        autoUpdater.checkForUpdates();
    }
    return { success: true };
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
    log.error('Uncaught exception:', error);
});

process.on('unhandledRejection', (error) => {
    log.error('Unhandled rejection:', error);
});
