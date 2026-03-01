'use client';

import { useCrossword } from '@/hooks/useCrossword';
import { GameHeader } from './GameHeader';
import { CrosswordGrid } from './CrosswordGrid';
import { CluesPanel } from './CluesPanel';
import { WinModal } from './WinModal';

export function CrosswordGame() {
  const {
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
  } = useCrossword();

  return (
    <div className="min-h-screen bg-neutral-50 flex flex-col">
      <GameHeader
        title={puzzle.title}
        difficulty={puzzle.difficulty}
        elapsedSeconds={elapsedSeconds}
        timerActive={timerActive}
        activePuzzleIndex={activePuzzleIndex}
        onPuzzleChange={changePuzzle}
        onCheck={checkPuzzle}
        onReveal={revealWord}
        onReset={resetPuzzle}
      />

      <main className="flex-1 flex flex-col md:flex-row gap-4 p-4 max-w-5xl mx-auto w-full">
        {/* Grid */}
        <div className="flex justify-center md:justify-start items-start">
          <div className="overflow-x-auto">
            <CrosswordGrid
              grid={grid}
              size={puzzle.size}
              selectedCell={selectedCell}
              selectedWord={selectedWord}
              direction={direction}
              onCellClick={selectCell}
              onLetter={inputLetter}
              onDelete={deleteLetter}
              onArrow={moveArrow}
            />
          </div>
        </div>

        {/* Clues */}
        <div className="flex-1 bg-white rounded-xl border border-neutral-200 shadow-sm p-4 min-h-[200px] md:min-h-0 md:overflow-hidden md:flex md:flex-col">
          <CluesPanel
            clues={clues}
            selectedWord={selectedWord}
            direction={direction}
            onClueClick={selectClue}
          />
        </div>
      </main>

      {isComplete && (
        <WinModal
          elapsedSeconds={elapsedSeconds}
          activePuzzleIndex={activePuzzleIndex}
          onPlayAgain={resetPuzzle}
          onNextPuzzle={() => changePuzzle(activePuzzleIndex + 1)}
        />
      )}
    </div>
  );
}
