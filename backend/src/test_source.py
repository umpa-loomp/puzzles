from puzzle import Puzzle
from main import load_puzzles_from_file
import os
import time
import sys

# Add the root directory to the path to find the config module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import config  # Import the config module

# Reset any existing puzzles
Puzzle.reset()

# Get source path from config
source_path = str(config.SOURCE_FILE)

# Check if file exists
if not os.path.exists(source_path):
    print(f"Error: source.txt not found at {source_path}")
    # Try fallback paths
    for path in [
        "/app/data/source.txt",  # Docker path
        os.path.join(os.path.dirname(__file__), "source.txt"),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "large_connected.txt")
    ]:
        if os.path.exists(path):
            print(f"Found alternative path: {path}")
            source_path = path
            break
    else:
        print("No valid source file found. Exiting.")
        exit(1)

def load_source_data(source_path):
    """Load puzzle data from source.txt"""
    try:
        with open(source_path, 'r') as f:
            lines = f.readlines()
            puzzle_lines = [line.strip() for line in lines if line.strip() and len(line.strip()) == 6]
            print(f"source.txt contains {len(puzzle_lines)} puzzle entries")
            return puzzle_lines
    except FileNotFoundError:
        print(f"Error: Could not find source.txt at {source_path}")
        return None
    except Exception as e:
        print(f"Error reading source.txt: {str(e)}")
        return None

# Load puzzles
print(f"Loading puzzles from {source_path}...")
count = load_puzzles_from_file(source_path)
print(f"Successfully loaded {count} puzzles")

# Run the chain finder with a reasonable timeout
print("\nRunning puzzle chain finder on source.txt...")
start_time = time.time()
chain = Puzzle.find_longest_chain(timeout_seconds=120)
elapsed = time.time() - start_time

# Display results
print(f"\nChain finder completed in {elapsed:.2f} seconds")
print(f"Found chain with {len(chain)} puzzles out of {count} total")

# If you want to see some of the puzzles in the chain
if chain:
    puzzles = Puzzle.get_all_puzzles()
    print("\nFirst 5 puzzles in the chain:")
    for i, puzzle_id in enumerate(chain[:5]):
        puzzle = puzzles[puzzle_id]
        print(f"{i+1}. #{puzzle.puzzle_number} - Takes: {puzzle.puzzle_sides['takes']}, Gives: {puzzle.puzzle_sides['gives']}")
    
    if len(chain) > 5:
        print("...")
        print("\nLast 5 puzzles in the chain:")
        for i, puzzle_id in enumerate(chain[-5:]):
            puzzle = puzzles[puzzle_id]
            print(f"{len(chain)-4+i}. #{puzzle.puzzle_number} - Takes: {puzzle.puzzle_sides['takes']}, Gives: {puzzle.puzzle_sides['gives']}")