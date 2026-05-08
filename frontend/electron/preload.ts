import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('cafeAPI', {
  openFolder: () => ipcRenderer.invoke('dialog:openFolder'),
  listDirectory: (dirPath: string) => ipcRenderer.invoke('fs:listDirectory', dirPath),
  readFile: (filePath: string) => ipcRenderer.invoke('fs:readFile', filePath),
  writeFile: (filePath: string, content: string) => ipcRenderer.invoke('fs:writeFile', filePath, content),
  createFile: (filePath: string) => ipcRenderer.invoke('fs:createFile', filePath),
  createFolder: (folderPath: string) => ipcRenderer.invoke('fs:createFolder', folderPath),
  runCompiler: (source: string, action: 'generate' | 'compile' | 'run', outputPath: string) =>
    ipcRenderer.invoke('compiler:run', source, action, outputPath)
});
