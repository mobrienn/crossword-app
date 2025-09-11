''' ======================================
crossword_generator.py
Generates 5x5 crossword puzzles using 5-letter words.
=========================================='''
from dataclasses import dataclass
from collections import defaultdict, Counter 
from types import MappingProxyType
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
    def __init__(self, start, direction, length=GRID_SIZE, label=None):
        self.start = start
        self.direction = direction
        self.length = length 
        self.label = label

    def __repr__(self):
        direction = "Across" if self.direction else "Down"
        return f"Slot({self.start},{direction},len={self.length},label={self.label})"

    def __eq__(self, other):
        return (isinstance(other, Slot) and
            self.start == other.start and  
            self.length == other.length and
            self.direction == other.direction and
            self.label == other.label)

    def __hash__(self):
        return hash((self.start, self.direction, self.length, self.label))

    def positions(self):
        """Return list of (r, c) positions this slot covers"""
        r, c = self.start
        if self.direction == "across":
            return [(r,c+i) for i in range(self.length)]
        else:
            return [(r+i,c) for i in range(self.length)]
    
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
    def __init__(self,word_entries):
        self.wordlist = tuple(entry.word for entry in word_entries)
        self.word_to_clue = MappingProxyType({entry.word: entry.clue for entry in word_entries})
        self.grid = [[''] * GRID_SIZE for _ in range(GRID_SIZE)] # live 5x5 grid
        self.slots = self.create_slots() # defines row/col slots
        self.prefix_dict = self.build_prefix_dict(self.wordlist) # maps prefixes to possible words
        self.column_freq = self.compute_column_frequencies()
        self.slot_to_word = {}
        self.cell_to_slots = defaultdict(set)
# ----------------------------------------
#       slot set up
# ----------------------------------------
    def create_slots(self):
        slots = []
        for r in range(GRID_SIZE):
            slot = Slot(r, 0, True, GRID_SIZE, f"{r+1}-Across")
            slots.append(slot)
        for c in range(GRID_SIZE):
            slot = Slot(0, c, False, GRID_SIZE, f"{c+1}-Down")
            slots.append(slot)
        return slots
# ----------------------------------------
#       dictionary set uo
# ----------------------------------------
    def build_prefix_dict(self, wordlist):
        prefix_dict = set()
        for word in wordlist:
            for i in range (1, len(word) + 1):
                prefix_dict.add(word[:i])
        return prefix_dict
# ----------------------------------------
#       scoring set up
# ----------------------------------------
    def compute_column_frequencies(self):
        column_freq = [Counter() for _ in range(GRID_SIZE)]
        for entry in self.words:
            word = entry.word
            for i, letter in enumerate(word):
                column_freq[i][letter] += 1
        return column_freq
# ----------------------------------------
#       grid functions
# ----------------------------------------
    def place_word(self, word, slot):
        self.slot_to_word[slot] = word
        for i, (r, c) in enumerate(slot.positions()):
            self.grid[r][c] = word[i]
            self.cell_to_slots[(r,c)].add(slot)

    def remove_word(self, slot):
        if slot not in self.slot_to_word:
            return
        
        word = self.slot_to_word[slot]
        for i, (r, c) in enumerate(slot.positions()):
            self.cell_to_slots[(r,c)].remove(slot)

            if not self.cell_to_slots[(r,c)]:
                self.grid[r][c] = ''
                del self.cell_to_slots[(r,c)]

            else:
                other_slot = next(iter(self.cell_to_slots[(r,c)]))
                other_word = self.slot_to_word[other_slot]
                j = other_slot.positions().index((r,c))
                self.grid[r][c] = other_word[j]

        del self.slot_to_word[slot]

    def is_valid_placement(self, word, slot):
        for i, (r, c) in enumerate(slot.positions()):
            cell = self.grid[r][c]
            if cell != '' and cell != word[i]:
                return False
        return True

    def get_slot_pattern(self, slot):
        return tuple(
            self.grid[r][c] if self.grid[r][c] != '' else '_'
            for r, c in slot.positions()
        )
    
# ----------------------------------------
#       ANALYZE GRID CANDIDATES
# ----------------------------------------
    


# ----------------------------------------
#       SCORE CANDIDATE
# ----------------------------------------  


# ----------------------------------------
#      FIRST & SECOND ROW PLACEMENT 
# ----------------------------------------


# ----------------------------------------
#       FILL IN REMAINING ROWS
# ----------------------------------------


# ----------------------------------------
#       PRINT / BUG TESTING 
# ----------------------------------------

    def print_grid(self):
        for row in self.grid:
            print(' '.join(letter if letter else '.' for letter in row))
        print("---")     

        print("Slot to word mapping:")
        for slot, word in self.slot_to_word.items():
            print(f"{slot.label}: {word}")

###########################################
###########################################

if __name__ == "__main__":
    words_clues = import_words("test_words.txt")
    generator = CrosswordGenerator(words_clues)