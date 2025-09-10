''' ======================================
crossword_generator.py
Generates 5x5 crossword puzzles using 5-letter words.
=========================================='''
from dataclasses import dataclass
from collections import defaultdict, Counter 
import random
import copy

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
        self.grid = [[''] * GRID_SIZE for _ in range(GRID_SIZE)] # live 5x5 grid
        self.slots = self.create_slots() # list of Slot objects
        self.prefix_dict = self.build_prefix_dict() # maps prefixes to possible words
        self.pattern_dict = self.build_pattern_dict() # maps patterns to possible words
        self.slot_to_word = {}

    def create_slots(self):
        slots = []
        for r in range(GRID_SIZE):
            slots.append(Slot(r, 0, True, GRID_SIZE, f"{r+1}-Across"))
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
                if entry not in pattern_dict[pattern]:
                    pattern_dict[pattern].append(entry)
            if entry not in pattern_dict[('_','_','_','_','_')]:
                pattern_dict[('_','_','_','_','_')].append(entry)
        return pattern_dict
    
    def compute_column_frequencies(self):
        """Compute letter frequencies in each column across all words."""
        column_freq = [Counter() for _ in range(GRID_SIZE)]
        for entry in self.words:
            word = entry.word
            for i, letter in enumerate(word):
                column_freq[i][letter] += 1
        return column_freq
    
# ----------------------------------------
# 
# ----------------------------------------
    def get_slot_pattern(self, slot):
        return tuple(
            self.grid[r][c] if self.grid[r][c] != '' else '_'
            for r, c in slot.positions()
        )
    
    def is_valid_placement(self, word, slot):
        for i, (r, c) in enumerate(slot.positions()):
            cell = self.grid[r][c]
            if cell and cell != word[i]:
                return False
        return True
    
# ----------------------------------------
#       ANALYZE GRID CANDIDATES
# ----------------------------------------
    
    def analyze_grid_candidates(self, used_words):
        slot_candidates = {}
        for slot in self.slots:
            pattern = self.get_slot_pattern(slot)
            candidates = [
                entry.word for entry in self.words
                if entry.word not in used_words and self.is_valid_placement(entry.word, slot)
            ]
            slot_candidates[slot] = candidates
        return slot_candidates 

# ----------------------------------------
#       SCORE CANDIDATE
# ----------------------------------------  
    def score_candidates(self, slot, candidate_word, used_words):
        '''
        Simulate placing a word in the slot and return a score based on remaining candidate options for other slots.
        Higher score = more options left for other slots
        '''
        grid_copy = copy.deepcopy(self.grid)
        used_words_copy = used_words.copy()

        for i, (r,c) in enumerate(slot.positions()):
            grid_copy[r][c] = candidate_word[i]
        used_words_copy.add(candidate_word)

        for s in self.slots:
            if s.is_filled(grid_copy) or s == slot:
                continue
            pattern = tuple(grid_copy[r][c] if grid_copy[r][c] != '' else '_' for r, c in s.positions())
            candidates = [entry.word for entry in self.words
                        if entry.word not in used_words_copy and self.is_valid_placement(entry.word, s)]
            
            # if a slot has no candidates 
            if len(candidates) == 0:
                return -1
            

        total_options = sum(len([entry.word for entry in self.pattern_dict.get(
                            tuple(grid_copy[r][c] if grid_copy[r][c] != '' else '_' for r,c in s.positions()),[]
                        ) if entry.word not in used_words_copy]) for s in self.slots if not s.is_filled(grid_copy))

        return total_options 
    
    def score_first_row_word(self, word, column_freq):
        '''Score a word by summing how common its letter are in each column.'''
        return sum(column_freq[i][letter] for i, letter in enumerate(word))
    
