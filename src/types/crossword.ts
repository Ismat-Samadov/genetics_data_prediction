export interface CellState {
  letter: string;        // correct answer letter
  isBlack: boolean;
  number?: number;       // clue number shown in top-left
  userInput: string;     // what the user typed
  acrossWord?: number;   // clue number of the across word this belongs to
  downWord?: number;     // clue number of the down word this belongs to
  isRevealed: boolean;
  isChecked: boolean;    // has been manually checked
  isCorrect?: boolean;   // set after check
}

export interface ClueEntry {
  number: number;
  direction: 'across' | 'down';
  clue: string;
  answer: string;
  row: number;
  col: number;
  length: number;
}

export interface PuzzleDefinition {
  id: string;
  title: string;
  difficulty: 'easy' | 'medium' | 'hard';
  size: number;
  solution: string[][];  // '#' = black cell, else answer letter
  clues: {
    across: { number: number; clue: string }[];
    down: { number: number; clue: string }[];
  };
}
