import { FileCode2, Folder, FolderPlus, Plus, RefreshCw } from 'lucide-react';
import type { FileEntry } from '../types';

interface ExplorerPanelProps {
  rootFolder: string | null;
  files: FileEntry[];
  onOpenFolder(): void;
  onOpenFile(file: FileEntry): void;
  onRefresh(): void;
  onCreateFile(): void;
  onCreateFolder(): void;
}

export function ExplorerPanel({ rootFolder, files, onOpenFolder, onOpenFile, onRefresh, onCreateFile, onCreateFolder }: ExplorerPanelProps) {
  return (
    <aside className="flex h-full w-72 flex-col border-r border-latte/10 bg-espresso/95 text-crema">
      <div className="flex h-10 items-center justify-between border-b border-latte/10 px-3 text-xs font-semibold uppercase tracking-wider text-latte">
        Explorer
        <div className="flex items-center gap-1">
          <button className="icon-button compact" onClick={onCreateFile} title="New file">
            <Plus size={14} />
          </button>
          <button className="icon-button compact" onClick={onCreateFolder} title="New folder">
            <FolderPlus size={14} />
          </button>
          <button className="icon-button compact" onClick={onRefresh} title="Refresh">
            <RefreshCw size={14} />
          </button>
        </div>
      </div>

      <button className="m-3 rounded-md border border-latte/20 bg-mocha/50 px-3 py-2 text-left text-sm text-foam transition hover:bg-mocha" onClick={onOpenFolder}>
        {rootFolder ? 'Switch Folder' : 'Open Folder'}
      </button>

      <div className="px-3 pb-2 text-xs text-latte/80">
        {rootFolder ? rootFolder : 'No folder opened'}
      </div>

      <div className="flex-1 overflow-auto px-2 pb-4">
        {files.map((file) => (
          <button
            key={file.path}
            className="flex w-full items-center gap-2 rounded px-2 py-1.5 text-left text-sm text-crema transition hover:bg-latte/10"
            onClick={() => onOpenFile(file)}
          >
            {file.type === 'folder' ? <Folder size={15} className="text-caramel" /> : <FileCode2 size={15} className="text-latte" />}
            <span className="truncate">{file.name}</span>
          </button>
        ))}
      </div>
    </aside>
  );
}
