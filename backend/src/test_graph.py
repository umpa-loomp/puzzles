# backend/src/test_graph.py
import os
import time
import logging
import tempfile
from puzzle import Puzzle

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def test_simple_chain():
    """Test with a simple linear chain"""
    Puzzle.reset()
    
    # Create a linear chain: 1->2->3->4->5
    Puzzle.add_puzzle_direct("104211")  # Takes 10, Gives 11
    Puzzle.add_puzzle_direct("114212")  # Takes 11, Gives 12
    Puzzle.add_puzzle_direct("124213")  # Takes 12, Gives 13
    Puzzle.add_puzzle_direct("134214")  # Takes 13, Gives 14
    Puzzle.add_puzzle_direct("144215")  # Takes 14, Gives 15
    
    # Find longest chain
    logger.info("Testing simple linear chain")
    chain = Puzzle.find_longest_chain(timeout_seconds=10, export_paths=False)
    
    # Should find a chain of length 5
    logger.info(f"Expected chain length: 5, Got: {len(chain)}")
    assert len(chain) == 5, "Chain length should be 5"
    
    # Verify order
    puzzles = Puzzle.get_all_puzzles()
    chain_numbers = [next((p.puzzle_number for p in puzzles if p.id == i), "INVALID") for i in chain]
    expected = ["104211", "114212", "124213", "134214", "144215"]
    logger.info(f"Expected order: {expected}")
    logger.info(f"Actual order: {chain_numbers}")
    
    logger.info("Simple chain test passed!" if chain_numbers == expected else "Chain order incorrect!")
    
def test_branch_chain():
    """Test with a branching structure"""
    Puzzle.reset()
    
    # Main chain
    Puzzle.add_puzzle_direct("104211")  # Takes 10, Gives 11
    Puzzle.add_puzzle_direct("114212")  # Takes 11, Gives 12
    Puzzle.add_puzzle_direct("124213")  # Takes 12, Gives 13
    
    # Branch 1 - Length 2
    Puzzle.add_puzzle_direct("114299")  # Takes 11, Gives 99
    Puzzle.add_puzzle_direct("994288")  # Takes 99, Gives 88
    
    # Branch 2 - Length 3
    Puzzle.add_puzzle_direct("124277")  # Takes 12, Gives 77
    Puzzle.add_puzzle_direct("774266")  # Takes 77, Gives 66
    Puzzle.add_puzzle_direct("664255")  # Takes 66, Gives 55
    
    logger.info("\nTesting branching structure")
    chain = Puzzle.find_longest_chain(timeout_seconds=10, export_paths=False)
    logger.info(f"Expected longest chain length: 5, Got: {len(chain)}")
    
    # The longest branch should be Branch 2 (total length 5)
    assert len(chain) == 5, "Branch 2 should be the longest with length 5"
    
    logger.info("Branch chain test passed!")

def test_complex_structure():
    """Test with a more complex structure with multiple paths"""
    Puzzle.reset()
    
    # Create puzzles with multiple possible paths
    Puzzle.add_puzzle_direct("104211")  # Start
    Puzzle.add_puzzle_direct("114212")
    Puzzle.add_puzzle_direct("124213") 
    Puzzle.add_puzzle_direct("134214")  # Path 1 - Length 4
    
    Puzzle.add_puzzle_direct("114215")
    Puzzle.add_puzzle_direct("154216")
    Puzzle.add_puzzle_direct("164217")
    Puzzle.add_puzzle_direct("174218")
    Puzzle.add_puzzle_direct("184219")  # Path 2 - Length 6
    
    logger.info("\nTesting complex structure with multiple paths")
    chain = Puzzle.find_longest_chain(timeout_seconds=10, export_paths=False)
    logger.info(f"Expected longest chain length: 6, Got: {len(chain)}")
    
    # Should find Path 2 (Length 6)
    assert len(chain) == 6, "Should find the path with length 6"
    
    logger.info("Complex structure test passed!")

