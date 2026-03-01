'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { puzzles } from '@/data/puzzles';
import { CellState, ClueEntry } from '@/types/crossword';
import {
  buildClueMap,
  buildInitialGrid,
  getCellsForWord,
  isPuzzleComplete,
  numberGrid,
} from '@/utils/crosswordUtils';

type Direction = 'across' | 'down';

function initPuzzle(index: number) {
  const puzzle = puzzles[index];
  const nums = numberGrid(puzzle.solution);
  const clues = buildClueMap(puzzle, nums);
  const grid = buildInitialGrid(puzzle.solution, nums, clues);
  return { puzzle, nums, clues, grid };
}

export function useCrossword() {
  const [activePuzzleIndex, setActivePuzzleIndex] = useState(0);

  const { puzzle, clues, grid: initialGrid } = useMemo(
    () => initPuzzle(activePuzzleIndex),
    [activePuzzleIndex]
  );

  const [grid, setGrid] = useState<CellState[][]>(initialGrid);
  const [selectedCell, setSelectedCell] = useState<[number, number] | null>(null);
  const [direction, setDirection] = useState<Direction>('across');
  const [selectedWord, setSelectedWord] = useState<number | null>(null);
  const [isComplete, setIsComplete] = useState(false);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [timerActive, setTimerActive] = useState(false);

  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Reset when puzzle changes
  useEffect(() => {
    const { grid: g } = initPuzzle(activePuzzleIndex);
    setGrid(g);
    setSelectedCell(null);
    setDirection('across');
    setSelectedWord(null);
    setIsComplete(false);
    setElapsedSeconds(0);
    setTimerActive(false);
  }, [activePuzzleIndex]);

  // Timer
  useEffect(() => {
    if (timerActive && !isComplete) {
      timerRef.current = setInterval(() => setElapsedSeconds(s => s + 1), 1000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [timerActive, isComplete]);

  /** Find which word (clue) covers a given cell in the current direction. */
  const findWord = useCallback(
    (r: number, c: number, dir: Direction): ClueEntry | undefined => {
      const cell = grid[r]?.[c];
      if (!cell || cell.isBlack) return undefined;
      const wordNum = dir === 'across' ? cell.acrossWord : cell.downWord;
      if (!wordNum) return undefined;
      return clues.find(cl => cl.number === wordNum && cl.direction === dir);
    },
    [grid, clues]
  );

  const selectCell = useCallback(
    (r: number, c: number) => {
      const cell = grid[r]?.[c];
      if (!cell || cell.isBlack) return;

      if (selectedCell && selectedCell[0] === r && selectedCell[1] === c) {
        // Toggle direction on same-cell click
        const newDir: Direction = direction === 'across' ? 'down' : 'across';
        setDirection(newDir);
        const w = findWord(r, c, newDir);
        setSelectedWord(w?.number ?? null);
      } else {
        setSelectedCell([r, c]);
        // Keep direction if possible, otherwise switch
        let dir = direction;
        let w = findWord(r, c, dir);
        if (!w) {
          dir = dir === 'across' ? 'down' : 'across';
          w = findWord(r, c, dir);
          setDirection(dir);
        }
        setSelectedWord(w?.number ?? null);
      }
    },
    [grid, selectedCell, direction, findWord]
  );

  const selectClue = useCallback(
    (number: number, dir: Direction) => {
      const entry = clues.find(cl => cl.number === number && cl.direction === dir);
      if (!entry) return;
      setSelectedCell([entry.row, entry.col]);
      setDirection(dir);
      setSelectedWord(number);
    },
    [clues]
  );

  /** Advance to next cell in current word, or move to next word. */
  const advanceCell = useCallback(
    (r: number, c: number, dir: Direction) => {
      const word = findWord(r, c, dir);
      if (!word) return;
      const cells = getCellsForWord(word);
      const idx = cells.findIndex(([cr, cc]) => cr === r && cc === c);
      if (idx < cells.length - 1) {
        const [nr, nc] = cells[idx + 1];
        setSelectedCell([nr, nc]);
      }
    },
    [findWord]
  );

  /** Move back to previous cell in current word. */
  const retreatCell = useCallback(
    (r: number, c: number, dir: Direction) => {
      const word = findWord(r, c, dir);
      if (!word) return;
      const cells = getCellsForWord(word);
      const idx = cells.findIndex(([cr, cc]) => cr === r && cc === c);
      if (idx > 0) {
        const [nr, nc] = cells[idx - 1];
        setSelectedCell([nr, nc]);
      }
    },
    [findWord]
  );

  const inputLetter = useCallback(
    (ch: string) => {
      if (!selectedCell) return;
      const [r, c] = selectedCell;
      if (!timerActive) setTimerActive(true);

      setGrid(prev => {
        const next = prev.map(row => row.map(cell => ({ ...cell })));
        next[r][c].userInput = ch.toUpperCase();
        next[r][c].isChecked = false;
        next[r][c].isCorrect = undefined;
        return next;
      });

      // After state update, check completion and advance
      setTimeout(() => {
        setGrid(g => {
          if (isPuzzleComplete(g)) setIsComplete(true);
          return g;
        });
        advanceCell(r, c, direction);
      }, 0);
    },
    [selectedCell, direction, timerActive, advanceCell]
  );

  const deleteLetter = useCallback(() => {
    if (!selectedCell) return;
    const [r, c] = selectedCell;
    const hasContent = grid[r][c].userInput !== '';

    setGrid(prev => {
      const next = prev.map(row => row.map(cell => ({ ...cell })));
      next[r][c].userInput = '';
      next[r][c].isChecked = false;
      next[r][c].isCorrect = undefined;
      return next;
    });

    if (!hasContent) {
      retreatCell(r, c, direction);
    }
  }, [selectedCell, grid, direction, retreatCell]);

  const moveArrow = useCallback(
    (arrowDir: 'ArrowUp' | 'ArrowDown' | 'ArrowLeft' | 'ArrowRight') => {
      if (!selectedCell) return;
      const [r, c] = selectedCell;
      const size = puzzle.size;

      const isHorizontal = arrowDir === 'ArrowLeft' || arrowDir === 'ArrowRight';
      const newDir: Direction = isHorizontal ? 'across' : 'down';

      // If direction changes, just change direction (stay on cell)
      if (newDir !== direction) {
        setDirection(newDir);
        const w = findWord(r, c, newDir);
        setSelectedWord(w?.number ?? null);
        return;
      }

      const dr = arrowDir === 'ArrowDown' ? 1 : arrowDir === 'ArrowUp' ? -1 : 0;
      const dc = arrowDir === 'ArrowRight' ? 1 : arrowDir === 'ArrowLeft' ? -1 : 0;
      let nr = r + dr;
      let nc = c + dc;

      // Skip black cells
      while (
        nr >= 0 && nr < size && nc >= 0 && nc < size &&
        grid[nr][nc].isBlack
      ) {
        nr += dr;
        nc += dc;
      }

      if (nr >= 0 && nr < size && nc >= 0 && nc < size && !grid[nr][nc].isBlack) {
        setSelectedCell([nr, nc]);
        const w = findWord(nr, nc, direction);
        setSelectedWord(w?.number ?? null);
      }
    },
    [selectedCell, direction, puzzle.size, grid, findWord]
  );

  const checkPuzzle = useCallback(() => {
    setGrid(prev =>
      prev.map(row =>
        row.map(cell => {
          if (cell.isBlack || cell.userInput === '') return cell;
          return {
            ...cell,
            isChecked: true,
            isCorrect: cell.userInput.toUpperCase() === cell.letter.toUpperCase(),
          };
        })
      )
    );
  }, []);

  const revealWord = useCallback(() => {
    if (!selectedCell) return;
    const [r, c] = selectedCell;
    const word = findWord(r, c, direction);
    if (!word) return;
    const cells = getCellsForWord(word);

    setGrid(prev => {
      const next = prev.map(row => row.map(cell => ({ ...cell })));
      for (const [wr, wc] of cells) {
        next[wr][wc].userInput = next[wr][wc].letter;
        next[wr][wc].isRevealed = true;
        next[wr][wc].isChecked = false;
        next[wr][wc].isCorrect = undefined;
      }
      return next;
    });

    setTimeout(() => {
      setGrid(g => {
        if (isPuzzleComplete(g)) setIsComplete(true);
        return g;
      });
    }, 0);
  }, [selectedCell, direction, findWord]);

  const resetPuzzle = useCallback(() => {
    setGrid(prev =>
      prev.map(row =>
        row.map(cell => ({
          ...cell,
          userInput: '',
          isRevealed: false,
          isChecked: false,
          isCorrect: undefined,
        }))
      )
    );
    setIsComplete(false);
    setElapsedSeconds(0);
    setTimerActive(false);
  }, []);

  const changePuzzle = useCallback((index: number) => {
    setActivePuzzleIndex(index);
  }, []);

  return {
    puzzle,
    grid,
    clues,
    selectedCell,
    direction,
    selectedWord,
    isComplete,
    elapsedSeconds,
    timerActive,
    activePuzzleIndex,
    selectCell,
    selectClue,
    inputLetter,
    deleteLetter,
    moveArrow,
    checkPuzzle,
    revealWord,
    resetPuzzle,
    changePuzzle,
  };
}
