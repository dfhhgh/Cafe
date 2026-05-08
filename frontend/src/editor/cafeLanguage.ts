import type * as monaco from 'monaco-editor';

export const cafeKeywords = [
  'serve',
  'recipe',
  'refill',
  'stir',
  'check',
  'another_check',
  'instead',
  'bill',
  'menu',
  'item',
  'any_drink',
  'done',
  'package',
  'hot',
  'cold',
  'safe_order',
  'spilled'
];

export const cafeTypes = ['count', 'measure', 'note', 'coin', 'emo'];

export function registerCafeLanguage(monacoInstance: typeof monaco) {
  const languages = monacoInstance.languages.getLanguages();
  if (!languages.some((language) => language.id === 'cafe')) {
    monacoInstance.languages.register({ id: 'cafe', extensions: ['.cafe'], aliases: ['Cafe'] });
  }

  monacoInstance.languages.setMonarchTokensProvider('cafe', {
    defaultToken: '',
    tokenPostfix: '.cafe',
    keywords: cafeKeywords,
    typeKeywords: cafeTypes,
    booleans: ['hot', 'cold'],
    operators: ['=', '>', '<', '!', '~', '?', ':', '==', '<=', '>=', '!=', '+', '-', '*', '/', '<<'],
    symbols: /[=><!~?:&|+\-*\\/^%]+/,
    tokenizer: {
      root: [
        [/[a-zA-Z_]\w*/, { cases: { '@typeKeywords': 'type', '@booleans': 'constant', '@keywords': 'keyword', '@default': 'identifier' } }],
        [/\d+(\.\d+)?/, 'number'],
        [/"([^"\\]|\\.)*$/, 'string.invalid'],
        [/"/, { token: 'string.quote', bracket: '@open', next: '@string' }],
        [/'([^'\\]|\\.)'/, 'string.char'],
        [/\/\/.*$/, 'comment'],
        [/\/\*/, 'comment', '@comment'],
        [/[{}()[\]]/, '@brackets'],
        [/@symbols/, { cases: { '@operators': 'operator', '@default': '' } }],
        [/[;,.]/, 'delimiter']
      ],
      comment: [
        [/[^/*]+/, 'comment'],
        [/\*\//, 'comment', '@pop'],
        [/[/*]/, 'comment']
      ],
      string: [
        [/[^\\"]+/, 'string'],
        [/\\./, 'string.escape'],
        [/"/, { token: 'string.quote', bracket: '@close', next: '@pop' }]
      ]
    }
  });

  monacoInstance.languages.setLanguageConfiguration('cafe', {
    comments: { lineComment: '//', blockComment: ['/*', '*/'] },
    brackets: [['{', '}'], ['[', ']'], ['(', ')']],
    autoClosingPairs: [
      { open: '{', close: '}' },
      { open: '[', close: ']' },
      { open: '(', close: ')' },
      { open: '"', close: '"' },
      { open: "'", close: "'" }
    ],
    surroundingPairs: [
      { open: '{', close: '}' },
      { open: '[', close: ']' },
      { open: '(', close: ')' },
      { open: '"', close: '"' },
      { open: "'", close: "'" }
    ]
  });
}
