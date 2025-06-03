// electron/main.js - Fixed version
const { app, BrowserWindow } = require('electron');
const path = require('path');

function createWindow() {
  const win = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: false, // Allow loading local resources
      // Add cache directory to fix cache errors
      additionalArguments: ['--disable-web-security', '--disable-features=VizDisplayCompositor']
    },
    titleBarStyle: 'default',
    show: false,
    icon: path.join(__dirname, 'icon.png') // Add an icon if you have one
  });

  // Load the React app - using the correct port from your vite config
  const isDev = process.env.NODE_ENV !== 'production';

  // Try multiple common Vite ports in order
  const possiblePorts = [3011, 3010, 3000, 5173, 5174];
  let url = isDev ? `http://localhost:3011` : `file://${path.join(__dirname, '../frontend/dist/index.html')}`;

  console.log(`Loading URL: ${url}`);
  win.loadURL(url);

  // Show when ready to prevent white flash
  win.once('ready-to-show', () => {
    win.show();
    console.log('Window ready and shown');
  });

  // Handle loading errors - try next port if current one fails
  win.webContents.on('did-fail-load', async (event, errorCode, errorDescription, validatedURL) => {
    console.error(`Failed to load ${validatedURL}: ${errorDescription} (${errorCode})`);

    if (isDev && possiblePorts.length > 1) {
      // Remove the failed port and try the next one
      const currentPort = possiblePorts.shift();
      const nextPort = possiblePorts[0];

      if (nextPort) {
        console.log(`Trying next port: ${nextPort}`);
        const nextUrl = `http://localhost:${nextPort}`;
        win.loadURL(nextUrl);
      }
    }
  });

  // Open DevTools in development
  if (isDev) {
    win.webContents.openDevTools();
  }

  // Handle window closed
  win.on('closed', () => {
    console.log('Window closed');
  });

  return win;
}

// Disable hardware acceleration BEFORE app is ready
app.disableHardwareAcceleration();

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
  console.log('App activated');
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// Security: Prevent new window creation
app.on('web-contents-created', (event, contents) => {
  contents.on('new-window', (event, navigationUrl) => {
    event.preventDefault();
    console.log(`Blocked new window: ${navigationUrl}`);
  });
});

// Handle certificate errors in development
app.on('certificate-error', (event, webContents, url, error, certificate, callback) => {
  if (process.env.NODE_ENV !== 'production') {
    // In development, ignore certificate errors
    event.preventDefault();
    callback(true);
  } else {
    // In production, use default behavior
    callback(false);
  }
});

console.log('Electron main process started');