# backend/create_datasets.py
import os
import random
import logging
import time
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Ensure data directory exists with pathlib for better path handling
script_dir = Path(__file__).resolve().parent
backend_dir = script_dir.parent
data_dir = backend_dir / "data"
os.makedirs(data_dir, exist_ok=True)
logger.info(f"Creating datasets in {data_dir}")

def create_random_dataset(size, filename, unique=True):
    """
    Create a dataset of random puzzles
    
    Args:
        size (int): Number of puzzles to create
        filename (str): Output filename
        unique (bool): Whether to ensure all puzzles are unique
    
    Returns:
        bool: Success status
    """
    try:
        puzzles = set() if unique else []
        
        # Cap size at a reasonable number
        if size > 10000:
            logger.warning(f"Dataset size {size} is too large, capping at 10000")
            size = 10000
            
        # Generate random puzzles
        start_time = time.time()
        attempts = 0
        max_attempts = size * 10  # Avoid infinite loops
        
        while (unique and len(puzzles) < size) or (not unique and len(puzzles) < size):
            takes = random.randint(1, 99)
            gives = random.randint(1, 99)
            middle = random.randint(1, 99)  # Randomize middle digits for variety
            
            # Format as 6 digits: takes(2) + middle(2) + gives(2)
            puzzle_number = f"{takes:02d}{middle:02d}{gives:02d}"
            
            if unique:
                puzzles.add(puzzle_number)
            else:
                puzzles.append(puzzle_number)
                
            attempts += 1
            if attempts >= max_attempts:
                logger.warning(f"Reached maximum attempts ({max_attempts}). Generated {len(puzzles)} unique puzzles.")
                break
        
        # Convert to list if set
        puzzles_list = list(puzzles) if unique else puzzles
        
        # Shuffle to ensure random order
        random.shuffle(puzzles_list)
        
        # Write to file with error handling
        file_path = data_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(puzzles_list))
        
        elapsed = time.time() - start_time
        logger.info(f"Created random dataset with {len(puzzles_list)} puzzles at {file_path} in {elapsed:.2f}s")
        
        return True
    except Exception as e:
        logger.error(f"Error creating random dataset {filename}: {e}")
        return False

def create_connected_dataset(size, filename, add_noise=False, noise_percent=10):
    """
    Create a dataset with guaranteed chain
    
    Args:
        size (int): Number of puzzles in the main chain
        filename (str): Output filename
        add_noise (bool): Whether to add additional non-chain puzzles
        noise_percent (int): Percentage of noise puzzles to add
    
    Returns:
        bool: Success status
    """
    try:
        puzzles = []
        
        # Cap size at a reasonable number
        if size > 10000:
            logger.warning(f"Chain size {size} is too large, capping at 10000")
            size = 10000
        
        # Create a guaranteed chain of values
        start_time = time.time()
        chain_values = [random.randint(1, 99)]
        
        # Generate chain values ensuring no loops (which would shorten the chain)
        used_values = set(chain_values)
        for _ in range(size):
            # Try to find an unused value to prevent loops
            attempts = 0
            next_val = random.randint(1, 99)
            while next_val in used_values and attempts < 100:
                next_val = random.randint(1, 99)
                attempts += 1
                
            # If we can't find unused value after many attempts,
            # just use a random one (but the chain might be shorter than expected)
            chain_values.append(next_val)
            used_values.add(next_val)
        
        # Create puzzles where each one's "gives" matches next one's "takes"
        for i in range(size):
            takes = chain_values[i]
            gives = chain_values[i+1]
            middle = random.randint(10, 99)
            
            # Format as 6 digits: takes(2) + middle(2) + gives(2)
            puzzle_num = f"{takes:02d}{middle:02d}{gives:02d}"
            puzzles.append(puzzle_num)
        
        # Add noise puzzles if requested (puzzles not in the main chain)
        if add_noise and noise_percent > 0:
            noise_count = int(size * noise_percent / 100)
            for _ in range(noise_count):
                takes = random.randint(1, 99)
                gives = random.randint(1, 99)
                middle = random.randint(10, 99)
                
                # Ensure this doesn't accidentally connect to our chain
                while any(gives == chain_values[i] for i in range(1, len(chain_values))):
                    gives = random.randint(1, 99)
                
                puzzle_num = f"{takes:02d}{middle:02d}{gives:02d}"
                puzzles.append(puzzle_num)
            
            # Shuffle to mix chain and noise puzzles
            random.shuffle(puzzles)
        
        # Write to file with error handling
        file_path = data_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(puzzles))
        
        elapsed = time.time() - start_time
        logger.info(f"Created connected dataset with {len(puzzles)} puzzles (chain length: {size}) at {file_path} in {elapsed:.2f}s")
        
        return True
    except Exception as e:
        logger.error(f"Error creating connected dataset {filename}: {e}")
        return False

