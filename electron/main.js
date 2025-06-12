// electron/main.js - Targeted cleanup version
const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow = null;
let splashWindow = null;
let backendProcess = null;

function killSpecificPorts() {
  console.log('🔄 Killing only Atlas ports (3011, 8000)...');

  return new Promise((resolve) => {
    const killPorts = spawn('npx', ['kill-port', '3011', '8000'], {
      cwd: path.join(__dirname, '..'),
      stdio: 'ignore', // Hide console output
      shell: true,
      windowsHide: true // Hide the console window on Windows
    });

    const timeout = setTimeout(() => {
      console.log('⏰ Port cleanup timeout');
      resolve();
    }, 3000);

    killPorts.on('close', (code) => {
      clearTimeout(timeout);
      console.log(`✅ Atlas ports cleaned (code: ${code})`);
      resolve();
    });

    killPorts.on('error', (error) => {
      clearTimeout(timeout);
      console.log(`⚠️ Port cleanup error: ${error.message}`);
      resolve();
    });
  });
}

function killAtlasBackend() {
  console.log('🔄 Killing Atlas backend only...');

  return new Promise((resolve) => {
    let killCommand, killArgs;

    if (process.platform === 'win32') {
      // Only kill Python processes running uvicorn with main:app on port 8000
      killCommand = 'taskkill';
      killArgs = ['/F', '/FI', 'COMMANDLINE eq *uvicorn*main:app*8000*'];
    } else {
      // Unix: kill processes with uvicorn and port 8000 in command line
      killCommand = 'pkill';
      killArgs = ['-f', 'uvicorn.*main:app.*8000'];
    }

    const killProcess = spawn(killCommand, killArgs, {
      stdio: 'ignore', // Hide console output
      shell: true,
      windowsHide: true // Hide the console window on Windows
    });

    const timeout = setTimeout(() => {
      console.log('⏰ Backend kill timeout (this is normal)');
      resolve();
    }, 2000);

    killProcess.on('close', (code) => {
      clearTimeout(timeout);
      if (code === 0) {
        console.log(`✅ Atlas backend killed successfully`);
      } else {
        console.log(`ℹ️ No Atlas backend processes found (code: ${code})`);
      }
      resolve();
    });

    killProcess.on('error', (error) => {
      clearTimeout(timeout);
      console.log(`ℹ️ Backend kill completed (${error.message})`);
      resolve();
    });
  });
}

async function targetedCleanup() {
  console.log('🧹 Starting targeted Atlas cleanup...');

  // First try to kill the tracked backend process
  if (backendProcess && !backendProcess.killed) {
    try {
      console.log('Killing tracked backend process...');
      backendProcess.kill('SIGTERM');

      // Give it 2 seconds to gracefully shut down
      setTimeout(() => {
        if (backendProcess && !backendProcess.killed) {
          backendProcess.kill('SIGKILL');
        }
      }, 2000);
    } catch (error) {
      console.log('Error killing tracked backend:', error.message);
    }
  }

  // Then clean up ports and any remaining Atlas processes
  await killSpecificPorts();
  await killAtlasBackend();

  console.log('✅ Targeted cleanup completed');
}

function startBackendProcess() {
  console.log('🚀 Starting Atlas backend process...');

  // Start the backend as a child process we can track
  backendProcess = spawn('python', ['-m', 'uvicorn', 'main:app', '--reload', '--port', '8000'], {
    cwd: path.join(__dirname, '..', 'backend'),
    stdio: ['ignore', 'pipe', 'pipe'],
    shell: true,
    windowsHide: true // Hide the console window on Windows
  });

  backendProcess.stdout.on('data', (data) => {
    console.log(`Backend: ${data}`);
  });

  backendProcess.stderr.on('data', (data) => {
    console.error(`Backend Error: ${data}`);
  });

  backendProcess.on('close', (code) => {
    console.log(`Backend process exited with code ${code}`);
    backendProcess = null;
  });

  backendProcess.on('error', (error) => {
    console.error('Backend process error:', error);
    backendProcess = null;
  });

  return backendProcess;
}

function createSplashWindow() {
  splashWindow = new BrowserWindow({
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

  splashWindow.loadFile(path.join(__dirname, 'splash.html'));
  splashWindow.show();

  return splashWindow;
}

function createWindow() {
  mainWindow = new BrowserWindow({
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

  const url = 'http://localhost:3011';
  mainWindow.loadURL(url);

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    console.log('Window ready and shown');
  });

  // Handle window closed
  mainWindow.on('closed', async () => {
    console.log('Main window closed - cleaning up Atlas processes only');
    await targetedCleanup();
    mainWindow = null;
  });

  return mainWindow;
}

// App event handlers
app.whenReady().then(async () => {
  console.log('Electron app ready');

  // Clean up any existing Atlas processes first
  await targetedCleanup();

  // Show splash screen
  const splash = createSplashWindow();

  // Create main window
  setTimeout(() => {
    const main = createWindow();
    main.once('ready-to-show', () => {
      console.log('Main window ready - closing splash');
      if (splash && !splash.isDestroyed()) {
        splash.close();
      }
    });
  }, 1500);
});

app.on('window-all-closed', async () => {
  console.log('All windows closed - cleaning up Atlas processes only');
  await targetedCleanup();

  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', async (event) => {
  console.log('App about to quit - cleaning up Atlas processes');
  event.preventDefault();

  await targetedCleanup();
  app.exit(0);
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// Handle any uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception:', error);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});

// Cleanup on process signals
process.on('SIGINT', async () => {
  console.log('SIGINT received - cleaning up Atlas processes only');
  await targetedCleanup();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  console.log('SIGTERM received - cleaning up Atlas processes only');
  await targetedCleanup();
  process.exit(0);
});

console.log('Electron main process started with targeted cleanup');