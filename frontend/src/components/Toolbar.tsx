import { Coffee, FolderOpen, Hammer, Moon, Play, Save, Sun, TerminalSquare, Wand2 } from 'lucide-react';
import type { CompilerAction, ThemeMode } from '../types';

interface ToolbarProps {
  isBusy: boolean;
  themeMode: ThemeMode;
  onAction(action: CompilerAction): void;
  onOpenFolder(): void;
  onSave(): void;
  onToggleTheme(): void;
}

export function Toolbar({ isBusy, themeMode, onAction, onOpenFolder, onSave, onToggleTheme }: ToolbarProps) {
  const disabled = isBusy;
  return (
    <header className="flex h-12 items-center justify-between border-b border-latte/10 bg-roast/95 px-3 text-foam shadow-lg">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 rounded-md bg-mocha/60 px-3 py-1.5 text-sm font-semibold tracking-wide text-crema">
          <Coffee size={18} />
          Cafe IDE
        </div>
        <button className="toolbar-button" onClick={onOpenFolder} title="Open Folder">
          <FolderOpen size={16} />
          Open Folder
        </button>
        <button className="toolbar-button" onClick={onSave} title="Save">
          <Save size={16} />
          Save
        </button>
      </div>

      <div className="flex items-center gap-2">
        <button className="toolbar-button primary" disabled={disabled} onClick={() => onAction('run')} title="Run Cafe program">
          <Play size={16} />
          Run
        </button>
        <button className="toolbar-button" disabled={disabled} onClick={() => onAction('compile')} title="Compile generated C++">
          <Hammer size={16} />
          Compile
        </button>
        <button className="toolbar-button" disabled={disabled} onClick={() => onAction('generate')} title="Generate C++">
          <Wand2 size={16} />
          Generate C++
        </button>
        <div className="mx-1 h-6 w-px bg-latte/20" />
        <button className="icon-button" onClick={onToggleTheme} title="Switch theme">
          {themeMode === 'dark' ? <Sun size={17} /> : <Moon size={17} />}
        </button>
        <TerminalSquare className="text-latte" size={18} />
      </div>
    </header>
  );
}
