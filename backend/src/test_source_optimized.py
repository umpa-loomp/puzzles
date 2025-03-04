# src/test_source_optimized.py - Modified for Docker
from puzzle import Puzzle
from main import load_puzzles_from_file
from main import app  # Import the Flask app
import os
import time
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from contextlib import redirect_stdout, redirect_stderr

# Add to the top of the file
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import config

# Configure minimal logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Get timeout from environment or use default
try:
    timeout_seconds = int(os.environ.get('TIMEOUT', 3600))  # Default 1 hour
    if timeout_seconds <= 0:
        logger.warning("Invalid timeout value, using default 3600 seconds")
        timeout_seconds = 3600
except ValueError:
    logger.warning("Could not parse timeout value, using default 3600 seconds")
    timeout_seconds = 3600

def load_puzzles_silently(filepath):
    """Load puzzles without printing to stdout"""
    try:
        # Use contextlib to redirect stdout/stderr while loading
        with open(os.devnull, 'w') as null_file:
            with redirect_stdout(null_file), redirect_stderr(null_file):
                logger.info(f"Loading puzzles from {filepath}")
                Puzzle.reset()
                count = load_puzzles_from_file(filepath)
                logger.info(f"Loaded {count} puzzles")
                return count
    except Exception as e:
        logger.error(f"Failed to load puzzles: {e}")
        return 0

# Path to source.txt with fallbacks
source_paths = [
    str(config.SOURCE_FILE),
    "/app/data/source.txt",  # Docker path as fallback
    os.path.join(os.path.dirname(__file__), "source.txt"), # Local fallback
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "large_connected.txt") # Another fallback
]

# Try loading from different path options
puzzle_count = 0
for path in source_paths:
    logger.info(f"Trying to load puzzles from: {path}")
    if os.path.exists(path):
        puzzle_count = load_puzzles_silently(path)
        if puzzle_count > 0:
            logger.info(f"Successfully loaded {puzzle_count} puzzles from {path}")
            break
    else:
        logger.warning(f"File not found: {path}")

if puzzle_count == 0:
    logger.error("Could not load any puzzles. Please check file paths.")
    sys.exit(1)

# Modify find_longest_chain for maximum performance
def find_longest_chain_optimized(timeout_seconds=600):
    """Stripped-down version for maximum performance"""
    puzzles = Puzzle.get_all_puzzles()
    if not puzzles:
        logger.error("No puzzles to process")
        return []
        
    # Build graph (silently)
    graph = {}
    for p in puzzles:
        graph[p.id] = []
        
    connection_count = 0
    for p1 in puzzles:
        for p2 in puzzles:
            if p1.id != p2.id and p1.puzzle_sides['gives'] == p2.puzzle_sides['takes']:
                graph[p1.id].append(p2.id)
                connection_count += 1
    
    # Track variables
    start_time = time.time()
    max_path_length = 0
    max_path = []
    operation_count = 0
    last_update_time = start_time
    processed_nodes = 0
    
    # Optimization: Use memoization to avoid recomputing paths
    memo = {}
    visited_global = set()  # Track globally visited nodes
    
    logger.info(f"Starting search on {len(puzzles)} puzzles with {connection_count} connections")
    logger.info(f"Timeout set to {timeout_seconds} seconds")
    
    # Sort starting nodes by number of outgoing connections (most promising first)
    starting_nodes = sorted(graph.keys(), key=lambda node: len(graph[node]), reverse=True)
    
    # DFS from each starting node
    for start_node in starting_nodes:
        if time.time() - start_time >= timeout_seconds:
            logger.info("Timeout reached, stopping search")
            break
            
        processed_nodes += 1
        
        # Skip if we've already visited this node in a previous search
        if start_node in visited_global and len([start_node]) <= memo.get(start_node, 0):
            continue
            
        # Stack-based DFS with optimization
        stack = [(start_node, [start_node])]
        local_visited = {start_node}
        
        while stack and time.time() - start_time < timeout_seconds:
            current, path = stack.pop()
            
            operation_count += 1
            current_time = time.time()
            
            # Skip if we've seen this node in a better context already
            if current in memo and len(path) <= memo[current]:
                continue
                
            # Update memoization
            memo[current] = len(path)
            visited_global.add(current)
            
            # Minimal logging every 15 seconds
            if current_time - last_update_time > 15:
                elapsed = current_time - start_time
                ops_per_second = operation_count / elapsed if elapsed > 0 else 0
                logger.info(f"Time: {elapsed:.1f}s | Node: {processed_nodes}/{len(graph)} | Ops: {operation_count:,} | Rate: {ops_per_second:.0f} ops/s | Longest chain: {max_path_length}")
                last_update_time = current_time
            
            # Update max path length if we found a longer path
            if len(path) > max_path_length:
                max_path_length = len(path)
                max_path = path.copy()
                logger.info(f"New longest chain found: {max_path_length} puzzles (at {time.time() - start_time:.1f}s)")
                
                # Optimization: Early termination if we found a perfect chain
                if max_path_length == len(puzzles):
                    logger.info("Perfect chain found! Early termination.")
                    break
            
            # Optimization: Early pruning if this path can't beat current max
            remaining_nodes = len(puzzles) - len(visited_global)
            if len(path) + remaining_nodes <= max_path_length:
                continue
            
            # Get neighbors sorted by potential (most promising first)
            neighbors = sorted(
                [n for n in graph[current] if n not in path],
                key=lambda n: len(graph[n]),
                reverse=True
            )
            
            # Push unvisited neighbors to stack
            for neighbor in neighbors:
                if neighbor not in path:  # Avoid cycles
                    stack.append((neighbor, path + [neighbor]))
                    local_visited.add(neighbor)
    
    # Final result only
    total_time = time.time() - start_time
    logger.info(f"\nDONE: Found chain with {max_path_length} puzzles out of {len(puzzles)} total, in {total_time:.2f} seconds")
    
    # Verify chain validity
    is_valid = True
    for i in range(len(max_path) - 1):
        p1 = next((p for p in puzzles if p.id == max_path[i]), None)
        p2 = next((p for p in puzzles if p.id == max_path[i+1]), None)
        
        if not p1 or not p2:
            logger.error(f"Invalid puzzle reference at position {i}")
            is_valid = False
            continue
            
        if p1.puzzle_sides['gives'] != p2.puzzle_sides['takes']:
            logger.error(f"INVALID CONNECTION at position {i}: {p1.puzzle_number} gives {p1.puzzle_sides['gives']} but {p2.puzzle_number} takes {p2.puzzle_sides['takes']}")
            is_valid = False
    
    if is_valid:
        logger.info("Chain validation: VALID ✓")
    else:
        logger.error("Chain validation: INVALID ✗")
    
    # Return the result
    return max_path