def create_complex_dataset(size, filename, chain_count=3, min_chain_length=5):
    """
    Create dataset with multiple chains of different lengths
    
    Args:
        size (int): Total number of puzzles
        filename (str): Output filename
        chain_count (int): Number of different chains to create
        min_chain_length (int): Minimum length for each chain
        
    Returns:
        bool: Success status
    """
    try:
        puzzles = []
        start_time = time.time()
        
        # Determine chain sizes
        remaining_puzzles = size
        chain_sizes = []
        
        # Ensure minimum puzzles for each chain
        for i in range(chain_count):
            chain_sizes.append(min_chain_length)
            remaining_puzzles -= min_chain_length
        
        # Distribute remaining puzzles randomly among chains
        while remaining_puzzles > 0:
            chain_idx = random.randint(0, chain_count - 1)
            chain_sizes[chain_idx] += 1
            remaining_puzzles -= 1
        
        # Create each chain
        all_chain_values = []
        for i, chain_size in enumerate(chain_sizes):
            # Create a chain similar to create_connected_dataset
            chain_values = [random.randint(1, 99)]
            used_values = set(chain_values)
            
            for _ in range(chain_size):
                next_val = random.randint(1, 99)
                while next_val in used_values and len(used_values) < 99:
                    next_val = random.randint(1, 99)
                chain_values.append(next_val)
                used_values.add(next_val)
            
            # Create puzzles for this chain
            for j in range(chain_size):
                takes = chain_values[j]
                gives = chain_values[j+1]
                middle = random.randint(10, 99)
                puzzle_num = f"{takes:02d}{middle:02d}{gives:02d}"
                puzzles.append(puzzle_num)
            
            all_chain_values.append(chain_values)
            logger.debug(f"Chain {i+1}: length {chain_size}, first value: {chain_values[0]}, last value: {chain_values[-1]}")
        
        # Shuffle all puzzles
        random.shuffle(puzzles)
        
        # Write to file
        file_path = data_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(puzzles))
        
        elapsed = time.time() - start_time
        chain_info = ", ".join(f"Chain {i+1}: {len}" for i, len in enumerate(chain_sizes))
        logger.info(f"Created complex dataset with {len(puzzles)} total puzzles ({chain_info}) at {file_path} in {elapsed:.2f}s")
        
        return True
    except Exception as e:
        logger.error(f"Error creating complex dataset {filename}: {e}")
        return False

