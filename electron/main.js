// electron/main.js - Improved version with precise Atlas process targeting
const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn, exec } = require('child_process');

let mainWindow = null;
let splashWindow = null;
let backendProcess = null;

function killAtlasProcessesPrecise() {
  console.log('🎯 Killing Atlas processes precisely...');

  return new Promise((resolve) => {
    let command;

    if (process.platform === 'win32') {
      // Windows: Use WMIC to find processes by command line and kill only Atlas ones
      command = `
        for /f "tokens=2" %i in ('wmic process where "CommandLine like '%uvicorn%main:app%' and CommandLine like '%8000%'" get ProcessId /format:value ^| find "ProcessId"') do (
          if not "%i"=="" taskkill /F /PID %i
        )
      `;
    } else {
      // Unix: More precise process killing
      command = `pkill -f "uvicorn.*main:app.*--port.*8000"`;
    }

    exec(command, { shell: true }, (error, stdout, stderr) => {
      if (error) {
        console.log(`ℹ️ No Atlas backend processes found (normal if already stopped)`);
      } else {
        console.log(`✅ Atlas backend processes terminated`);
        if (stdout) console.log(`Output: ${stdout}`);
      }
      resolve();
    });
  });
}

function killAtlasPortsOnly() {
  console.log('🔌 Freeing Atlas ports (3011, 8000)...');

  return new Promise((resolve) => {
    const killPorts = spawn('npx', ['kill-port', '3011', '8000'], {
      cwd: path.join(__dirname, '..'),
      stdio: 'pipe',
      shell: true,
      windowsHide: true
    });

    let output = '';

    killPorts.stdout.on('data', (data) => {
      output += data.toString();
    });

    killPorts.stderr.on('data', (data) => {
      output += data.toString();
    });

    const timeout = setTimeout(() => {
      console.log('⏰ Port cleanup timeout');
      resolve();
    }, 5000);

    killPorts.on('close', (code) => {
      clearTimeout(timeout);
      if (output.includes('Process on port')) {
        console.log(`✅ Atlas ports freed`);
      } else {
        console.log(`ℹ️ Atlas ports were already free`);
      }
      resolve();
    });

    killPorts.on('error', (error) => {
      clearTimeout(timeout);
      console.log(`ℹ️ Port cleanup completed (${error.message})`);
      resolve();
    });
  });
}

function killAtlasProcessesByName() {
  console.log('🔍 Searching for Atlas-specific Python processes...');

  return new Promise((resolve) => {
    if (process.platform === 'win32') {
      // Use PowerShell to find and kill only Atlas processes
      const psCommand = `
        Get-WmiObject Win32_Process | 
        Where-Object { $_.CommandLine -like "*uvicorn*main:app*" -and $_.CommandLine -like "*8000*" } |
        ForEach-Object { 
          Write-Host "Killing Atlas process PID: $($_.ProcessId) - $($_.CommandLine)"
          Stop-Process -Id $_.ProcessId -Force 
        }
      `;

      exec(`powershell -Command "${psCommand}"`, (error, stdout, stderr) => {
        if (error) {
          console.log(`ℹ️ No Atlas processes found or already stopped`);
        } else {
          console.log(`✅ Atlas processes terminated`);
          if (stdout.trim()) console.log(stdout);
        }
        resolve();
      });
    } else {
      // Unix version - more precise
      exec(`pgrep -f "uvicorn.*main:app.*8000" | xargs -r kill -TERM`, (error, stdout, stderr) => {
        if (error) {
          console.log(`ℹ️ No Atlas processes found`);
        } else {
          console.log(`✅ Atlas processes terminated`);
        }
        resolve();
      });
    }
  });
}

async function preciseAtlasCleanup() {
  console.log('🧹 Starting precise Atlas cleanup...');

  // Step 1: Kill tracked backend process first
  if (backendProcess && !backendProcess.killed) {
    try {
      console.log('🎯 Terminating tracked backend process...');
      backendProcess.kill('SIGTERM');

      // Wait 2 seconds for graceful shutdown
      await new Promise(resolve => setTimeout(resolve, 2000));

      if (backendProcess && !backendProcess.killed) {
        backendProcess.kill('SIGKILL');
        console.log('💀 Force killed tracked backend process');
      }
    } catch (error) {
      console.log(`⚠️ Error with tracked process: ${error.message}`);
    }
  }

  // Step 2: Kill any remaining Atlas processes by command line
  await killAtlasProcessesByName();

  // Step 3: Free up the ports as backup
  await killAtlasPortsOnly();

  // Step 4: Final precise cleanup
  await killAtlasProcessesPrecise();

  console.log('✅ Precise Atlas cleanup completed');
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
    console.log('🪟 Main window ready and shown');
  });

  // Handle window closed
  mainWindow.on('closed', async () => {
    console.log('🚪 Main window closed - cleaning up Atlas processes');
    await preciseAtlasCleanup();
    mainWindow = null;
  });

  return mainWindow;
}

// App event handlers
app.whenReady().then(async () => {
  console.log('🚀 Electron app ready');

  // Show splash screen
  const splash = createSplashWindow();

  // Create main window (wait for services to be ready)
  setTimeout(() => {
    const main = createWindow();
    main.once('ready-to-show', () => {
      console.log('✨ Main window ready - closing splash');
      if (splash && !splash.isDestroyed()) {
        splash.close();
      }
    });
  }, 3000);
});

app.on('window-all-closed', async () => {
  console.log('🏁 All windows closed - cleaning up Atlas processes');
  await preciseAtlasCleanup();

  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', async (event) => {
  console.log('🛑 App about to quit - cleaning up Atlas processes');
  event.preventDefault();

  await preciseAtlasCleanup();
  app.exit(0);
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// Handle any uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('💥 Uncaught Exception:', error);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('🚫 Unhandled Rejection at:', promise, 'reason:', reason);
});

// Cleanup on process signals
process.on('SIGINT', async () => {
  console.log('⚡ SIGINT received - cleaning up Atlas processes');
  await preciseAtlasCleanup();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  console.log('⚡ SIGTERM received - cleaning up Atlas processes');
  await preciseAtlasCleanup();
  process.exit(0);
});

console.log('🎯 Electron main process started with precise Atlas cleanup');