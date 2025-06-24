#!/usr/bin/env node
// scripts/cleanup-atlas.js - Standalone Atlas process cleanup script

const { spawn, exec } = require('child_process');

function killAtlasProcessesPrecise() {
  console.log('🎯 Searching for Atlas backend processes...');

  return new Promise((resolve) => {
    if (process.platform === 'win32') {
      // Windows: Use PowerShell to find and kill only Atlas processes
      const psCommand = `
        $processes = Get-WmiObject Win32_Process | Where-Object { 
          $_.CommandLine -like "*uvicorn*main:app*" -and $_.CommandLine -like "*8000*" 
        }
        if ($processes) {
          foreach ($proc in $processes) {
            Write-Host "🎯 Killing Atlas process PID: $($proc.ProcessId)"
            Write-Host "   Command: $($proc.CommandLine)"
            Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
          }
          Write-Host "✅ $($processes.Count) Atlas process(es) terminated"
        } else {
          Write-Host "ℹ️ No Atlas backend processes found"
        }
      `;

      exec(`powershell -Command "${psCommand}"`, (error, stdout, stderr) => {
        if (stdout) console.log(stdout);
        if (stderr && !stderr.includes('Cannot find')) console.error(stderr);
        resolve();
      });
    } else {
      // Unix: More precise process killing
      exec(`pgrep -f "uvicorn.*main:app.*8000"`, (error, stdout, stderr) => {
        if (error) {
          console.log('ℹ️ No Atlas backend processes found');
          resolve();
          return;
        }

        const pids = stdout.trim().split('\n').filter(pid => pid);
        if (pids.length > 0) {
          console.log(`🎯 Found ${pids.length} Atlas process(es): ${pids.join(', ')}`);
          exec(`kill -TERM ${pids.join(' ')}`, (killError) => {
            if (killError) {
              console.log('⚠️ Error killing processes:', killError.message);
            } else {
              console.log('✅ Atlas processes terminated');
            }
            resolve();
          });
        } else {
          console.log('ℹ️ No Atlas backend processes found');
          resolve();
        }
      });
    }
  });
}

function killAtlasPorts() {
  console.log('🔌 Freeing Atlas ports (3011, 8000)...');

  return new Promise((resolve) => {
    const killPorts = spawn('npx', ['kill-port', '3011', '8000'], {
      stdio: 'pipe',
      shell: true
    });

    let output = '';

    killPorts.stdout.on('data', (data) => {
      output += data.toString();
    });

    killPorts.stderr.on('data', (data) => {
      output += data.toString();
    });

    const timeout = setTimeout(() => {
      console.log('⏰ Port cleanup timeout (normal if ports are free)');
      resolve();
    }, 10000);

    killPorts.on('close', (code) => {
      clearTimeout(timeout);

      if (output.includes('Process on port')) {
        const matches = output.match(/Process on port \d+ killed/g);
        if (matches) {
          console.log(`✅ Ports freed: ${matches.join(', ')}`);
        }
      } else {
        console.log('ℹ️ No processes found on Atlas ports (already free)');
      }
      resolve();
    });

    killPorts.on('error', (error) => {
      clearTimeout(timeout);
      console.log(`⚠️ Port cleanup error: ${error.message}`);
      resolve();
    });
  });
}

function checkForAtlasProcesses() {
  console.log('🔍 Checking for remaining Atlas processes...');

  return new Promise((resolve) => {
    if (process.platform === 'win32') {
      const psCommand = `
        $processes = Get-WmiObject Win32_Process | Where-Object { 
          $_.CommandLine -like "*uvicorn*" -or 
          ($_.Name -eq "python.exe" -and $_.CommandLine -like "*main:app*") -or
          ($_.Name -eq "node.exe" -and $_.CommandLine -like "*3011*")
        }
        if ($processes) {
          foreach ($proc in $processes) {
            Write-Host "⚠️ Remaining process PID: $($proc.ProcessId) - $($proc.Name)"
            Write-Host "   Command: $($proc.CommandLine)"
          }
        } else {
          Write-Host "✅ No Atlas-related processes found"
        }
      `;

      exec(`powershell -Command "${psCommand}"`, (error, stdout, stderr) => {
        if (stdout) console.log(stdout);
        resolve();
      });
    } else {
      exec(`pgrep -f "(uvicorn|main:app|port.*3011)" || echo "✅ No Atlas-related processes found"`, (error, stdout, stderr) => {
        console.log(stdout || '✅ No Atlas-related processes found');
        resolve();
      });
    }
  });
}

async function main() {
  console.log('🧹 Blacksmith Atlas - Precise Process Cleanup');
  console.log('='.repeat(50));

  // Step 1: Kill Atlas backend processes
  await killAtlasProcessesPrecise();

  // Step 2: Free up ports
  await killAtlasPorts();

  // Step 3: Wait a moment for processes to fully terminate
  console.log('⏳ Waiting for processes to terminate...');
  await new Promise(resolve => setTimeout(resolve, 2000));

  // Step 4: Check for any remaining Atlas processes
  await checkForAtlasProcesses();

  console.log('='.repeat(50));
  console.log('✅ Atlas cleanup completed!');
  console.log('');
  console.log('You can now run:');
  console.log('  npm run dev    - to start Atlas again');
  console.log('  npm run cleanup - to run this cleanup script');
}

// Handle errors gracefully
process.on('uncaughtException', (error) => {
  console.error('💥 Error during cleanup:', error.message);
  process.exit(1);
});

process.on('unhandledRejection', (reason) => {
  console.error('🚫 Promise rejection:', reason);
  process.exit(1);
});

// Run the cleanup
main().catch(error => {
  console.error('❌ Cleanup failed:', error);
  process.exit(1);
});