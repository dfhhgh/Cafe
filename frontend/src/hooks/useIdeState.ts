import { useMemo, useState } from 'react';
import { sampleProgram } from '../utils/sampleProgram';
import type { CompilerAction, CompilerResult, Diagnostic, EditorTab, FileEntry, PanelTab, ThemeMode } from '../types';

const initialTab: EditorTab = {
  id: 'welcome.cafe',
  name: 'welcome.cafe',
  content: sampleProgram,
  dirty: false,
  language: 'cafe'
};

export function useIdeState() {
  const [tabs, setTabs] = useState<EditorTab[]>([initialTab]);
  const [activeTabId, setActiveTabId] = useState(initialTab.id);
  const [rootFolder, setRootFolder] = useState<string | null>(null);
  const [files, setFiles] = useState<FileEntry[]>([]);
  const [consoleLines, setConsoleLines] = useState<string[]>(['Cafe IDE ready. Warm compiler, fresh syntax.']);
  const [diagnostics, setDiagnostics] = useState<Diagnostic[]>([]);
  const [cppSource, setCppSource] = useState('');
  const [status, setStatus] = useState('Ready');
  const [panelTab, setPanelTab] = useState<PanelTab>('console');
  const [themeMode, setThemeMode] = useState<ThemeMode>('dark');
  const [cursor, setCursor] = useState({ line: 1, column: 1 });
  const [isBusy, setBusy] = useState(false);

  const activeTab = useMemo(() => tabs.find((tab) => tab.id === activeTabId) ?? tabs[0], [tabs, activeTabId]);

  function appendConsole(lines: string | string[]) {
    setConsoleLines((current) => [...current, ...(Array.isArray(lines) ? lines : [lines])]);
  }

  function updateActiveContent(content: string) {
    setTabs((current) =>
      current.map((tab) => (tab.id === activeTabId ? { ...tab, content, dirty: true } : tab))
    );
  }

  async function openFolder() {
    const folder = await window.cafeAPI.openFolder();
    if (!folder) return;
    setRootFolder(folder);
    const entries = await window.cafeAPI.listDirectory(folder);
    setFiles(entries);
    setStatus('Folder opened');
  }

  async function refreshFolder(folder = rootFolder) {
    if (!folder) return;
    setFiles(await window.cafeAPI.listDirectory(folder));
  }

  async function openFile(file: FileEntry) {
    if (file.type !== 'file') return;
    const content = await window.cafeAPI.readFile(file.path);
    const existing = tabs.find((tab) => tab.path === file.path);
    if (existing) {
      setActiveTabId(existing.id);
      return;
    }
    const tab: EditorTab = {
      id: file.path,
      path: file.path,
      name: file.name,
      content,
      dirty: false,
      language: 'cafe'
    };
    setTabs((current) => [...current, tab]);
    setActiveTabId(tab.id);
  }

  async function saveActiveFile() {
    if (!activeTab) return;
    const targetPath = activeTab.path ?? `${rootFolder ?? '.'}/${activeTab.name}`;
    await window.cafeAPI.writeFile(targetPath, activeTab.content);
    setTabs((current) =>
      current.map((tab) => (tab.id === activeTab.id ? { ...tab, path: targetPath, id: targetPath, dirty: false } : tab))
    );
    setActiveTabId(targetPath);
    await refreshFolder();
    setStatus('Saved');
    appendConsole(`Saved ${targetPath}`);
  }

  async function createFile() {
    if (!rootFolder) {
      appendConsole('Open a folder before creating files.');
      return;
    }
    const name = window.prompt('New Cafe file name', 'new_recipe.cafe');
    if (!name) return;
    const filePath = `${rootFolder}/${name}`;
    await window.cafeAPI.createFile(filePath);
    await refreshFolder();
    await openFile({ name, path: filePath, type: 'file' });
    appendConsole(`Created file ${filePath}`);
  }

  async function createFolder() {
    if (!rootFolder) {
      appendConsole('Open a folder before creating folders.');
      return;
    }
    const name = window.prompt('New folder name', 'recipes');
    if (!name) return;
    const folderPath = `${rootFolder}/${name}`;
    await window.cafeAPI.createFolder(folderPath);
    await refreshFolder();
    appendConsole(`Created folder ${folderPath}`);
  }

  function closeTab(tabId: string) {
    if (tabs.length === 1) return;
    const index = tabs.findIndex((tab) => tab.id === tabId);
    const nextTabs = tabs.filter((tab) => tab.id !== tabId);
    setTabs(nextTabs);
    if (activeTabId === tabId) {
      setActiveTabId(nextTabs[Math.max(0, index - 1)].id);
    }
  }

  async function runCompiler(action: CompilerAction) {
    if (!activeTab) return;
    setBusy(true);
    setStatus(action === 'run' ? 'Running' : action === 'compile' ? 'Compiling' : 'Generating C++');
    setPanelTab('console');
    try {
      const result: CompilerResult = await window.cafeAPI.runCompiler(activeTab.content, action, 'output.cpp');
      setDiagnostics(result.diagnostics ?? []);
      setCppSource(result.cppSource ?? '');
      appendConsole([
        `> ${action.toUpperCase()} ${activeTab.name}`,
        ...(result.logs ?? []),
        result.runtimeOutput ? `Runtime Output:\n${result.runtimeOutput}` : '',
        result.ok ? 'SUCCESS: Pipeline completed' : 'FAILED: See diagnostics'
      ].filter(Boolean));
      setStatus(result.ok ? 'Success' : 'Diagnostics');
      if (result.cppSource) setPanelTab(action === 'generate' ? 'cpp' : 'console');
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      setDiagnostics([{ stage: 'IDE', severity: 'error', message }]);
      appendConsole(`IDE Error: ${message}`);
      setStatus('Error');
    } finally {
      setBusy(false);
    }
  }

  return {
    tabs,
    activeTab,
    activeTabId,
    rootFolder,
    files,
    consoleLines,
    diagnostics,
    cppSource,
    status,
    panelTab,
    themeMode,
    cursor,
    isBusy,
    setActiveTabId,
    setPanelTab,
    setThemeMode,
    setCursor,
    updateActiveContent,
    openFolder,
    refreshFolder,
    openFile,
    createFile,
    createFolder,
    saveActiveFile,
    closeTab,
    runCompiler
  };
}
