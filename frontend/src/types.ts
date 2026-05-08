export type CompilerAction = 'generate' | 'compile' | 'run';
export type ThemeMode = 'dark' | 'latte';
export type PanelTab = 'console' | 'cpp' | 'diagnostics';

export interface FileEntry {
  name: string;
  path: string;
  type: 'file' | 'folder';
}

export interface EditorTab {
  id: string;
  path?: string;
  name: string;
  content: string;
  dirty: boolean;
  language: 'cafe';
}

export interface Diagnostic {
  stage: string;
  severity: 'error' | 'warning' | 'info';
  message: string;
  line?: number | null;
  column?: number | null;
}

export interface CompilerResult {
  ok: boolean;
  action: CompilerAction;
  diagnostics: Diagnostic[];
  logs: string[];
  tokens: Array<{ type: string; value: string; line: number; column: number }>;
  ast: string;
  cppSource: string;
  runtimeOutput: string;
  outputPath: string;
}

export interface CafeAPI {
  openFolder(): Promise<string | null>;
  listDirectory(dirPath: string): Promise<FileEntry[]>;
  readFile(filePath: string): Promise<string>;
  writeFile(filePath: string, content: string): Promise<void>;
  createFile(filePath: string): Promise<string>;
  createFolder(folderPath: string): Promise<string>;
  runCompiler(source: string, action: CompilerAction, outputPath: string): Promise<CompilerResult>;
}

declare global {
  interface Window {
    cafeAPI: CafeAPI;
  }
}
