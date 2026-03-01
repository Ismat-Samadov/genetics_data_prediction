'use client';

import { CellState } from '@/types/crossword';

interface Props {
  cell: CellState;
  isSelected: boolean;
  isInWord: boolean;
  onClick: () => void;
  cellSize: number;
}

export function CrosswordCell({ cell, isSelected, isInWord, onClick, cellSize }: Props) {
  if (cell.isBlack) {
    return (
      <div
        className="bg-neutral-900"
        style={{ width: cellSize, height: cellSize }}
      />
    );
  }

  let bg = 'bg-white';
  if (cell.isRevealed) bg = 'bg-violet-100';
  else if (cell.isChecked && cell.isCorrect === false) bg = 'bg-rose-100';
  else if (cell.isChecked && cell.isCorrect === true) bg = 'bg-emerald-100';
  else if (isSelected) bg = 'bg-amber-300';
  else if (isInWord) bg = 'bg-sky-100';

  return (
    <div
      className={`relative border border-neutral-300 cursor-pointer select-none flex items-center justify-center transition-colors duration-100 ${bg}`}
      style={{ width: cellSize, height: cellSize }}
      onClick={onClick}
    >
      {cell.number !== undefined && (
        <span
          className="absolute top-0 left-0 text-neutral-700 font-bold leading-none"
          style={{ fontSize: Math.max(7, cellSize * 0.28), padding: '1px 1px' }}
        >
          {cell.number}
        </span>
      )}
      <span
        className="font-bold text-neutral-900 uppercase"
        style={{ fontSize: Math.max(10, cellSize * 0.55) }}
      >
        {cell.userInput}
      </span>
    </div>
  );
}
