# Crossword Puzzle

A visually polished, fully interactive crossword puzzle game built with **Next.js 16**, **TypeScript**, and **Tailwind CSS**.

![Next.js](https://img.shields.io/badge/Next.js-16-black?logo=next.js)
![TypeScript](https://img.shields.io/badge/TypeScript-5-blue?logo=typescript)
![Tailwind CSS](https://img.shields.io/badge/Tailwind-3-06B6D4?logo=tailwindcss)

---

## Features

- **Two built-in puzzles** — "Tech World" (medium) and "Wild Kingdom" (easy), both 13×13
- **Full keyboard support** — type letters, backspace, arrow keys, automatic word advance
- **Mouse/click navigation** — click any cell or clue to jump to it; click same cell to toggle direction
- **Live timer** — starts on first keypress, stops when the puzzle is solved
- **Check** — marks incorrect cells red, correct cells green
- **Reveal Word** — fills in the current word (highlighted in purple)
- **Reset** — clears all input and restarts the timer
- **Win modal** — CSS confetti animation + completion time display
- **Responsive layout** — two-column grid + clues on desktop; stacked with tabbed clues on mobile

---

## Getting Started

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## Project Structure

```
src/
├── app/
│   ├── page.tsx          # Root page
│   ├── layout.tsx        # HTML shell + metadata
│   └── globals.css       # Tailwind + custom animations
├── types/
│   └── crossword.ts      # CellState, ClueEntry, PuzzleDefinition
├── data/
│   └── puzzles.ts        # Puzzle definitions (solution grids + clues)
├── hooks/
│   └── useCrossword.ts   # All game logic and state
├── utils/
│   └── crosswordUtils.ts # Grid numbering, clue mapping, helpers
└── components/
    ├── CrosswordGame.tsx  # Top-level shell
    ├── GameHeader.tsx     # Title, timer, controls
    ├── CrosswordGrid.tsx  # Interactive grid with keyboard capture
    ├── CrosswordCell.tsx  # Single cell (7 visual states)
    ├── CluesPanel.tsx     # Across / Down clue lists
    └── WinModal.tsx       # Completion overlay
public/
└── favicon.svg           # Custom SVG favicon
```

---

## How to Play

| Action | How |
|--------|-----|
| Select a cell | Click it |
| Toggle direction | Click the same cell again |
| Type a letter | Keyboard — advances automatically |
| Delete a letter | `Backspace` |
| Navigate | Arrow keys |
| Jump to a clue | Click it in the clues panel |
| Check answers | "Check" button |
| Reveal current word | "Reveal Word" button |
| Reset | "Reset" button |
| Switch puzzle | Dropdown in the header |

---

## Cell Colour Key

| Colour | Meaning |
|--------|---------|
| White | Default |
| Sky blue | In the currently selected word |
| Amber | Currently selected cell |
| Emerald | Checked — correct |
| Rose | Checked — incorrect |
| Violet | Revealed by "Reveal Word" |
| Dark | Black / blocked cell |

---

## Adding a New Puzzle

1. Open `src/data/puzzles.ts`
2. Add a new `PuzzleDefinition` object to the `puzzles` array:
   - `solution` — 2D string array (`'#'` for black cells, uppercase letters elsewhere)
   - `clues.across` / `clues.down` — arrays of `{ number, clue }` where `number` matches the auto-generated grid numbering

Cell numbers are assigned automatically by `numberGrid()` following standard crossword rules (a cell is numbered if it starts an across or down word of length ≥ 2).

---

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Production build |
| `npm start` | Start production server |
| `npm run lint` | Run ESLint |
