import { app, BrowserWindow, dialog, ipcMain } from 'electron';
import fs from 'node:fs/promises';
import path from 'node:path';
import { spawn } from 'node:child_process';

type CompilerAction = 'generate' | 'compile' | 'run';

const isDev = process.env.VITE_DEV_SERVER_URL || !app.isPackaged;

function repoRoot() {
  return path.resolve(app.getAppPath(), '..');
}

function bridgePath() {
  return path.join(repoRoot(), 'Cafe', 'ide_bridge.py');
}

function createWindow() {
  const window = new BrowserWindow({
    width: 1440,
    height: 920,
    minWidth: 1080,
    minHeight: 720,
    backgroundColor: '#130d0b',
    title: 'Cafe IDE',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  if (isDev) {
    window.loadURL(process.env.VITE_DEV_SERVER_URL ?? 'http://127.0.0.1:5173');
  } else {
    window.loadFile(path.join(app.getAppPath(), 'dist', 'index.html'));
  }
}

async function listDirectory(dirPath: string) {
  const entries = await fs.readdir(dirPath, { withFileTypes: true });
  return entries
    .filter((entry) => !entry.name.startsWith('.') && entry.name !== 'node_modules')
    .map((entry) => ({
      name: entry.name,
      path: path.join(dirPath, entry.name),
      type: entry.isDirectory() ? 'folder' : 'file'
    }))
    .sort((a, b) => Number(b.type === 'file') - Number(a.type === 'file') || a.name.localeCompare(b.name));
}

function runCompiler(source: string, action: CompilerAction, outputPath: string) {
  return new Promise((resolve) => {
    const child = spawn('python', [bridgePath()], {
      cwd: repoRoot(),
      stdio: ['pipe', 'pipe', 'pipe']
    });

    let stdout = '';
    let stderr = '';

    child.stdout.on('data', (chunk) => {
      stdout += chunk.toString();
    });
    child.stderr.on('data', (chunk) => {
      stderr += chunk.toString();
    });
    child.on('error', (error) => {
      resolve({
        ok: false,
        diagnostics: [{ stage: 'Bridge', severity: 'error', message: error.message }],
        logs: [`Bridge Error: ${error.message}`]
      });
    });
    child.on('close', () => {
      try {
        const parsed = JSON.parse(stdout || '{}');
        if (stderr.trim()) {
          parsed.logs = [...(parsed.logs ?? []), stderr.trim()];
        }
        resolve(parsed);
      } catch {
        resolve({
          ok: false,
          diagnostics: [{ stage: 'Bridge', severity: 'error', message: 'Invalid compiler bridge response' }],
          logs: [stderr || stdout]
        });
      }
    });

    child.stdin.write(JSON.stringify({ source, action, outputPath }));
    child.stdin.end();
  });
}

app.whenReady().then(() => {
  ipcMain.handle('dialog:openFolder', async () => {
    const result = await dialog.showOpenDialog({ properties: ['openDirectory'] });
    return result.canceled ? null : result.filePaths[0];
  });
  ipcMain.handle('fs:listDirectory', (_event, dirPath: string) => listDirectory(dirPath));
  ipcMain.handle('fs:readFile', (_event, filePath: string) => fs.readFile(filePath, 'utf-8'));
  ipcMain.handle('fs:writeFile', (_event, filePath: string, content: string) => fs.writeFile(filePath, content, 'utf-8'));
  ipcMain.handle('fs:createFile', async (_event, filePath: string) => {
    await fs.mkdir(path.dirname(filePath), { recursive: true });
    await fs.writeFile(filePath, '', { flag: 'wx' });
    return filePath;
  });
  ipcMain.handle('fs:createFolder', async (_event, folderPath: string) => {
    await fs.mkdir(folderPath, { recursive: true });
    return folderPath;
  });
  ipcMain.handle('compiler:run', (_event, source: string, action: CompilerAction, outputPath: string) =>
    runCompiler(source, action, outputPath)
  );

  createWindow();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
