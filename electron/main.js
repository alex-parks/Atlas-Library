// electron/main.js - SIMPLE VERSION
const { app, BrowserWindow } = require('electron');
const path = require('path');

function createSplashWindow() {
  const splash = new BrowserWindow({
    width: 800,
    height: 600,
    frame: false,
    alwaysOnTop: true,
    transparent: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  // Load the splash HTML file
  splash.loadFile(path.join(__dirname, 'splash.html'));
  splash.show();

  return splash;
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: true,
      allowRunningInsecureContent: false,
      experimentalFeatures: false
    },
    titleBarStyle: 'default',
    show: false
  });

  // Just load the frontend URL - assume it's already running
  const url = 'http://localhost:3011';
  console.log(`Loading URL: ${url}`);

  win.loadURL(url);

  // Show when ready (splash will be closed by main logic)
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

  // DevTools can be opened manually with Cmd+Option+I if needed
  // Removed automatic opening to avoid security warnings

  return win;
}

// App event handlers
app.whenReady().then(() => {
  console.log('Electron app ready, showing splash screen...');
  
  // Show splash screen first
  const splash = createSplashWindow();
  
  // Create main window after a short delay
  setTimeout(() => {
    const mainWin = createWindow();
    mainWin.once('ready-to-show', () => {
      console.log('Main window ready - closing splash');
      splash.close();
    });
  }, 1500); // Show loading for 1.5 seconds minimum
});

app.on('window-all-closed', () => {
  console.log('All windows closed - killing backend processes');
  
  // Kill the backend and frontend processes
  const { spawn } = require('child_process');
  const killPorts = spawn('npx', ['kill-port', '3011', '8000'], {
    cwd: path.join(__dirname, '..'),
    stdio: 'inherit'
  });
  
  killPorts.on('close', () => {
    console.log('Ports cleaned up');
    if (process.platform !== 'darwin') {
      app.quit();
    }
  });
  
  // Force quit after 3 seconds if kill-port doesn't work
  setTimeout(() => {
    if (process.platform !== 'darwin') {
      app.quit();
    }
  }, 3000);
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

console.log('Electron main process started');