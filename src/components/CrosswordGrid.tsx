'use client';

import { useCallback, useEffect, useRef } from 'react';
import { CellState } from '@/types/crossword';
import { CrosswordCell } from './CrosswordCell';

interface Props {
  grid: CellState[][];
  size: number;
  selectedCell: [number, number] | null;
  selectedWord: number | null;
  direction: 'across' | 'down';
  onCellClick: (r: number, c: number) => void;
  onLetter: (ch: string) => void;
  onDelete: () => void;
  onArrow: (dir: 'ArrowUp' | 'ArrowDown' | 'ArrowLeft' | 'ArrowRight') => void;
}

const CELL_SIZE = 44;

export function CrosswordGrid({
  grid,
  size,
  selectedCell,
  selectedWord,
  direction,
  onCellClick,
  onLetter,
  onDelete,
  onArrow,
}: Props) {
  const wrapperRef = useRef<HTMLDivElement>(null);

  // Focus wrapper so keyboard events are captured
  useEffect(() => {
    if (selectedCell && wrapperRef.current) {
      wrapperRef.current.focus({ preventScroll: true });
    }
  }, [selectedCell]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Backspace' || e.key === 'Delete') {
        e.preventDefault();
        onDelete();
      } else if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
        e.preventDefault();
        onArrow(e.key as 'ArrowUp' | 'ArrowDown' | 'ArrowLeft' | 'ArrowRight');
      } else if (/^[a-zA-Z]$/.test(e.key)) {
        e.preventDefault();
        onLetter(e.key.toUpperCase());
      }
    },
    [onDelete, onArrow, onLetter]
  );

  const isInWord = useCallback(
    (r: number, c: number) => {
      if (!selectedWord || !grid[r] || !grid[r][c]) return false;
      const cell = grid[r][c];
      if (direction === 'across') return cell.acrossWord === selectedWord;
      return cell.downWord === selectedWord;
    },
    [grid, selectedWord, direction]
  );

  const gridPixels = size * CELL_SIZE;

  return (
    <div
      ref={wrapperRef}
      tabIndex={0}
      onKeyDown={handleKeyDown}
      className="outline-none focus:ring-2 focus:ring-amber-400 focus:ring-offset-2 rounded"
      style={{ width: gridPixels, height: gridPixels }}
    >
      <div
        className="grid border-2 border-neutral-800"
        style={{
          display: 'grid',
          gridTemplateColumns: `repeat(${size}, ${CELL_SIZE}px)`,
          gridTemplateRows: `repeat(${size}, ${CELL_SIZE}px)`,
          width: gridPixels,
          height: gridPixels,
        }}
      >
        {grid.map((row, r) =>
          row.map((cell, c) => (
            <CrosswordCell
              key={`${r}-${c}`}
              cell={cell}
              isSelected={
                selectedCell !== null &&
                selectedCell[0] === r &&
                selectedCell[1] === c
              }
              isInWord={isInWord(r, c)}
              onClick={() => onCellClick(r, c)}
              cellSize={CELL_SIZE}
            />
          ))
        )}
      </div>
    </div>
  );
}
