#!/usr/bin/env node
const { spawnSync } = require('child_process');

const args = process.argv.slice(2);
const candidates = ['python3', 'python', 'py'];
let found = false;

for (const cmd of candidates) {
  const result = spawnSync(cmd, args, { stdio: 'inherit' });
  if (result.status === 0 || result.status === null) {
    found = true;
    process.exit(result.status || 0);
  }
}
console.error('No suitable Python interpreter found (tried python3, python, py)');
process.exit(1); 