def create_cyclic_dataset(size, filename, cycle_length=3):
    """
    Create a dataset containing a chain with a cycle
    
    Args:
        size (int): Total number of puzzles
        filename (str): Output filename
        cycle_length (int): Length of the cycle within the chain
    
    Returns:
        bool: Success status
    """
    try:
        if cycle_length < 3:
            cycle_length = 3  # Minimum cycle size
            
        # Create linear part of the chain
        linear_length = max(size - cycle_length, 0)
        puzzles = []
        
        start_time = time.time()
        
        # Start values for chain (linear part + cycle)
        chain_values = [random.randint(1, 99)]
        used_values = set(chain_values)
        
        # Generate linear part
        for _ in range(linear_length):
            next_val = random.randint(1, 99)
            while next_val in used_values and len(used_values) < 99:
                next_val = random.randint(1, 99)
            chain_values.append(next_val)
            used_values.add(next_val)
        
        # Generate cycle part
        cycle_start_value = chain_values[-1]  # Last value of linear part
        cycle_values = [cycle_start_value]
        
        for _ in range(cycle_length - 1):
            next_val = random.randint(1, 99)
            while next_val in used_values and len(used_values) < 99:
                next_val = random.randint(1, 99)
            cycle_values.append(next_val)
            used_values.add(next_val)
        
        # Close the cycle by making last value point to first
        chain_values.extend(cycle_values[1:])  # Add all but first cycle value (already in chain)
        
        # Create puzzles for the entire chain
        for i in range(len(chain_values) - 1):
            takes = chain_values[i]
            gives = chain_values[i+1]
            middle = random.randint(10, 99)
            puzzle_num = f"{takes:02d}{middle:02d}{gives:02d}"
            puzzles.append(puzzle_num)
        
        # Create final puzzle that closes the cycle
        puzzle_num = f"{chain_values[-1]:02d}{random.randint(10, 99):02d}{cycle_start_value:02d}"
        puzzles.append(puzzle_num)
        
        # Shuffle puzzles
        random.shuffle(puzzles)
        
        # Write to file
        file_path = data_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(puzzles))
        
        elapsed = time.time() - start_time
        logger.info(f"Created cyclic dataset with {len(puzzles)} puzzles (linear: {linear_length}, cycle: {cycle_length}) at {file_path} in {elapsed:.2f}s")
        
        return True
    except Exception as e:
        logger.error(f"Error creating cyclic dataset {filename}: {e}")
        return False

def verify_datasets():
    """Verify that all created datasets exist and have content"""
    try:
        dataset_files = [
            "small_random.txt",
            "medium_random.txt",
            "small_connected.txt", 
            "medium_connected.txt",
            "large_connected.txt",
            "complex.txt",
            "cyclic.txt"
        ]
        
        all_valid = True
        for filename in dataset_files:
            file_path = data_dir / filename
            if not os.path.exists(file_path):
                logger.error(f"Missing dataset: {file_path}")
                all_valid = False
                continue
                
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                logger.error(f"Empty dataset: {file_path}")
                all_valid = False
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    valid_puzzles = [line.strip() for line in lines 
                                     if line.strip() and len(line.strip()) == 6 and line.strip().isdigit()]
                    
                    logger.info(f"Dataset {filename}: {len(valid_puzzles)} valid puzzles, size: {file_size} bytes")
            except Exception as e:
                logger.error(f"Error reading dataset {filename}: {e}")
                all_valid = False
        
        return all_valid
    except Exception as e:
        logger.error(f"Error verifying datasets: {e}")
        return False

# Create test datasets
logger.info("Creating test datasets...")
try:
    # Create various dataset types
    create_random_dataset(20, "small_random.txt")
    create_random_dataset(100, "medium_random.txt")
    create_connected_dataset(20, "small_connected.txt")
    create_connected_dataset(100, "medium_connected.txt")
    create_connected_dataset(500, "large_connected.txt", add_noise=True, noise_percent=5)
    create_complex_dataset(50, "complex.txt", chain_count=3)
    create_cyclic_dataset(20, "cyclic.txt", cycle_length=5)
    
    # Verify all datasets were created successfully
    if verify_datasets():
        logger.info("All datasets created and verified successfully!")
    else:
        logger.warning("Some datasets may not have been created correctly.")
        
except Exception as e:
    logger.error(f"Error creating datasets: {e}")

logger.info("Dataset creation script completed.")