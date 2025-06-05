// electron/main.js - SIMPLE VERSION
const { app, BrowserWindow } = require('electron');
const path = require('path');

function createWindow() {
  const win = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: false
    },
    titleBarStyle: 'default',
    show: false
  });

  // Just load the frontend URL - assume it's already running
  const url = 'http://localhost:3011';
  console.log(`Loading URL: ${url}`);

  win.loadURL(url);

  // Show when ready
  win.once('ready-to-show', () => {
    win.show();
    console.log('Window ready and shown');
  });

  // Handle loading errors - retry once
  win.webContents.on('did-fail-load', (event, errorCode, errorDescription, validatedURL) => {
    console.error(`Failed to load ${validatedURL}: ${errorDescription}`);
    console.log('Retrying in 3 seconds...');
    setTimeout(() => {
      win.loadURL(url);
    }, 3000);
  });

  // Open DevTools in development
  if (process.env.NODE_ENV !== 'production') {
    win.webContents.openDevTools();
  }

  return win;
}

// App event handlers
app.whenReady().then(() => {
  console.log('Electron app ready, creating window...');
  createWindow();
});

app.on('window-all-closed', () => {
  console.log('All windows closed');
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

console.log('Electron main process started');