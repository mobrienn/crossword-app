''' ======================================
crossword_generator.py
Generates 5x5 crossword puzzles using 5-letter words.
=========================================='''
from dataclasses import dataclass
from collections import defaultdict
import random

# ----------------------------------------
# CONSTANTS
# ----------------------------------------
GRID_SIZE = 5

# ----------------------------------------
# DATA CLASSES
# ----------------------------------------
@dataclass
class WordEntry:
    word: str
    clue:str

@dataclass
class Slot:
    # constructor - runs when new slot is created
    def __init__(self, row, col, is_row, length=GRID_SIZE, label=None):
        self.row = row
        self.col = col
        self.is_row = is_row
        self.length = length
        self.label = label

    # printing/debugging
    def __repr__(self):
        direction = "Across" if self.is_row else "Down"
        return f"Slot({self.row},{self.col},{direction},len={self.length},label={self.label})"

    # comparing instances
    def __eq__(self, other):
        return (
            isinstance(other, Slot) and
            self.row == other.row and
            self.col == other.col and
            self.is_row == other.is_row and
            self.length == other.length
        )

    # if needed
    def __hash__(self):
        return hash((self.row, self.col, self.is_row, self.length))

    # tells generator which cells a word would occupy
    def positions(self):
        """Return list of (r, c) positions this slot covers"""
        return [
            (
                self.row + (i if not self.is_row else 0),
                self.col + (i if self.is_row else 0)
            )
            for i in range(self.length)
        ]
    
    # tells generator if all slots are filled
    def is_filled(self, grid):
        """Check if all cells in this slot are filled in the grid"""
        return all(grid[r][c] != '' for r, c in self.positions())

# ----------------------------------------
# DATA IMPORT
# ----------------------------------------   
def import_words(wordlist_file):
    words_clues = []
    with open(wordlist_file, "r") as f:
        for line in f:
            if ':' not in line:
                continue
            word, clue = line.strip().split(":")
            word = word.upper()
            if len(word) == GRID_SIZE:
                words_clues.append(WordEntry(word, clue))
    return words_clues

# ----------------------------------------
# CROSSWORD GENERATOR CLASS
# ----------------------------------------
class CrosswordGenerator:
    def __init__(self,words):
        self.words = words
        self.grid = [[''] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.slots = self.create_slots()
        self.prefix_dict = self.build_prefix_dict()
        self.pattern_dict = self.build_pattern_dict()


    def create_slots(self):
        slots = []

        # Across slots (row fixed, col starts at 0)
        for r in range(GRID_SIZE):
            slots.append(Slot(r, 0, True, GRID_SIZE, f"{r+1}-Across"))

        # Down slots (col fixed, row starts at 0)
        for c in range(GRID_SIZE):
            slots.append(Slot(0, c, False, GRID_SIZE, f"{c+1}-Down"))

        return slots


    def build_prefix_dict(self):
        d = {}
        for w in self.words:
            for i in range (1, len(w.word) + 1):
                prefix = w.word[:i]
                d.setdefault(prefix, []).append(w.word)
        return d

    def build_pattern_dict(self):
        pattern_dict = defaultdict(list)
        for entry in self.words:
            word = entry.word
            for i in range(1, 2 ** GRID_SIZE):
                pattern = tuple(
                    word[j] if (i>>j) & 1 else '_'
                    for j in range(GRID_SIZE)
                )
                pattern_dict[pattern].append(entry)
        return pattern_dict



    
###########################################
###########################################
###########################################

if __name__ == "__main__":
    words_clues = import_words("test.txt")
    generator = CrosswordGenerator(words_clues)

