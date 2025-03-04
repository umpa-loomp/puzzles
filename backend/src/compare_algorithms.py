from puzzle import Puzzle
from main import load_puzzles_from_file
from optimized_graph_algorithms import OptimizedGraphAlgorithms
import os
import time

def build_graph_from_puzzles():
    """Convert puzzles to graph structure needed by optimized algorithms"""
    puzzles = Puzzle.get_all_puzzles()
    print(f"Building graph from {len(puzzles)} puzzles...")
    
    # Create graph structure
    graph = {}
    for p in puzzles:
        graph[p.id] = []
    
    # Add connections
    connection_count = 0
    for p1 in puzzles:
        for p2 in puzzles:
            if p1.id != p2.id and p1.puzzle_sides['gives'] == p2.puzzle_sides['takes']:
                graph[p1.id].append(p2.id)
                connection_count += 1
    
    print(f"Built graph with {len(puzzles)} nodes and {connection_count} connections")
    return graph, puzzles

def display_path(path, puzzles):
    """Display the puzzle chain in a readable format"""
    if not path:
        print("No path found")
        return
    
    print(f"Path length: {len(path)}")
    print("\nFirst 5 puzzles in the chain:")
    for i, puzzle_id in enumerate(path[:5]):
        puzzle = puzzles[puzzle_id]
        print(f"{i+1}. ID {puzzle_id}: #{puzzle.puzzle_number} - Takes: {puzzle.puzzle_sides['takes']}, Gives: {puzzle.puzzle_sides['gives']}")
    
    if len(path) > 10:
        print("...")
        print("\nLast 5 puzzles in the chain:")
        for i, puzzle_id in enumerate(path[-5:]):
            puzzle = puzzles[puzzle_id]
            print(f"{len(path)-4+i}. ID {puzzle_id}: #{puzzle.puzzle_number} - Takes: {puzzle.puzzle_sides['takes']}, Gives: {puzzle.puzzle_sides['gives']}")

def test_algorithms():
    """Test all algorithms on the puzzle data"""
    # Reset puzzles
    Puzzle.reset()
    
    # Load source.txt
    source_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "source.txt")
    if not os.path.exists(source_path):
        print(f"Error: source.txt not found at {source_path}")
        return
        
    count = load_puzzles_from_file(source_path)
    print(f"Loaded {count} puzzles from {source_path}")
    
    # Build graph
    graph, puzzles = build_graph_from_puzzles()
    
    # Test different algorithms (60 seconds each)
    timeout = 60
    algorithms = [
        "iterative_dfs",  # Optimized DFS (default)
        "dp",             # Dynamic programming approach
        "bidirectional",  # Bidirectional search
        "a_star",         # A* search with heuristics
        "topo"            # Topological sort (for DAGs)
    ]
    
    results = {}
    
    for algo in algorithms:
        print(f"\n===== Testing algorithm: {algo} =====")
        start_time = time.time()
        
        try:
            path = OptimizedGraphAlgorithms.find_longest_path(graph, timeout_seconds=timeout, algorithm=algo)
            elapsed = time.time() - start_time
            
            results[algo] = {
                "path": path,
                "length": len(path),
                "time": elapsed
            }
            
            print(f"Algorithm completed in {elapsed:.2f} seconds")
            display_path(path, puzzles)
            
        except Exception as e:
            print(f"Error with algorithm {algo}: {str(e)}")
    
    # Compare results
    print("\n===== ALGORITHM COMPARISON =====")
    print(f"{'Algorithm':<15} {'Length':<10} {'Time (s)':<10}")
    print("-" * 35)
    
    for algo, data in results.items():
        print(f"{algo:<15} {data['length']:<10} {data['time']:.2f}")
    
    # Find best algorithm
    if results:
        best_algo = max(results.items(), key=lambda x: (x[1]['length'], -x[1]['time']))
        print(f"\nBest result: {best_algo[0]} with length {best_algo[1]['length']} in {best_algo[1]['time']:.2f}s")

if __name__ == "__main__":
    test_algorithms()