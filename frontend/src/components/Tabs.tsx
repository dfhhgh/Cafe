import { X } from 'lucide-react';
import type { EditorTab } from '../types';

interface TabsProps {
  tabs: EditorTab[];
  activeTabId: string;
  onSelect(tabId: string): void;
  onClose(tabId: string): void;
}

export function Tabs({ tabs, activeTabId, onSelect, onClose }: TabsProps) {
  return (
    <div className="flex h-10 items-end overflow-x-auto border-b border-latte/10 bg-espresso">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          className={`group flex h-10 min-w-40 items-center justify-between gap-3 border-r border-latte/10 px-3 text-sm transition ${
            tab.id === activeTabId ? 'bg-roast text-foam' : 'bg-espresso/80 text-latte hover:bg-mocha/40'
          }`}
          onClick={() => onSelect(tab.id)}
        >
          <span className="truncate">
            {tab.name}
            {tab.dirty ? <span className="ml-1 text-caramel">●</span> : null}
          </span>
          <span
            role="button"
            tabIndex={0}
            className="rounded p-0.5 opacity-0 transition hover:bg-latte/10 group-hover:opacity-100"
            onClick={(event) => {
              event.stopPropagation();
              onClose(tab.id);
            }}
          >
            <X size={14} />
          </span>
        </button>
      ))}
    </div>
  );
}
