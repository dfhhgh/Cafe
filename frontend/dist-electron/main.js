"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const electron_1 = require("electron");
const promises_1 = __importDefault(require("node:fs/promises"));
const node_path_1 = __importDefault(require("node:path"));
const node_child_process_1 = require("node:child_process");
const isDev = process.env.VITE_DEV_SERVER_URL || !electron_1.app.isPackaged;
function repoRoot() {
    return node_path_1.default.resolve(electron_1.app.getAppPath(), '..');
}
function bridgePath() {
    return node_path_1.default.join(repoRoot(), 'Cafe', 'ide_bridge.py');
}
function createWindow() {
    const window = new electron_1.BrowserWindow({
        width: 1440,
        height: 920,
        minWidth: 1080,
        minHeight: 720,
        backgroundColor: '#130d0b',
        title: 'Cafe IDE',
        webPreferences: {
            preload: node_path_1.default.join(__dirname, 'preload.js'),
            contextIsolation: true,
            nodeIntegration: false
        }
    });
    if (isDev) {
        window.loadURL(process.env.VITE_DEV_SERVER_URL ?? 'http://127.0.0.1:5173');
    }
    else {
        window.loadFile(node_path_1.default.join(electron_1.app.getAppPath(), 'dist', 'index.html'));
    }
}
async function listDirectory(dirPath) {
    const entries = await promises_1.default.readdir(dirPath, { withFileTypes: true });
    return entries
        .filter((entry) => !entry.name.startsWith('.') && entry.name !== 'node_modules')
        .map((entry) => ({
        name: entry.name,
        path: node_path_1.default.join(dirPath, entry.name),
        type: entry.isDirectory() ? 'folder' : 'file'
    }))
        .sort((a, b) => Number(b.type === 'file') - Number(a.type === 'file') || a.name.localeCompare(b.name));
}
function runCompiler(source, action, outputPath) {
    return new Promise((resolve) => {
        const child = (0, node_child_process_1.spawn)('python', [bridgePath()], {
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
            }
            catch {
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
electron_1.app.whenReady().then(() => {
    electron_1.ipcMain.handle('dialog:openFolder', async () => {
        const result = await electron_1.dialog.showOpenDialog({ properties: ['openDirectory'] });
        return result.canceled ? null : result.filePaths[0];
    });
    electron_1.ipcMain.handle('fs:listDirectory', (_event, dirPath) => listDirectory(dirPath));
    electron_1.ipcMain.handle('fs:readFile', (_event, filePath) => promises_1.default.readFile(filePath, 'utf-8'));
    electron_1.ipcMain.handle('fs:writeFile', (_event, filePath, content) => promises_1.default.writeFile(filePath, content, 'utf-8'));
    electron_1.ipcMain.handle('fs:createFile', async (_event, filePath) => {
        await promises_1.default.mkdir(node_path_1.default.dirname(filePath), { recursive: true });
        await promises_1.default.writeFile(filePath, '', { flag: 'wx' });
        return filePath;
    });
    electron_1.ipcMain.handle('fs:createFolder', async (_event, folderPath) => {
        await promises_1.default.mkdir(folderPath, { recursive: true });
        return folderPath;
    });
    electron_1.ipcMain.handle('compiler:run', (_event, source, action, outputPath) => runCompiler(source, action, outputPath));
    createWindow();
});
electron_1.app.on('window-all-closed', () => {
    if (process.platform !== 'darwin')
        electron_1.app.quit();
});
