import type * as monaco from 'monaco-editor';

export function registerCafeThemes(monacoInstance: typeof monaco) {
  monacoInstance.editor.defineTheme('cafe-dark', {
    base: 'vs-dark',
    inherit: true,
    rules: [
      { token: 'keyword', foreground: 'f0b36a', fontStyle: 'bold' },
      { token: 'type', foreground: 'd8b98a' },
      { token: 'constant', foreground: 'eebf78' },
      { token: 'number', foreground: 'f7d28b' },
      { token: 'string', foreground: 'f5d6aa' },
      { token: 'string.char', foreground: 'ffd19a' },
      { token: 'comment', foreground: '9f7a5f', fontStyle: 'italic' },
      { token: 'operator', foreground: 'c47a37' }
    ],
    colors: {
      'editor.background': '#130d0b',
      'editor.foreground': '#f6ead8',
      'editorLineNumber.foreground': '#7a5a42',
      'editorLineNumber.activeForeground': '#e2b878',
      'editorCursor.foreground': '#f0b36a',
      'editor.selectionBackground': '#6d4228aa',
      'editor.lineHighlightBackground': '#20130f',
      'editorGutter.background': '#130d0b'
    }
  });

  monacoInstance.editor.defineTheme('cafe-latte', {
    base: 'vs',
    inherit: true,
    rules: [
      { token: 'keyword', foreground: '8f4e19', fontStyle: 'bold' },
      { token: 'type', foreground: '7b4a2d' },
      { token: 'constant', foreground: '9d5b24' },
      { token: 'number', foreground: '7c4a1f' },
      { token: 'string', foreground: '6b4b2d' },
      { token: 'comment', foreground: '9a806a', fontStyle: 'italic' },
      { token: 'operator', foreground: 'a75f2a' }
    ],
    colors: {
      'editor.background': '#fff6e6',
      'editor.foreground': '#2f1d15',
      'editorLineNumber.foreground': '#ad8c67',
      'editorLineNumber.activeForeground': '#7b4a2d',
      'editorCursor.foreground': '#8f4e19',
      'editor.selectionBackground': '#d8b98a88',
      'editor.lineHighlightBackground': '#f7e8cf',
      'editorGutter.background': '#fff6e6'
    }
  });
}
