# backend/src/puzzle.py
import sys
import random
import time
import os
import json
from datetime import datetime
import logging

# Configure logging
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(log_dir, "puzzle.log"),
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class Puzzle:
    _puzzles = []
    _next_id = 0

    def __init__(self, puzzle_number):
        """Initialize a puzzle with validation"""
        try:
            if not isinstance(puzzle_number, str) or len(puzzle_number) != 6 or not puzzle_number.isdigit():
                raise ValueError(f"Puzzle number must be a 6-digit string, got: '{puzzle_number}'")
            
            self.id = Puzzle._next_id
            Puzzle._next_id += 1
            
            self.puzzle_number = puzzle_number
            self.puzzle_sides = {
                "takes": puzzle_number[:2],
                "gives": puzzle_number[4:]
            }
        except Exception as e:
            logger.error(f"Error creating puzzle: {e}")
            raise

    def get_puzzle_info(self):
        """Get puzzle information as a dictionary"""
        return {
            "id": self.id,
            "puzzle_number": self.puzzle_number,
            "puzzle_sides": self.puzzle_sides
        }

    @classmethod
    def reset(cls):
        """Reset the puzzle collection and ID counter"""
        cls._puzzles = []
        cls._next_id = 0
        logger.info("Puzzle collection and ID counter reset")

    @classmethod
    def add_puzzle_direct(cls, puzzle_number):
        """Add a puzzle directly to the collection"""
        try:
            puzzle = cls(puzzle_number)
            cls._puzzles.append(puzzle)
            return puzzle
        except ValueError as e:
            logger.error(f"Failed to add puzzle: {e}")
            return None
        
    @classmethod
    def get_all_puzzles(cls):
        """Get all puzzles in the collection"""
        return cls._puzzles
    
    @classmethod
    def find_longest_chain(cls, timeout_seconds=600, export_paths=True):
        """Find longest chain - optimized to find maximum depth first, then a single path"""
        puzzles = cls.get_all_puzzles()
        if not puzzles:
            logger.warning("No puzzles to process")
            return []

        # Build graph of puzzle connections
        logger.info("Building puzzle connection graph...")
        graph = {p.id: [] for p in puzzles}

        # Add connections based on gives->takes matching
        connection_count = 0
        for p1 in puzzles:
            for p2 in puzzles:
                if p1.id != p2.id and p1.puzzle_sides['gives'] == p2.puzzle_sides['takes']:
                    graph[p1.id].append(p2.id)
                    connection_count += 1

        # Set up tracking variables
        start_time = time.time()
        max_path_length = 0
        max_path = []
        operation_count = 0
        last_update_time = start_time
        processed_nodes = 0
        max_length_count = 0  # Track how many times we find maximum length 

        # Calculate parameters
        N = len(puzzles)
        C = connection_count / N if N > 0 else 0
        D = min(N, 30)  # Cap max depth estimate at 30

        # Calculate estimated max operations
        if C > 1:
            formula = f"N*(C^min(D,30)) = {N}*({C:.2f}^{min(D,30)})"
            estimated_max_ops = min(int(N * (C ** min(D, 30))), 100_000_000)
        else:
            formula = f"N*N*10 = {N}*{N}*10"
            estimated_max_ops = N * N * 10
        
        # Cap at reasonable maximum
        if estimated_max_ops > 100_000_000:
            estimated_max_ops = 100_000_000
            formula += " (capped at 100,000,000)"

        # Print initial information
        logger.info(f"Built graph with {N} nodes (N) and {connection_count} connections (C)")
        logger.info(f"Starting search with {timeout_seconds} second timeout...")  
        logger.info(f"Graph parameters: N={N} nodes, C={C:.2f} connections/node, D={min(D, 30)} (max depth used in formula)")
        logger.info(f"Estimated max operations: {estimated_max_ops:,} ({formula})")

        # For tracking operation rate
        ops_history = []
        
        # PHASE 1: Find maximum path length
        logger.info("\n==== PHASE 1: Finding maximum path length ====")

        # Implement memoization to avoid recomputing paths
        memo = {}

        # Attempt to find longest path from each starting node
        for start_node in graph:
            if time.time() - start_time >= timeout_seconds:
                logger.info(f"Timeout reached after {timeout_seconds:.2f} seconds")
                break

            processed_nodes += 1

            # Use stack-based iterative DFS with cycle detection
            stack = [(start_node, [start_node])]
            visited = set()

            while stack and time.time() - start_time < timeout_seconds:     
                current, path = stack.pop()
                
                # Skip if we've seen this node in a better context
                if current in visited and len(path) <= memo.get(current, 0):
                    continue
                
                visited.add(current)
                memo[current] = max(memo.get(current, 0), len(path))

                operation_count += 1
                current_time = time.time()

                # Log progress every 5 seconds only
                if current_time - last_update_time > 5:
                    elapsed = current_time - start_time
                    ops_per_second = operation_count / elapsed if elapsed > 0 else 0

                    # Track ops rate history for smoothing
                    ops_history.append(ops_per_second)
                    if len(ops_history) > 5:
                        ops_history.pop(0)

                    # Calculate average rate
                    avg_ops_per_second = sum(ops_history) / len(ops_history) if ops_history else ops_per_second

                    # Progress info
                    logger.info(f"Operations: {operation_count:,}")
                    logger.info(f"Performance: {avg_ops_per_second:,.0f} ops/sec")
                    logger.info(f"Best chain length: {max_path_length} puzzles (found {max_length_count} times)")
                    logger.info(f"Time: {elapsed:.1f}s elapsed, {elapsed/timeout_seconds*100:.1f}% of timeout used")
                    logger.info(f"Processed {processed_nodes}/{len(graph)} starting nodes")
                    logger.info("")  # Add new line for readability

                    last_update_time = current_time

                # Update max path length if we found a longer path
                if len(path) > max_path_length:
                    max_path_length = len(path)
                    max_path = path.copy()  # Store this path for reference 
                    max_length_count = 1  # Reset counter when we find a longer path
                elif len(path) == max_path_length:
                    max_length_count += 1  # Increment for paths of same max length

                # Optimization: Early termination if we found a perfect chain
                if max_path_length == len(puzzles):
                    logger.info("Perfect chain found! Ending search early.")
                    break

                # Push unvisited neighbors to stack in reverse order (to simulate DFS)
                for neighbor in sorted(graph[current], reverse=True):
                    if neighbor not in path:  # Avoid cycles
                        # Skip if this path won't beat our current max
                        remaining_nodes = len(puzzles) - len(path)
                        if len(path) + remaining_nodes <= max_path_length:
                            continue
                            
                        stack.append((neighbor, path + [neighbor]))

        # Final report for Phase 1
        total_time = time.time() - start_time
        final_ops_per_second = operation_count / total_time if total_time > 0 else 0

        logger.info("\n==== PHASE 1 COMPLETE ====")
        logger.info(f"Max path length: {max_path_length} puzzles (found {max_length_count} times)")
        logger.info(f"Operations: {operation_count:,}. Time: {total_time:.2f} seconds. Ops/s: {final_ops_per_second:,.0f}")
        
        # Special message if we found a perfect chain
        if max_path_length == len(puzzles):
            logger.info("\n*** Perfect chain found! Chain includes all puzzles in the dataset. ***")
        
        # PHASE 2: If we have time left, verify we have a valid path of max length
        if max_path_length > 0 and len(max_path) == max_path_length:
            logger.info("\n==== PHASE 2: Verifying chain ====")

            # Verify chain connections
            is_valid = True
            for i in range(len(max_path) - 1):
                p1 = next((p for p in puzzles if p.id == max_path[i]), None)
                p2 = next((p for p in puzzles if p.id == max_path[i+1]), None)
                
                if not p1 or not p2:
                    logger.error(f"Invalid puzzle reference at position {i}")
                    is_valid = False
                    break
                    
                if p1.puzzle_sides['gives'] != p2.puzzle_sides['takes']:    
                    logger.error(f"Invalid connection at position {i}: {p1.puzzle_number} gives {p1.puzzle_sides['gives']} but {p2.puzzle_number} takes {p2.puzzle_sides['takes']}")
                    is_valid = False

            if is_valid:
                logger.info("Chain is valid! All connections verified.")
            else:
                logger.warning("Chain has invalid connections! Attempting to find a valid chain...")

        # Export the single result to JSON
        json_filepath = None
        if export_paths and max_path_length > 0:
            try:
                result_data = {
                    "timestamp": time.strftime("%Y%m%d_%H%M%S"),
                    "search_time_seconds": total_time,
                    "operations": operation_count,
                    "max_path_length": max_path_length,
                    "path": []
                }

                # Add path details if we have one
                if max_path:
                    for i, node_id in enumerate(max_path):
                        p = next((p for p in puzzles if p.id == node_id), None)
                        if p:
                            result_data["path"].append({
                                "position": i,
                                "id": p.id,
                                "number": p.puzzle_number,
                                "takes": p.puzzle_sides['takes'],
                                "gives": p.puzzle_sides['gives']
                            })

                # Create export directory if it doesn't exist
                export_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "exports")
                os.makedirs(export_dir, exist_ok=True)

                # Write to JSON file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                json_filename = f"longest_chain_{timestamp}.json"
                json_filepath = os.path.join(export_dir, json_filename)

                with open(json_filepath, 'w') as f:
                    json.dump(result_data, f, indent=2)

                logger.info(f"\nExported result to: {json_filepath}")
            except Exception as e:
                logger.error(f"Error exporting results: {e}")

        logger.info(f"\nSearch complete after {total_time:.2f} seconds")
        logger.info(f"Processed {processed_nodes}/{len(graph)} starting nodes")
        logger.info(f"Total operations: {operation_count:,}")
        logger.info(f"Found longest chain with {max_path_length} puzzles (found {max_length_count} times)")

        if export_paths and json_filepath:
            logger.info(f"Results exported to: {json_filepath}")

        if C > 1 and N * (C ** min(D, 30)) <= 100_000_000:
            logger.info(f"Formula used: N*(C^min(D,30)) = {N}*({C:.2f}^{min(D,30)}) = {estimated_max_ops:,}")
        
        return max_path

    @classmethod
    def export_path(cls, path, puzzles, first_found=False):
        """Export a single path to a text file"""
        try:
            # Create export directory if it doesn't exist
            export_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "exports")
            os.makedirs(export_dir, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            prefix = "first_longest" if first_found else "additional"
            filename = f"{prefix}_path_{timestamp}.txt"
            filepath = os.path.join(export_dir, filename)

            # Write path to file
            with open(filepath, 'w') as f:
                f.write(f"Path length: {len(path)} puzzles\n")
                f.write("----------------------------\n")
                for i, node_id in enumerate(path):
                    p = next((p for p in puzzles if p.id == node_id), None)
                    if not p:
                        f.write(f"{i+1}. ERROR: Puzzle with ID {node_id} not found\n")
                        continue
                    f.write(f"{i+1}. Puzzle #{p.puzzle_number} - Takes: {p.puzzle_sides['takes']}, Gives: {p.puzzle_sides['gives']}\n")

            logger.info(f"Exported path to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error exporting path: {e}")
            return None

    @classmethod
    def export_all_paths(cls, paths, puzzles):
        """Export all longest paths to JSON and summary TXT"""
        try:
            # Create export directory if it doesn't exist
            export_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "exports")
            os.makedirs(export_dir, exist_ok=True)

            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_filename = f"all_longest_paths_{timestamp}.json"
            txt_filename = f"all_longest_paths_{timestamp}.txt"
            json_filepath = os.path.join(export_dir, json_filename)
            txt_filepath = os.path.join(export_dir, txt_filename)

            # Prepare data for JSON
            path_data = {
                "timestamp": timestamp,
                "total_paths": len(paths),
                "path_length": len(paths[0]) if paths else 0,
                "paths": []
            }

            # Write TXT file with just the paths
            with open(txt_filepath, 'w') as f:
                f.write(f"All longest paths - {len(paths)} paths of {len(paths[0]) if paths else 0} puzzles each\n")
                f.write("======================================================\n\n")

                # Process each path
                for path_index, path in enumerate(paths):
                    path_info = {
                        "path_index": path_index,
                        "puzzles": []
                    }

                    f.write(f"PATH #{path_index + 1}\n")
                    f.write("-" * 30 + "\n")

                    # Process each puzzle in the path
                    for i, node_id in enumerate(path):
                        p = next((p for p in puzzles if p.id == node_id), None)
                        if not p:
                            f.write(f"{i+1}. ERROR: Puzzle with ID {node_id} not found\n")
                            continue
                            
                        puzzle_info = {
                            "position": i,
                            "id": p.id,
                            "number": p.puzzle_number,
                            "takes": p.puzzle_sides['takes'],
                            "gives": p.puzzle_sides['gives']
                        }
                        path_info["puzzles"].append(puzzle_info)

                        # Add to text file
                        f.write(f"{i+1}. #{p.puzzle_number} - Takes: {p.puzzle_sides['takes']}, Gives: {p.puzzle_sides['gives']}\n")

                    path_data["paths"].append(path_info)
                    f.write("\n\n")
            
            # Write JSON file with complete info
            with open(json_filepath, 'w') as f:
                json.dump(path_data, f, indent=2)

            logger.info(f"Exported all paths to:")
            logger.info(f"  - JSON: {json_filepath}")
            logger.info(f"  - TXT: {txt_filepath}")
            
            return (json_filepath, txt_filepath)
        except Exception as e:
            logger.error(f"Error exporting all paths: {e}")
            return (None, None)

    @classmethod
    def debug_chain(cls, chain_ids):
        """Print detailed information about a chain for debugging"""        
        if not chain_ids:
            logger.warning("Empty chain, nothing to debug")
            return

        puzzles = cls.get_all_puzzles()
        logger.info(f"\nDebug Chain ({len(chain_ids)} puzzles):")
        logger.info("-" * 50)

        for i, node_id in enumerate(chain_ids):
            p = next((p for p in puzzles if p.id == node_id), None)
            if not p:
                logger.error(f"ERROR: Puzzle with ID {node_id} not found!")        
                continue

            logger.info(f"{i+1}. ID: {p.id}, Number: {p.puzzle_number}")
            logger.info(f"   Takes: {p.puzzle_sides['takes']}, Gives: {p.puzzle_sides['gives']}")

            # Show connection to next puzzle
            if i < len(chain_ids) - 1:
                next_id = chain_ids[i+1]
                next_p = next((p for p in puzzles if p.id == next_id), None)
                if next_p:
                    if p.puzzle_sides['gives'] == next_p.puzzle_sides['takes']:
                        logger.info(f"   ✓ Connects to next: {p.puzzle_sides['gives']} → {next_p.puzzle_sides['takes']}")
                    else:
                        logger.error(f"   ✗ INVALID CONNECTION: {p.puzzle_sides['gives']} ≠ {next_p.puzzle_sides['takes']}")
                else:
                    logger.error(f"   ✗ Next puzzle with ID {next_id} not found!")

            logger.info("-" * 50)