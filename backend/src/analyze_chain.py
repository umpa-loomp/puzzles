import os
import time
from puzzle import Puzzle
from main import load_puzzles_from_file

def analyze_puzzle_chain(chain, min_length=64, verbose=True):
    """Analyze a puzzle chain for validity and completeness"""
    puzzles = Puzzle.get_all_puzzles()
    total_puzzles = len(puzzles)
    chain_length = len(chain)
    
    if chain_length < min_length:
        print(f"WARNING: Chain length {chain_length} is less than minimum requested {min_length}")
    
    print(f"\n===== CHAIN ANALYSIS =====")
    print(f"Total puzzles: {total_puzzles}")
    print(f"Chain length: {chain_length} ({(chain_length/total_puzzles*100):.1f}% of total puzzles)")
    
    # 1. Validate connections
    connection_errors = []
    for i in range(chain_length - 1):
        p1 = puzzles[chain[i]]
        p2 = puzzles[chain[i+1]]
        if p1.puzzle_sides['gives'] != p2.puzzle_sides['takes']:
            connection_errors.append(
                f"Position {i}->{i+1}: {p1.puzzle_number} gives {p1.puzzle_sides['gives']} but {p2.puzzle_number} takes {p2.puzzle_sides['takes']}"
            )
    
    if connection_errors:
        print(f"\n❌ INVALID CONNECTIONS FOUND: {len(connection_errors)}")
        for error in connection_errors:
            print(f"  {error}")
    else:
        print(f"\n✅ All connections are valid")
    
    # 2. Check ID uniqueness
    chain_ids = set(chain)
    unique_ids = len(chain_ids)
    
    if unique_ids != chain_length:
        print(f"\n❌ DUPLICATE IDs FOUND: Chain has {chain_length} puzzles but only {unique_ids} unique IDs")
        
        # Find duplicates
        id_counts = {}
        for puzzle_id in chain:
            id_counts[puzzle_id] = id_counts.get(puzzle_id, 0) + 1
            
        duplicates = {puzzle_id: count for puzzle_id, count in id_counts.items() if count > 1}
        print(f"  Duplicated IDs: {len(duplicates)}")
        
        if verbose:
            for puzzle_id, count in duplicates.items():
                puzzle = puzzles[puzzle_id]
                print(f"  ID {puzzle_id} (Puzzle #{puzzle.puzzle_number}) appears {count} times")
    else:
        print(f"\n✅ All IDs in the chain are unique")
    
    # 3. Identify unused puzzles
    all_ids = set(range(len(puzzles)))
    unused_ids = all_ids - chain_ids
    unused_count = len(unused_ids)
    
    # Verify that unused + used = all (important check added)
    used_count = len(chain_ids)
    print(f"\nPuzzle Counts Verification:")
    print(f"  Total puzzles: {total_puzzles}")
    print(f"  Used in chain: {used_count} ({used_count/total_puzzles*100:.1f}%)")
    print(f"  Unused puzzles: {unused_count} ({unused_count/total_puzzles*100:.1f}%)")
    
    if used_count + unused_count == total_puzzles:
        print(f"  ✅ Verification passed: {used_count} + {unused_count} = {total_puzzles}")
    else:
        print(f"  ❌ Verification failed: {used_count} + {unused_count} = {used_count + unused_count} (expected {total_puzzles})")
    
    if verbose and unused_ids:
        print("\nSample of unused puzzles:")
        for i, puzzle_id in enumerate(list(unused_ids)[:10]):  # Show first 10 unused
            puzzle = puzzles[puzzle_id]
            print(f"  {i+1}. ID {puzzle_id}: #{puzzle.puzzle_number} - Takes: {puzzle.puzzle_sides['takes']}, Gives: {puzzle.puzzle_sides['gives']}")
        if unused_count > 10:
            print(f"  ... and {unused_count - 10} more")
    
    # 4. Check if any unused puzzles could connect to the chain
    if unused_ids:
        # Get start and end of chain
        chain_start = puzzles[chain[0]]
        chain_end = puzzles[chain[-1]]
        
        # Check which unused puzzles could connect to start/end
        could_connect_start = []
        could_connect_end = []
        
        for puzzle_id in unused_ids:
            unused_puzzle = puzzles[puzzle_id]
            
            # Could connect to start?
            if unused_puzzle.puzzle_sides['gives'] == chain_start.puzzle_sides['takes']:
                could_connect_start.append((puzzle_id, unused_puzzle.puzzle_number))
                
            # Could connect to end?
            if unused_puzzle.puzzle_sides['takes'] == chain_end.puzzle_sides['gives']:
                could_connect_end.append((puzzle_id, unused_puzzle.puzzle_number))
        
        print(f"\n{len(could_connect_start)} unused puzzles could connect to FRONT of chain")
        print(f"{len(could_connect_end)} unused puzzles could connect to END of chain")
        
        if verbose:
            if could_connect_start:
                print("\nCould connect to FRONT:")
                for i, (puzzle_id, puzzle_num) in enumerate(could_connect_start[:5]):
                    print(f"  {i+1}. ID {puzzle_id}: #{puzzle_num}")
                if len(could_connect_start) > 5:
                    print(f"  ... and {len(could_connect_start) - 5} more")
                    
            if could_connect_end:
                print("\nCould connect to END:")
                for i, (puzzle_id, puzzle_num) in enumerate(could_connect_end[:5]):
                    print(f"  {i+1}. ID {puzzle_id}: #{puzzle_num}")
                if len(could_connect_end) > 5:
                    print(f"  ... and {len(could_connect_end) - 5} more")
    
    # NEW: Find branching points in chain (where alternative paths were possible)
    print("\n===== BRANCHING ANALYSIS =====")
    
    # Build graph of puzzle connections to analyze branching
    graph = {}
    for p in puzzles:
        graph[p.id] = []
    
    # Add connections based on gives->takes matching
    for p1 in puzzles:
        for p2 in puzzles:
            if p1.id != p2.id and p1.puzzle_sides['gives'] == p2.puzzle_sides['takes']:
                graph[p1.id].append(p2.id)
    
    # Find branch points in the chain
    branching_points = []
    for i, puzzle_id in enumerate(chain[:-1]):  # Skip the last element as it can't branch forward
        current_puzzle = puzzles[puzzle_id]
        next_id_in_chain = chain[i+1]
        
        # Find all possible connections from this point
        possible_next_ids = graph[puzzle_id]
        
        # Filter out the one we actually used in the chain
        alternate_paths = [id for id in possible_next_ids if id != next_id_in_chain]
        
        if alternate_paths:
            branching_points.append({
                "position": i,
                "puzzle_id": puzzle_id,
                "puzzle_number": current_puzzle.puzzle_number,
                "used_next": next_id_in_chain,
                "alternate_ids": alternate_paths,
                "alternate_count": len(alternate_paths)
            })
    
    # Report branch points
    if branching_points:
        print(f"Found {len(branching_points)} potential branching points in the chain")
        
        if verbose:
            print("\nTop 10 branching points:")
            # Sort by number of alternatives
            for i, bp in enumerate(sorted(branching_points, key=lambda x: x['alternate_count'], reverse=True)[:10]):
                used_next_puzzle = puzzles[bp['used_next']]
                print(f"  {i+1}. Position {bp['position']+1}: Puzzle #{bp['puzzle_number']} (ID {bp['puzzle_id']}) → #{used_next_puzzle.puzzle_number}")
                print(f"     Used connection: Gives {puzzles[bp['puzzle_id']].puzzle_sides['gives']} → Takes {used_next_puzzle.puzzle_sides['takes']}")
                print(f"     Alternatives: {bp['alternate_count']} other puzzles could have followed")
                
                # Show a few alternatives
                if bp['alternate_count'] > 0:
                    print(f"     Example alternatives:")
                    for j, alt_id in enumerate(bp['alternate_ids'][:3]):
                        alt_puzzle = puzzles[alt_id]
                        print(f"       - #{alt_puzzle.puzzle_number} (ID {alt_id}): Takes {alt_puzzle.puzzle_sides['takes']}, Gives {alt_puzzle.puzzle_sides['gives']}")
                    if bp['alternate_count'] > 3:
                        print(f"       ... and {bp['alternate_count'] - 3} more")
    else:
        print("No branching opportunities found in the chain - all connections were the only option")
    
    # 5. Format the chain as requested
    if verbose:
        print("\n===== CHAIN VISUALIZATION =====")
        
        # Format 1: "(give to take side number) - ID - (give to take side number). the next one in the chain"
        print("\nFormat 1:")
        formatted_chain_1 = []
        for i, puzzle_id in enumerate(chain):
            puzzle = puzzles[puzzle_id]
            takes = puzzle.puzzle_sides['takes']
            gives = puzzle.puzzle_sides['gives']
            
            if i == 0:
                # First puzzle
                entry = f"(START) - {puzzle_id} - ({takes} → {gives})"
            else:
                # Middle puzzle
                entry = f"({takes} → {gives}) - {puzzle_id} - ({takes} → {gives})"
                
            formatted_chain_1.append(entry)
            
            # Print only first and last few entries if chain is long
            if chain_length > 20:
                if i < 5:
                    print(f"  {i+1}. {entry}")
                elif i >= chain_length - 5:
                    print(f"  {i+1}. {entry}")
                elif i == 5:
                    print("  ...")
            else:
                print(f"  {i+1}. {entry}")
        
        # Format 2: "number.number"
        print("\nFormat 2:")
        formatted_chain_2 = []
        for i, puzzle_id in enumerate(chain):
            puzzle = puzzles[puzzle_id]
            formatted_chain_2.append(puzzle.puzzle_number)
            
        # Join with dots
        chain_str = ".".join(formatted_chain_2)
        
        # Print just the beginning and end if too long
        if len(chain_str) > 100:
            print(f"  {chain_str[:50]}...{chain_str[-50:]}")
        else:
            print(f"  {chain_str}")
    
    return {
        "total_puzzles": total_puzzles,
        "chain_length": chain_length,
        "is_valid": len(connection_errors) == 0,
        "has_duplicates": unique_ids != chain_length,
        "used_count": used_count,
        "unused_count": unused_count,
        "verification_passed": used_count + unused_count == total_puzzles,
        "branching_points": len(branching_points),
        "could_extend_start": len(could_connect_start) if 'could_connect_start' in locals() else 0,
        "could_extend_end": len(could_connect_end) if 'could_connect_end' in locals() else 0
    }

def find_chain_with_length(target_length=64, timeout=60):
    """Find a chain with at least the target length"""
    print(f"Searching for chain with length >= {target_length}...")
    
    start_time = time.time()
    chain = Puzzle.find_longest_chain(timeout_seconds=timeout)
    elapsed = time.time() - start_time
    
    print(f"Chain finder completed in {elapsed:.2f} seconds")
    
    if len(chain) >= target_length:
        print(f"✓ Found chain with {len(chain)} puzzles (meets target of {target_length})")
    else:
        print(f"✗ Found chain with only {len(chain)} puzzles (target was {target_length})")
    
    return chain

def main():
    # Reset puzzles
    Puzzle.reset()
    
    # Path to source.txt
    source_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "source.txt")
    
    if not os.path.exists(source_path):
        print(f"Error: source.txt not found at {source_path}")
        return
    
    # Load puzzles
    print(f"Loading puzzles from {source_path}")
    count = load_puzzles_from_file(source_path)
    print(f"Loaded {count} puzzles")
    
    # Find chain with desired length
    chain = find_chain_with_length(target_length=64, timeout=10)
    
    # Analyze the chain
    analysis = analyze_puzzle_chain(chain)

if __name__ == "__main__":
    main()