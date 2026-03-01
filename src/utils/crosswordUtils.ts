import { CellState, ClueEntry, PuzzleDefinition } from '@/types/crossword';

/**
 * Assigns clue numbers to cells following standard crossword rules:
 * A cell gets a number if it starts an across word (leftmost of 2+ white cells in a row)
 * or a down word (topmost of 2+ white cells in a column).
 */
export function numberGrid(solution: string[][]): (number | undefined)[][] {
  const size = solution.length;
  const numbers: (number | undefined)[][] = Array.from({ length: size }, () =>
    Array(size).fill(undefined)
  );
  let counter = 1;

  for (let r = 0; r < size; r++) {
    for (let c = 0; c < size; c++) {
      if (solution[r][c] === '#') continue;

      const startsAcross =
        (c === 0 || solution[r][c - 1] === '#') &&
        c + 1 < size && solution[r][c + 1] !== '#';

      const startsDown =
        (r === 0 || solution[r - 1][c] === '#') &&
        r + 1 < size && solution[r + 1][c] !== '#';

      if (startsAcross || startsDown) {
        numbers[r][c] = counter++;
      }
    }
  }

  return numbers;
}

/**
 * Builds a flat list of ClueEntry objects with position and length filled in.
 */
export function buildClueMap(
  puzzle: PuzzleDefinition,
  numbers: (number | undefined)[][]
): ClueEntry[] {
  const { solution, clues, size } = puzzle;
  const entries: ClueEntry[] = [];

  for (const ac of clues.across) {
    // Find the cell that holds this number
    let found = false;
    for (let r = 0; r < size && !found; r++) {
      for (let c = 0; c < size && !found; c++) {
        if (numbers[r][c] === ac.number) {
          // Measure length
          let len = 0;
          while (c + len < size && solution[r][c + len] !== '#') len++;
          if (len >= 2) {
            const answer = Array.from({ length: len }, (_, i) => solution[r][c + i]).join('');
            entries.push({
              number: ac.number,
              direction: 'across',
              clue: ac.clue,
              answer,
              row: r,
              col: c,
              length: len,
            });
            found = true;
          }
        }
      }
    }
  }

  for (const dn of clues.down) {
    let found = false;
    for (let r = 0; r < size && !found; r++) {
      for (let c = 0; c < size && !found; c++) {
        if (numbers[r][c] === dn.number) {
          let len = 0;
          while (r + len < size && solution[r + len][c] !== '#') len++;
          if (len >= 2) {
            const answer = Array.from({ length: len }, (_, i) => solution[r + i][c]).join('');
            entries.push({
              number: dn.number,
              direction: 'down',
              clue: dn.clue,
              answer,
              row: r,
              col: c,
              length: len,
            });
            found = true;
          }
        }
      }
    }
  }

  return entries;
}

/** Returns [row, col] pairs for every cell in a given word. */
export function getCellsForWord(clue: ClueEntry): [number, number][] {
  return Array.from({ length: clue.length }, (_, i) =>
    clue.direction === 'across'
      ? ([clue.row, clue.col + i] as [number, number])
      : ([clue.row + i, clue.col] as [number, number])
  );
}

/** Creates the initial CellState grid from a solution. */
export function buildInitialGrid(
  solution: string[][],
  numbers: (number | undefined)[][],
  clueEntries: ClueEntry[]
): CellState[][] {
  const size = solution.length;

  // Build lookup maps: which across/down word each cell belongs to
  const acrossMap: Record<string, number> = {};
  const downMap: Record<string, number> = {};

  for (const entry of clueEntries) {
    const cells = getCellsForWord(entry);
    for (const [r, c] of cells) {
      const key = `${r},${c}`;
      if (entry.direction === 'across') acrossMap[key] = entry.number;
      else downMap[key] = entry.number;
    }
  }

  return Array.from({ length: size }, (_, r) =>
    Array.from({ length: size }, (_, c) => {
      const isBlack = solution[r][c] === '#';
      const key = `${r},${c}`;
      return {
        letter: isBlack ? '' : solution[r][c],
        isBlack,
        number: numbers[r][c],
        userInput: '',
        acrossWord: isBlack ? undefined : acrossMap[key],
        downWord: isBlack ? undefined : downMap[key],
        isRevealed: false,
        isChecked: false,
        isCorrect: undefined,
      } as CellState;
    })
  );
}

/** Returns true when every white cell has the correct letter entered. */
export function isPuzzleComplete(grid: CellState[][]): boolean {
  for (const row of grid) {
    for (const cell of row) {
      if (!cell.isBlack && cell.userInput.toUpperCase() !== cell.letter.toUpperCase()) {
        return false;
      }
    }
  }
  return true;
}

/** Format seconds as MM:SS */
export function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60).toString().padStart(2, '0');
  const s = (seconds % 60).toString().padStart(2, '0');
  return `${m}:${s}`;
}
