'use client';

import { useEffect, useRef, useState } from 'react';
import { ClueEntry } from '@/types/crossword';

interface Props {
  clues: ClueEntry[];
  selectedWord: number | null;
  direction: 'across' | 'down';
  onClueClick: (number: number, dir: 'across' | 'down') => void;
}

export function CluesPanel({ clues, selectedWord, direction, onClueClick }: Props) {
  const [activeTab, setActiveTab] = useState<'across' | 'down'>('across');
  const activeClueRef = useRef<HTMLButtonElement | null>(null);

  const acrossClues = clues.filter(c => c.direction === 'across').sort((a, b) => a.number - b.number);
  const downClues = clues.filter(c => c.direction === 'down').sort((a, b) => a.number - b.number);

  // Sync mobile tab with selected direction
  useEffect(() => {
    if (selectedWord) setActiveTab(direction);
  }, [selectedWord, direction]);

  // Auto-scroll active clue into view
  useEffect(() => {
    activeClueRef.current?.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  }, [selectedWord, direction]);

  const ClueList = ({
    entries,
    dir,
  }: {
    entries: ClueEntry[];
    dir: 'across' | 'down';
  }) => (
    <ul className="space-y-0.5">
      {entries.map(entry => {
        const isActive = selectedWord === entry.number && direction === dir;
        return (
          <li key={`${dir}-${entry.number}`}>
            <button
              ref={isActive ? activeClueRef : null}
              onClick={() => onClueClick(entry.number, dir)}
              className={`w-full text-left px-3 py-1.5 rounded text-sm transition-colors duration-100 ${
                isActive
                  ? 'bg-amber-300 text-neutral-900 font-semibold'
                  : 'hover:bg-sky-50 text-neutral-700'
              }`}
            >
              <span className="font-bold mr-1.5 text-neutral-500 text-xs">
                {entry.number}.
              </span>
              {entry.clue}
            </button>
          </li>
        );
      })}
    </ul>
  );

  return (
    <div className="flex flex-col h-full">
      {/* Mobile tabs */}
      <div className="flex md:hidden border-b border-neutral-200 mb-2">
        {(['across', 'down'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`flex-1 py-2 text-sm font-semibold capitalize transition-colors ${
              activeTab === tab
                ? 'border-b-2 border-amber-400 text-amber-600'
                : 'text-neutral-500 hover:text-neutral-700'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Mobile: single list */}
      <div className="md:hidden overflow-y-auto flex-1 pr-1">
        <ClueList entries={activeTab === 'across' ? acrossClues : downClues} dir={activeTab} />
      </div>

      {/* Desktop: two columns */}
      <div className="hidden md:flex gap-4 h-full overflow-hidden">
        <div className="flex-1 overflow-y-auto">
          <h3 className="text-xs font-bold uppercase tracking-widest text-neutral-400 mb-2 px-3">
            Across
          </h3>
          <ClueList entries={acrossClues} dir="across" />
        </div>
        <div className="w-px bg-neutral-200 flex-shrink-0" />
        <div className="flex-1 overflow-y-auto">
          <h3 className="text-xs font-bold uppercase tracking-widest text-neutral-400 mb-2 px-3">
            Down
          </h3>
          <ClueList entries={downClues} dir="down" />
        </div>
      </div>
    </div>
  );
}
