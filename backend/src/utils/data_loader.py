import os
import sys
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Add the root directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
import config

def load_puzzle_data(filename="source.txt", relative_to_src=False):
    """Load puzzle data from the data directory
    
    Args:
        filename: Name of the file to load
        relative_to_src: If True, load from backend/src/data instead of backend/data
    """
    if relative_to_src:
        filepath = Path(__file__).parent.parent / "data" / filename
    else:
        filepath = config.DATA_DIR / filename
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read().splitlines()
    except FileNotFoundError:
        logger.error(f"Error: Could not find {filepath}")
        # Try alternate locations if primary location fails
        alt_paths = [
            Path(__file__).parent.parent / "data" / filename,  # backend/src/data
            Path("/app/data") / filename                       # Docker container path
        ]
        
        for alt_path in alt_paths:
            try:
                if alt_path.exists():
                    print(f"Found alternative at {alt_path}")
                    with open(alt_path, "r", encoding="utf-8") as f:
                        return f.read().splitlines()
            except Exception:
                pass
                
        return []
    except UnicodeDecodeError:
        print(f"Error: Encoding issue with {filepath}")
        return []
    except Exception as e:
        print(f"Error loading {filepath}: {str(e)}")
        return []