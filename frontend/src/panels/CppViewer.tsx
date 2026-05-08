import Editor from '@monaco-editor/react';
import type { ThemeMode } from '../types';

interface CppViewerProps {
  source: string;
  themeMode: ThemeMode;
}

export function CppViewer({ source, themeMode }: CppViewerProps) {
  return (
    <div className="h-full border-l border-latte/10 bg-roast">
      <div className="flex h-10 items-center border-b border-latte/10 px-3 text-xs font-semibold uppercase tracking-wider text-latte">
        Generated C++
      </div>
      <Editor
        height="calc(100% - 2.5rem)"
        language="cpp"
        value={source || '// Generate C++ to view output.cpp here.'}
        theme={themeMode === 'dark' ? 'vs-dark' : 'light'}
        options={{
          readOnly: true,
          fontSize: 13,
          minimap: { enabled: false },
          lineNumbers: 'on',
          automaticLayout: true,
          wordWrap: 'on'
        }}
      />
    </div>
  );
}