# ----------------------------------------
#       SMART GENERATION
# ----------------------------------------
    def smart_generation(self, used_words=None):
        if used_words is None:
            used_words = set()

        # If all slots filled --> Success
        if all(slot.is_filled(self.grid) for slot in self.slots):
            return True

        print("Grid after placement:")                                      ## <-- bug testing ##
        self.print_grid()                                                   ## <-- bug testing ##

        # If slots empty --> start
        if len(used_words) == 0:
            first_slot = self.slots[0]
            candidates = [w.word for w in self.words if len(w.word) == GRID_SIZE]
            
            column_freq = self.compute_column_frequencies()
            scored_candidates = [(w, self.score_first_row_word(w, column_freq)) for w in candidates]
            scored_candidates.sort(key=lambda x: x[1], reverse=True)  # highest score first
            best_first_row_words = [w for w, _ in scored_candidates]
            
            for word in best_first_row_words: 
                self.place_word(word, first_slot)
                used_words.add(word)
                if self.smart_generation(used_words):
                    return True
                self.remove_word(first_slot)
                used_words.remove(word)
            return False

        if len(used_words) == 1:
            second_slot = self.slots[GRID_SIZE]
            candidates = [
                    w.word for w in self.words 
                    if w.word not in used_words and self.is_valid_placement(w.word, second_slot)
            ]                  

            if not candidates:
                return False
            word = random.choice(candidates)
            self.place_word(word, second_slot)
            used_words.add(word)
            print(f"Second word '{word}' placed in {second_slot.label}")                    ## <-- bug testing ##
            self.print_grid()                                                               ## <-- bug testing ##
            return self.smart_generation(used_words)

        # Get candidates for each slot
        slot_candidates = self.analyze_grid_candidates(used_words)
        slot_candidates = {s: c for s, c in slot_candidates.items() if not s.is_filled(self.grid)}


        # Debug: show candidate counts                                     ## <-- bug testing ##
        #print("Slot candidate lengths:")
        #for slot, cands in slot_candidates.items():
            #print(f"{slot.label} ({'Across' if slot.is_row else 'Down'}): {len(cands)}")

        # If any slot has no candidate
        for slot, cands in slot_candidates.items():
            if not slot.is_filled(self.grid) and len(cands) == 0:
                return False
 
        # Choose slot with fewest candidates
        slot_to_fill = min(slot_candidates, key=lambda s: len(slot_candidates[s]))
        candidates = slot_candidates[slot_to_fill]

        random.shuffle(candidates)

        # Score candidates
        scored_candidates = []
        for word in candidates:
            score = self.score_candidates(slot_to_fill, word, used_words)
            if score >= 0:
                scored_candidates.append((word, score))

        # Sort scored candidates
        scored_candidates.sort(key=lambda x: x[1], reverse=True)

        # Recursive placement
        for word, score in scored_candidates:
            self.place_word(word, slot_to_fill)
            used_words.add(word)

            if self.smart_generation(used_words):
                return True
            
            self.remove_word(slot_to_fill)
            used_words.remove(word)

            print(f"Backtracking on slot {slot_to_fill.label} after trying {word}")           ## <-- bug testing ##
    
        #print("Grid after placement:")
        #self.print_grid()

# ----------------------------------------
#       GRID FUNCTIONS
# ----------------------------------------
    def place_word(self, word, slot):
        print(f"Placing '{word}' in {slot.label}")                                                 ## <-- bug testing ##
        for i, (r, c) in enumerate(slot.positions()):
            self.grid[r][c] = word[i]
        self.slot_to_word[slot] = word

    def remove_word(self, slot):
        word = self.slot_to_word.get(slot)
        if not word:
            return
        for i, (r, c) in enumerate(slot.positions()):
            # only clear letter if no other slot uses it
            keep = any((r, c) in s.positions() and self.slot_to_word.get(s) and self.slot_to_word[s][s.positions().index((r, c))] == self.grid[r][c]
                   for s in self.slots if s != slot)
            if not keep:
                self.grid[r][c] = ''
        del self.slot_to_word[slot]
                   
    def generate_clues(self):
        across, down = [], []
        for slot in self.slots:
            word = ''.join(self.grid[r][c] for r, c in slot.positions())
            clue_entry = next((w.clue for w in self.words if w.word == word), "No clue found")
            if slot.is_row:
                across.append((slot.label, clue_entry, word))
            else:
                down.append((slot.label, clue_entry, word))
        return across, down

# ----------------------------------------
#       PRINT / BUG TESTING 
# ----------------------------------------

    def print_grid(self):
        for row in self.grid:
            print(' '.join(letter if letter else '.' for letter in row))
        print("---")     

    def print_clues(self):
        for slot in self.slots:
            word = ''.join(self.grid[r][c] for r, c in slot.positions())
            match = next((w for w in self.words if w.word == word), None)
            if match:
                print(f"{slot.label}: {match.clue} ({word})")
            else:
                print(f"{slot.label}: No clue found ({word})")

###########################################
###########################################

if __name__ == "__main__":
    words_clues = import_words("test_words.txt")
    generator = CrosswordGenerator(words_clues)


    # Run smart generator
    success = generator.smart_generation()
    if success:
        print("Crossword generated successfully!\n")
        generator.print_grid()
        print("\nClues:")
        generator.print_clues()
    else:
        print("No solution found.")