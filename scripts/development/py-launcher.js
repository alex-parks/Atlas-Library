#!/usr/bin/env node
const { spawnSync } = require('child_process');
const os = require('os');

const args = process.argv.slice(2);
let cmd, cmdArgs;

if (os.platform() === 'win32') {
  cmd = 'py';
  cmdArgs = args;
} else {
  cmd = 'node';
  cmdArgs = ['../scripts/python3.js', ...args];
}

const result = spawnSync(cmd, cmdArgs, { stdio: 'inherit' });
process.exit(result.status); 