"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const electron_1 = require("electron");
electron_1.contextBridge.exposeInMainWorld('cafeAPI', {
    openFolder: () => electron_1.ipcRenderer.invoke('dialog:openFolder'),
    listDirectory: (dirPath) => electron_1.ipcRenderer.invoke('fs:listDirectory', dirPath),
    readFile: (filePath) => electron_1.ipcRenderer.invoke('fs:readFile', filePath),
    writeFile: (filePath, content) => electron_1.ipcRenderer.invoke('fs:writeFile', filePath, content),
    createFile: (filePath) => electron_1.ipcRenderer.invoke('fs:createFile', filePath),
    createFolder: (folderPath) => electron_1.ipcRenderer.invoke('fs:createFolder', folderPath),
    runCompiler: (source, action, outputPath) => electron_1.ipcRenderer.invoke('compiler:run', source, action, outputPath)
});
