import { useIdeState } from './hooks/useIdeState';
import { Toolbar } from './components/Toolbar';
import { ExplorerPanel } from './panels/ExplorerPanel';
import { Tabs } from './components/Tabs';
import { CafeEditor } from './editor/CafeEditor';
import { CppViewer } from './panels/CppViewer';
import { OutputPanel } from './panels/OutputPanel';
import { StatusBar } from './components/StatusBar';

export function App() {
  const ide = useIdeState();
  const showCpp = ide.cppSource.length > 0;

  return (
    <div className={`h-screen overflow-hidden ${ide.themeMode === 'dark' ? 'theme-dark' : 'theme-latte'}`}>
      <div className="flex h-full flex-col bg-app text-foam">
        <Toolbar
          isBusy={ide.isBusy}
          themeMode={ide.themeMode}
          onAction={ide.runCompiler}
          onOpenFolder={ide.openFolder}
          onSave={ide.saveActiveFile}
          onToggleTheme={() => ide.setThemeMode(ide.themeMode === 'dark' ? 'latte' : 'dark')}
        />

        <div className="flex min-h-0 flex-1">
          <ExplorerPanel
            rootFolder={ide.rootFolder}
            files={ide.files}
            onOpenFolder={ide.openFolder}
            onOpenFile={ide.openFile}
            onRefresh={() => void ide.refreshFolder()}
            onCreateFile={ide.createFile}
            onCreateFolder={ide.createFolder}
          />

          <main className="flex min-w-0 flex-1 flex-col bg-roast/95">
            <Tabs tabs={ide.tabs} activeTabId={ide.activeTabId} onSelect={ide.setActiveTabId} onClose={ide.closeTab} />

            <div className="grid min-h-0 flex-1" style={{ gridTemplateColumns: showCpp ? 'minmax(0, 1.1fr) minmax(360px, 0.9fr)' : 'minmax(0, 1fr)' }}>
              <CafeEditor
                value={ide.activeTab?.content ?? ''}
                diagnostics={ide.diagnostics}
                themeMode={ide.themeMode}
                onChange={ide.updateActiveContent}
                onCursorChange={ide.setCursor}
              />
              {showCpp ? <CppViewer source={ide.cppSource} themeMode={ide.themeMode} /> : null}
            </div>

            <OutputPanel
              activeTab={ide.panelTab}
              consoleLines={ide.consoleLines}
              diagnostics={ide.diagnostics}
              onTabChange={ide.setPanelTab}
            />
          </main>
        </div>

        <StatusBar tab={ide.activeTab} status={ide.status} diagnostics={ide.diagnostics} cursor={ide.cursor} />
      </div>
    </div>
  );
}
