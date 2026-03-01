'use client';

import { puzzles } from '@/data/puzzles';
import { formatTime } from '@/utils/crosswordUtils';

interface Props {
  title: string;
  difficulty: string;
  elapsedSeconds: number;
  timerActive: boolean;
  activePuzzleIndex: number;
  onPuzzleChange: (index: number) => void;
  onCheck: () => void;
  onReveal: () => void;
  onReset: () => void;
}

const difficultyColors: Record<string, string> = {
  easy: 'bg-emerald-100 text-emerald-700',
  medium: 'bg-amber-100 text-amber-700',
  hard: 'bg-rose-100 text-rose-700',
};

export function GameHeader({
  title,
  difficulty,
  elapsedSeconds,
  timerActive,
  activePuzzleIndex,
  onPuzzleChange,
  onCheck,
  onReveal,
  onReset,
}: Props) {
  return (
    <header className="bg-white border-b border-neutral-200 shadow-sm px-4 py-3">
      <div className="max-w-5xl mx-auto flex flex-wrap items-center gap-3">
        {/* Title area */}
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <div className="text-2xl">⬛</div>
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-xl font-black text-neutral-900 tracking-tight leading-none">
                {title}
              </h1>
              <span
                className={`text-xs font-semibold px-2 py-0.5 rounded-full capitalize ${
                  difficultyColors[difficulty] ?? 'bg-neutral-100 text-neutral-600'
                }`}
              >
                {difficulty}
              </span>
            </div>
            <p className="text-xs text-neutral-400 mt-0.5 font-medium tracking-wide">
              CROSSWORD
            </p>
          </div>
        </div>

        {/* Timer */}
        <div className="flex items-center gap-1.5 bg-neutral-50 border border-neutral-200 rounded-lg px-3 py-1.5">
          <span className="text-neutral-400 text-sm">⏱</span>
          <span className={`font-mono font-bold text-lg leading-none ${timerActive ? 'text-neutral-800' : 'text-neutral-400'}`}>
            {formatTime(elapsedSeconds)}
          </span>
        </div>

        {/* Puzzle selector */}
        <select
          value={activePuzzleIndex}
          onChange={e => onPuzzleChange(Number(e.target.value))}
          className="text-sm border border-neutral-300 rounded-lg px-2 py-1.5 bg-white text-neutral-700 focus:outline-none focus:ring-2 focus:ring-amber-400 cursor-pointer"
        >
          {puzzles.map((p, i) => (
            <option key={p.id} value={i}>
              {p.title}
            </option>
          ))}
        </select>

        {/* Action buttons */}
        <div className="flex gap-2">
          <button
            onClick={onCheck}
            className="text-sm font-semibold px-3 py-1.5 rounded-lg border border-neutral-300 text-neutral-700 hover:bg-neutral-50 transition-colors"
          >
            Check
          </button>
          <button
            onClick={onReveal}
            className="text-sm font-semibold px-3 py-1.5 rounded-lg border border-neutral-300 text-neutral-700 hover:bg-neutral-50 transition-colors"
          >
            Reveal Word
          </button>
          <button
            onClick={onReset}
            className="text-sm font-semibold px-3 py-1.5 rounded-lg bg-neutral-900 text-white hover:bg-neutral-700 transition-colors"
          >
            Reset
          </button>
        </div>
      </div>
    </header>
  );
}
