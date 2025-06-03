const { app, BrowserWindow } = require('electron');
const path = require('path');

function createWindow() {
  const win = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: false // Allow loading local resources
    },
    titleBarStyle: 'default',
    show: false,
    icon: path.join(__dirname, 'icon.png') // Add an icon if you have one
  });

  // Load the React app - using the correct port from your vite config
  const isDev = process.env.NODE_ENV !== 'production';
  const url = isDev ? 'http://localhost:3000' : `file://${path.join(__dirname, '../frontend/dist/index.html')}`;

  console.log(`Loading URL: ${url}`);
  win.loadURL(url);

  // Show when ready to prevent white flash
  win.once('ready-to-show', () => {
    win.show();
    console.log('Window ready and shown');
  });

  // Handle loading errors
  win.webContents.on('did-fail-load', (event, errorCode, errorDescription, validatedURL) => {
    console.error(`Failed to load ${validatedURL}: ${errorDescription} (${errorCode})`);
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

console.log('Electron main process started');