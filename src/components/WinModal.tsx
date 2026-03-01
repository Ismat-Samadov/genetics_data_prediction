'use client';

import { formatTime } from '@/utils/crosswordUtils';
import { puzzles } from '@/data/puzzles';

interface Props {
  elapsedSeconds: number;
  activePuzzleIndex: number;
  onPlayAgain: () => void;
  onNextPuzzle: () => void;
}

export function WinModal({ elapsedSeconds, activePuzzleIndex, onPlayAgain, onNextPuzzle }: Props) {
  const hasNext = activePuzzleIndex < puzzles.length - 1;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

      {/* Confetti layer */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none" aria-hidden>
        {Array.from({ length: 40 }).map((_, i) => (
          <div
            key={i}
            className="confetti-piece"
            style={{
              left: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 3}s`,
              animationDuration: `${2 + Math.random() * 3}s`,
              backgroundColor: ['#fbbf24','#34d399','#60a5fa','#f472b6','#a78bfa','#fb923c'][i % 6],
              width: `${6 + Math.random() * 8}px`,
              height: `${6 + Math.random() * 8}px`,
              borderRadius: Math.random() > 0.5 ? '50%' : '2px',
            }}
          />
        ))}
      </div>

      {/* Modal card */}
      <div className="relative z-10 bg-white rounded-3xl shadow-2xl p-10 flex flex-col items-center gap-6 max-w-sm w-full text-center animate-win-pop">
        <div className="text-6xl animate-bounce">🎉</div>

        <div>
          <h2 className="text-3xl font-black text-neutral-900 mb-1">Puzzle Solved!</h2>
          <p className="text-neutral-500 text-sm">
            You completed <span className="font-semibold text-neutral-700">{puzzles[activePuzzleIndex].title}</span>
          </p>
        </div>

        <div className="bg-gradient-to-br from-amber-50 to-amber-100 rounded-2xl px-8 py-4 border border-amber-200">
          <p className="text-xs font-semibold text-amber-600 uppercase tracking-widest mb-1">
            Your Time
          </p>
          <p className="text-4xl font-black text-amber-700 font-mono">
            {formatTime(elapsedSeconds)}
          </p>
        </div>

        <div className="flex flex-col gap-3 w-full">
          <button
            onClick={onPlayAgain}
            className="w-full py-3 rounded-xl bg-neutral-900 text-white font-bold text-base hover:bg-neutral-700 transition-colors"
          >
            Play Again
          </button>
          {hasNext && (
            <button
              onClick={onNextPuzzle}
              className="w-full py-3 rounded-xl bg-amber-400 text-neutral-900 font-bold text-base hover:bg-amber-300 transition-colors"
            >
              Next Puzzle →
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
