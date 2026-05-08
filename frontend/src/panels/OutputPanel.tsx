import { AlertCircle, CheckCircle2, Info } from 'lucide-react';
import type { Diagnostic, PanelTab } from '../types';

interface OutputPanelProps {
  activeTab: PanelTab;
  consoleLines: string[];
  diagnostics: Diagnostic[];
  onTabChange(tab: PanelTab): void;
}

export function OutputPanel({ activeTab, consoleLines, diagnostics, onTabChange }: OutputPanelProps) {
  return (
    <section className="flex h-64 flex-col border-t border-latte/10 bg-roast text-sm text-crema">
      <div className="flex h-9 items-center border-b border-latte/10">
        {(['console', 'diagnostics'] as PanelTab[]).map((tab) => (
          <button
            key={tab}
            className={`h-full px-4 text-xs uppercase tracking-wider transition ${
              activeTab === tab ? 'bg-mocha text-foam' : 'text-latte hover:bg-latte/10'
            }`}
            onClick={() => onTabChange(tab)}
          >
            {tab}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-auto p-3 font-mono text-xs leading-6">
        {activeTab === 'diagnostics' ? (
          diagnostics.length ? diagnostics.map((diagnostic, index) => (
            <div key={`${diagnostic.message}-${index}`} className="mb-2 flex gap-2 rounded border border-red-400/20 bg-red-950/20 p-2 text-red-100">
              <AlertCircle size={15} className="mt-0.5 text-red-300" />
              <div>
                <div className="font-semibold">{diagnostic.stage} {diagnostic.line ? `at ${diagnostic.line}:${diagnostic.column ?? 1}` : ''}</div>
                <div>{diagnostic.message}</div>
              </div>
            </div>
          )) : (
            <div className="flex items-center gap-2 text-latte">
              <CheckCircle2 size={15} />
              No diagnostics. The brew is smooth.
            </div>
          )
        ) : (
          consoleLines.map((line, index) => (
            <div key={`${line}-${index}`} className={line.includes('Error') || line.includes('FAILED') ? 'text-red-200' : line.includes('SUCCESS') ? 'text-green-200' : 'text-crema'}>
              <Info size={12} className="mr-2 inline text-caramel" />
              {line}
            </div>
          ))
        )}
      </div>
    </section>
  );
}