# Create results directory
result_dir = os.environ.get('RESULT_DIR', os.path.join(os.path.dirname(os.path.dirname(__file__)), "results"))
try:
    os.makedirs(result_dir, exist_ok=True)
    logger.info(f"Results will be saved to {result_dir}")
except Exception as e:
    logger.error(f"Failed to create results directory: {e}")
    result_dir = os.getcwd()
    logger.info(f"Will save results to current directory: {result_dir}")

# Run the optimized version
try:
    logger.info(f"Starting optimized chain search with {timeout_seconds} seconds timeout")
    start_time = time.time()
    chain = find_longest_chain_optimized(timeout_seconds=timeout_seconds)
    elapsed = time.time() - start_time
    logger.info(f"Total execution time: {elapsed:.2f} seconds")
except KeyboardInterrupt:
    logger.info("Search interrupted by user")
    elapsed = time.time() - start_time
    logger.info(f"Execution time before interrupt: {elapsed:.2f} seconds")
    chain = []
except Exception as e:
    logger.error(f"Error during search: {e}", exc_info=True)
    elapsed = time.time() - start_time
    logger.info(f"Execution time before error: {elapsed:.2f} seconds")
    chain = []

# Save results to file
try:
    result_data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "chain_length": len(chain),
        "execution_time": elapsed,
        "puzzle_count": len(Puzzle.get_all_puzzles()),
        "chain": []
    }

    # Add chain details
    puzzles = Puzzle.get_all_puzzles()
    for i, puzzle_id in enumerate(chain):
        puzzle = next((p for p in puzzles if p.id == puzzle_id), None)
        if not puzzle:
            logger.error(f"Puzzle with ID {puzzle_id} not found")
            continue
        
        # Get connection info if not first puzzle
        connection = ""
        if i > 0:
            prev_id = chain[i-1]
            prev = next((p for p in puzzles if p.id == prev_id), None)
            if prev:
                connection = f"{prev.puzzle_sides['gives']} → {puzzle.puzzle_sides['takes']}"
        
        result_data["chain"].append({
            "position": i + 1,
            "puzzle_number": puzzle.puzzle_number,
            "takes": puzzle.puzzle_sides['takes'],
            "gives": puzzle.puzzle_sides['gives'],
            "connection": connection
        })

    # Save to JSON file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    result_file = os.path.join(result_dir, f"chain_result_{timestamp}.json")
    with open(result_file, 'w') as f:
        json.dump(result_data, f, indent=2)

    # Also save as TXT file for easy reading
    txt_file = os.path.join(result_dir, f"chain_result_{timestamp}.txt")
    with open(txt_file, 'w') as f:
        f.write(f"Puzzle Chain Results\n")
        f.write(f"=================\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Chain length: {len(chain)}\n")
        f.write(f"Total puzzles: {len(Puzzle.get_all_puzzles())}\n")
        f.write(f"Execution time: {elapsed:.2f} seconds\n\n")
        
        f.write("Puzzle Chain:\n")
        f.write("------------\n")
        
        for i, puzzle_id in enumerate(chain):
            puzzle = next((p for p in puzzles if p.id == puzzle_id), None)
            if not puzzle:
                f.write(f"{i+1}. ERROR: Puzzle with ID {puzzle_id} not found\n")
                continue
            
            if i > 0:
                prev_id = chain[i-1]
                prev = next((p for p in puzzles if p.id == prev_id), None)
                if prev:
                    connection = f"({prev.puzzle_sides['gives']} → {puzzle.puzzle_sides['takes']})"
                    f.write(f"  {connection}\n")
                
            f.write(f"{i+1}. Puzzle {puzzle.puzzle_number} - Takes: {puzzle.puzzle_sides['takes']}, Gives: {puzzle.puzzle_sides['gives']}\n")

    logger.info(f"Results saved to {result_file} and {txt_file}")
except Exception as e:
    logger.error(f"Error saving results: {e}")

if __name__ == '__main__':
    logger.info("Starting Flask app")
    try:
        app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
    except Exception as e:
        logger.error(f"Error starting Flask app: {e}")