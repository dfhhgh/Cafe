import { useEffect, useRef } from 'react';
import Editor, { OnMount, useMonaco } from '@monaco-editor/react';
import type * as monaco from 'monaco-editor';
import type { Diagnostic, ThemeMode } from '../types';
import { registerCafeLanguage } from './cafeLanguage';
import { registerCafeThemes } from './monacoThemes';

interface CafeEditorProps {
  value: string;
  diagnostics: Diagnostic[];
  themeMode: ThemeMode;
  onChange(value: string): void;
  onCursorChange(position: { line: number; column: number }): void;
}

export function CafeEditor({ value, diagnostics, themeMode, onChange, onCursorChange }: CafeEditorProps) {
  const monacoInstance = useMonaco();
  const editorRef = useRef<monaco.editor.IStandaloneCodeEditor | null>(null);

  const handleMount: OnMount = (editor, monacoInstance) => {
    editorRef.current = editor;
    registerCafeLanguage(monacoInstance);
    registerCafeThemes(monacoInstance);
    monacoInstance.editor.setTheme(themeMode === 'dark' ? 'cafe-dark' : 'cafe-latte');
    editor.onDidChangeCursorPosition((event) => {
      onCursorChange({ line: event.position.lineNumber, column: event.position.column });
    });
  };

  useEffect(() => {
    if (!monacoInstance || !editorRef.current) return;
    applyMarkers(editorRef.current, monacoInstance);
  }, [diagnostics, monacoInstance]);

  useEffect(() => {
    if (!monacoInstance) return;
    monacoInstance.editor.setTheme(themeMode === 'dark' ? 'cafe-dark' : 'cafe-latte');
  }, [themeMode, monacoInstance]);

  function applyMarkers(editor: monaco.editor.IStandaloneCodeEditor, monacoInstance: typeof monaco) {
    const model = editor.getModel();
    if (!model) return;
    const markers = diagnostics
      .filter((diagnostic) => diagnostic.line)
      .map((diagnostic) => ({
        severity: diagnostic.severity === 'warning' ? monacoInstance.MarkerSeverity.Warning : monacoInstance.MarkerSeverity.Error,
        message: `[${diagnostic.stage}] ${diagnostic.message}`,
        startLineNumber: diagnostic.line ?? 1,
        startColumn: diagnostic.column ?? 1,
        endLineNumber: diagnostic.line ?? 1,
        endColumn: (diagnostic.column ?? 1) + 1
      }));
    monacoInstance.editor.setModelMarkers(model, 'cafe', markers);
  }

  return (
    <Editor
      height="100%"
      language="cafe"
      value={value}
      theme={themeMode === 'dark' ? 'cafe-dark' : 'cafe-latte'}
      beforeMount={(monacoInstance) => {
        registerCafeLanguage(monacoInstance);
        registerCafeThemes(monacoInstance);
      }}
      onMount={(editor, monacoInstance) => {
        handleMount(editor, monacoInstance);
        applyMarkers(editor, monacoInstance);
      }}
      onChange={(nextValue) => onChange(nextValue ?? '')}
      options={{
        fontSize: 14,
        fontFamily: '"Cascadia Code", "Fira Code", Consolas, monospace',
        minimap: { enabled: true },
        lineNumbers: 'on',
        bracketPairColorization: { enabled: true },
        guides: { bracketPairs: true, indentation: true },
        smoothScrolling: true,
        cursorSmoothCaretAnimation: 'on',
        padding: { top: 18, bottom: 18 },
        wordWrap: 'on',
        automaticLayout: true,
        tabSize: 4
      }}
    />
  );
}
