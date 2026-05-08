# Cafe IDE

Coffee-themed desktop IDE for the Cafe programming language.

## Stack

- Electron for the desktop shell
- React + TypeScript for the renderer
- TailwindCSS for styling
- Monaco Editor for Cafe source editing
- Python compiler bridge using the existing Cafe compiler modules

## Project Layout

```text
frontend/
  electron/          Electron main/preload process
  src/
    components/      Toolbar, tabs, status bar
    panels/          Explorer, output, generated C++ viewer
    editor/          Monaco Cafe language and themes
    compiler/        Reserved for renderer compiler utilities
    hooks/           IDE state orchestration
    themes/          Reserved for theme expansion
    utils/           Sample source and helpers
```

## Commands

```bash
npm install
npm run dev
npm run build
```

The renderer calls `Cafe/ide_bridge.py`, which runs the existing scanner, parser,
semantic checks, and C++ generator without changing compiler architecture.

