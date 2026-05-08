import { CheckCircle2, Coffee, FileCode2 } from 'lucide-react';
import type { Diagnostic, EditorTab } from '../types';

interface StatusBarProps {
  tab?: EditorTab;
  status: string;
  diagnostics: Diagnostic[];
  cursor: { line: number; column: number };
}

export function StatusBar({ tab, status, diagnostics, cursor }: StatusBarProps) {
  const errorCount = diagnostics.filter((diagnostic) => diagnostic.severity === 'error').length;
  return (
    <footer className="flex h-7 items-center justify-between border-t border-latte/10 bg-mocha px-3 text-xs text-crema">
      <div className="flex items-center gap-4">
        <span className="flex items-center gap-1.5">
          <Coffee size={14} />
          Cafe~
        </span>
        <span className="flex items-center gap-1.5">
          <FileCode2 size={14} />
          {tab?.name ?? 'No file'}
        </span>
        <span>Ln {cursor.line}, Col {cursor.column}</span>
      </div>
      <div className="flex items-center gap-4">
        <span>{errorCount ? `${errorCount} diagnostic${errorCount > 1 ? 's' : ''}` : 'No diagnostics'}</span>
        <span className="flex items-center gap-1.5">
          <CheckCircle2 size={14} />
          {status}
        </span>
        <span>Language: Cafe</span>
      </div>
    </footer>
  );
}