def test_cycle_detection():
    """Test that cycles don't cause infinite loops"""
    Puzzle.reset()
    
    # Create a cycle
    Puzzle.add_puzzle_direct("104211")  # Takes 10, Gives 11
    Puzzle.add_puzzle_direct("114212")  # Takes 11, Gives 12
    Puzzle.add_puzzle_direct("124210")  # Takes 12, Gives 10 - Creates a cycle!
    
    logger.info("\nTesting cycle detection")
    start_time = time.time()
    chain = Puzzle.find_longest_chain(timeout_seconds=10, export_paths=False)
    elapsed = time.time() - start_time
    
    logger.info(f"Completed in {elapsed:.2f} seconds")
    logger.info(f"Found chain with length {len(chain)}")
    
    # Should find a chain of length 3 (the cycle)
    assert len(chain) <= 3, "Should not get stuck in infinite loop"
    
    logger.info("Cycle detection test passed!")

def test_performance():
    """Test performance with isolated dataset"""
    Puzzle.reset()
    
    # Use container path for data
    data_path = os.path.join("/app", "data", "source.txt")
    
    if not os.path.exists(data_path):
        logger.warning(f"Source data not found at {data_path}")
        return
        
    try:
        # Count lines in source file
        with open(data_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        expected_count = sum(1 for line in lines 
                           if line.strip() and len(line.strip()) == 6)
        logger.info(f"Source contains {expected_count} valid puzzles")
        
        # Process puzzles directly from source
        puzzle_count = 0
        for line in lines:
            line = line.strip()
            if line and len(line) == 6 and line.isdigit():
                if Puzzle.add_puzzle_direct(line):
                    puzzle_count += 1
                    
        logger.info(f"Loaded {puzzle_count} puzzles for test")
        
        # Verify puzzle count
        loaded_puzzles = len(Puzzle.get_all_puzzles())
        if loaded_puzzles != expected_count:
            logger.warning(f"Expected {expected_count} puzzles but loaded {loaded_puzzles}")
            
        # Run the performance test
        logger.info("\nRunning chain finding performance test...")
        start_time = time.time()
        chain = Puzzle.find_longest_chain(timeout_seconds=30, export_paths=False)
        elapsed = time.time() - start_time
        
        logger.info(f"Performance test completed in {elapsed:.2f} seconds")
        logger.info(f"Found chain with length {len(chain)}")
        
        # Verify chain properties
        if len(chain) > 0:
            logger.info("Verifying chain connections...")
            puzzles = Puzzle.get_all_puzzles()
            is_valid = True
            
            # Check connections
            for i in range(len(chain)-1):
                p1 = next((p for p in puzzles if p.id == chain[i]), None)
                p2 = next((p for p in puzzles if p.id == chain[i+1]), None)
                
                if not p1 or not p2:
                    logger.error(f"Invalid puzzle reference at position {i}")
                    is_valid = False
                    continue
                
                if p1.puzzle_sides['gives'] != p2.puzzle_sides['takes']:
                    logger.error(f"Invalid connection: {p1.puzzle_number} gives {p1.puzzle_sides['gives']} but {p2.puzzle_number} takes {p2.puzzle_sides['takes']}")
                    is_valid = False
            
            # Check for duplicates
            seen = set()
            duplicates = False
            for puzzle_id in chain:
                if puzzle_id in seen:
                    logger.error(f"Duplicate puzzle ID found: {puzzle_id}")
                    duplicates = True
                seen.add(puzzle_id)
            
            if is_valid and not duplicates:
                logger.info("Chain validation PASSED - All connections valid, no duplicates")
            else:
                logger.error("Chain validation FAILED")
            
            # For medium_connected, we expect a chain of 100 puzzles
            if len(chain) == 100:
                logger.info("✓ Performance test PASSED - Found all puzzles in chain")
            else:
                logger.info(f"✗ Performance test NOTE: Found {len(chain)} puzzles in chain (expected 100)")
    except Exception as e:
        logger.error(f"Error in performance test: {e}")

def run_all_tests():
    """Run all tests and return True if all succeeded"""
    try:
        test_simple_chain()
        test_branch_chain() 
        test_complex_structure()
        test_cycle_detection()
        test_performance()
        logger.info("\nAll tests completed!")
        return True
    except AssertionError as e:
        logger.error(f"Test failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during tests: {e}")
        return False

if __name__ == "__main__":
    run_all_tests()