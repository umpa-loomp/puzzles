# backend/src/main.py
import os
from flask import Flask, jsonify, request, send_from_directory, Response
from flask_cors import CORS
import config  # Import the config module
from puzzle import Puzzle
import logging
import time
import traceback
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO if not config.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(config.LOGS_DIR, "app.log"))
    ]
)
logger = logging.getLogger(__name__)

# Use the data paths from config
logger.info("Available datasets:")
for key, path in config.DATASET_PATHS.items():
    logger.info(f"  {key}: {path} (exists: {os.path.exists(path)})")

# Create Flask app
app = Flask(__name__, static_folder=config.STATIC_FOLDER)
CORS(app)  # Enable CORS for all routes

def load_puzzles_from_file(file_path, force_reset=True):
    """Load puzzles from file with proper error handling"""
    try:
        logger.info(f"Loading puzzles from {file_path}")
        
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return 0
            
        if force_reset:
            Puzzle.reset()
            
        puzzle_count = 0
        skipped_count = 0
        
        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if not line or len(line) != 6:
                    skipped_count += 1
                    continue
                    
                try:
                    Puzzle.add_puzzle_direct(line)
                    puzzle_count += 1
                except ValueError as e:
                    logger.warning(f"Skipping invalid puzzle {line}: {e}")
                    skipped_count += 1
                    
        logger.info(f"Loaded {puzzle_count} puzzles, skipped {skipped_count} invalid entries")
        return puzzle_count
        
    except UnicodeDecodeError:
        logger.error(f"File encoding error: {file_path}")
        return 0
    except Exception as e:
        logger.error(f"Error loading puzzles: {e}")
        return 0

# Load default dataset on startup if exists
if os.path.exists(config.DATASET_PATHS["default"]):
    load_puzzles_from_file(config.DATASET_PATHS["default"])
else:
    logger.warning(f"Default dataset not found at {config.DATASET_PATHS['default']}")

@app.before_request
def ensure_puzzles_exist():
    """Ensure at least one test puzzle exists if none are loaded"""
    if not Puzzle.get_all_puzzles():
        logger.warning("No puzzles loaded. Adding a test puzzle.")
        Puzzle.add_puzzle_direct("123456")

@app.route('/api/datasets', methods=['GET'])
def get_datasets():
    """Return information about available datasets"""
    try:
        results = {}
        for name, path in config.DATASET_PATHS.items():
            exists = os.path.exists(path)
            size = os.path.getsize(path) if exists else 0
            puzzle_count = 0
            
            if exists:
                with open(path, 'r', encoding='utf-8-sig') as f:
                    puzzle_count = sum(1 for line in f if line.strip() and len(line.strip()) == 6 and line.strip().isdigit())
            
            results[name] = {
                "path": path,
                "exists": exists,
                "size_bytes": size,
                "puzzle_count": puzzle_count
            }
        
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error getting dataset info: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/api/puzzles', methods=['GET'])
def get_puzzles():
    """Get all puzzles or load a specific dataset"""
    logger.info("API endpoint /api/puzzles hit!")
    dataset = request.args.get('dataset', default='default')
    
    if dataset not in config.DATASET_PATHS:
        logger.error(f"Invalid dataset requested: {dataset}")
        return jsonify({
            "error": f"Invalid dataset: {dataset}",
            "available_datasets": list(config.DATASET_PATHS.keys())
        }), 400
    
    logger.info(f"Request for dataset: {dataset}")
    
    try:
        # Switch to requested dataset
        if (dataset in config.DATASET_PATHS):
            file_path = config.DATASET_PATHS[dataset]
            
            if os.path.exists(file_path):
                # Reset is now handled within load_puzzles_from_file
                puzzle_count = load_puzzles_from_file(file_path)
                if puzzle_count == 0:
                    logger.error(f"Failed to load dataset: {dataset}")
                    return jsonify({"error": f"Failed to load dataset: {dataset}"}), 500
                logger.info(f"Loaded {puzzle_count} puzzles from dataset: {dataset}")
            else:
                logger.error(f"Dataset file not found: {file_path}")
                return jsonify({"error": f"Dataset file not found: {file_path}"}), 404
                
        # Return all puzzles
        puzzles = Puzzle.get_all_puzzles()
        result = [p.get_puzzle_info() for p in puzzles]
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in get_puzzles: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/api/puzzles/longest_chain', methods=['GET'])
def get_longest_chain():
    """Find and return the longest chain of puzzles"""
    try:
        # Set timeout from request parameter or default
        timeout = int(request.args.get('timeout', default=60))
        if timeout <= 0 or timeout > 600:  # Cap at 10 minutes
            timeout = 60
            logger.warning(f"Invalid timeout value, using default: {timeout}")
        
        logger.info(f"Finding longest chain with {timeout} second timeout")
        
        # Find the longest chain
        start_time = time.time()
        chain_ids = Puzzle.find_longest_chain(timeout_seconds=timeout)
        elapsed = time.time() - start_time
        
        logger.info(f"Found chain of length {len(chain_ids)} in {elapsed:.2f} seconds")
        
        # Convert chain IDs to puzzle objects
        puzzles = Puzzle.get_all_puzzles()
        
        try:
            chain = []
            for id in chain_ids:
                matching_puzzle = next((p.get_puzzle_info() for p in puzzles if p.id == id), None)
                if matching_puzzle:
                    chain.append(matching_puzzle)
                else:
                    logger.error(f"Puzzle with ID {id} not found in puzzle collection")
        except Exception as e:
            logger.error(f"Error processing chain data: {e}")
            return jsonify({"error": f"Error processing chain data: {e}"}), 500
        
        # Log detailed chain info for debugging
        try:
            Puzzle.debug_chain(chain_ids)
        except Exception as e:
            logger.error(f"Error in debug_chain: {e}")
            # Continue despite error in debug function
        
        return jsonify({
            "chain": chain,
            "chain_length": len(chain),
            "processing_time_seconds": elapsed,
            "timeout_seconds": timeout
        })
    except ValueError as e:
        logger.error(f"Invalid parameter: {str(e)}")
        return jsonify({"error": f"Invalid parameter: {str(e)}"}), 400
    except Exception as e:
        logger.error(f"Error finding longest chain: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/api/puzzles/export/chain.txt')
def export_chain_txt():
    """Export the current chain as plaintext"""
    try:
        # Get the latest chain data
        chain_ids = Puzzle.find_longest_chain(timeout_seconds=int(request.args.get('timeout', 60)))
        puzzles = Puzzle.get_all_puzzles()
        
        if not chain_ids:
            return "No chain found", 404
            
        # Generate plain text content
        content = []
        content.append(f"Puzzle Chain Export")
        content.append(f"=================")
        content.append(f"")
        content.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        content.append(f"Chain Length: {len(chain_ids)} puzzles")
        content.append(f"")
        content.append(f"Chain:")
        content.append(f"")
        
        # Add each puzzle
        for i, puzzle_id in enumerate(chain_ids):
            puzzle = next((p for p in puzzles if p.id == puzzle_id), None)
            if puzzle:
                content.append(f"{i+1}. Puzzle #{puzzle.puzzle_number} - Takes: {puzzle.puzzle_sides['takes']}, Gives: {puzzle.puzzle_sides['gives']}")
                
                # Add connection for all but first
                if i > 0:
                    prev_puzzle = next((p for p in puzzles if p.id == chain_ids[i-1]), None)
                    if prev_puzzle:
                        content.append(f"   Connection: {prev_puzzle.puzzle_sides['gives']} → {puzzle.puzzle_sides['takes']}")
            
        # Generate response
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"puzzle-chain-{timestamp}.txt"
        
        return Response(
            "\n".join(content),
            mimetype="text/plain",
            headers={"Content-Disposition": f"attachment;filename={filename}"}
        )
    except Exception as e:
        logger.error(f"Error exporting chain as text: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/puzzles/export/chain.json')
def export_chain_json():
    """Export the current chain as JSON with metadata"""
    try:
        # Get the latest chain data with timeout validation
        timeout = min(max(int(request.args.get('timeout', 60)), 1), 600)
        start_time = time.time()
        chain_ids = Puzzle.find_longest_chain(timeout_seconds=timeout)
        if not chain_ids:
            logger.warning("No chain found or chain computation timed out")
            return jsonify({"error": "No valid chain found"}), 404
        processing_time = time.time() - start_time
        puzzles = Puzzle.get_all_puzzles()
        
        if not chain_ids:
            return jsonify({"error": "No chain found"}), 404
            
        # Generate JSON content
        result = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "processing_time_seconds": round(processing_time, 2),
                "puzzle_count": len(puzzles),
                "chain_length": len(chain_ids)
            },
            "chain": []
        }
        
        # Add each puzzle
        for i, puzzle_id in enumerate(chain_ids):
            puzzle = next((p for p in puzzles if p.id == puzzle_id), None)
            if puzzle:
                puzzle_data = {
                    "position": i + 1,
                    "id": puzzle.id,
                    "puzzle_number": puzzle.puzzle_number,
                    "takes": puzzle.puzzle_sides["takes"],
                    "gives": puzzle.puzzle_sides["gives"]
                }
                
                # Add connection info
                if i > 0:
                    prev_puzzle = next((p for p in puzzles if p.id == chain_ids[i-1]), None)
                    if prev_puzzle:
                        puzzle_data["connection"] = {
                            "from_puzzle": prev_puzzle.puzzle_number,
                            "gives": prev_puzzle.puzzle_sides["gives"],
                            "takes": puzzle.puzzle_sides["takes"],
                            "is_valid": prev_puzzle.puzzle_sides["gives"] == puzzle.puzzle_sides["takes"]
                        }
                        
                result["chain"].append(puzzle_data)
        
        # Generate response
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"puzzle-chain-{timestamp}.json"
        
        return Response(
            json.dumps(result, indent=2),
            mimetype="application/json",
            headers={"Content-Disposition": f"attachment;filename={filename}"}
        )
    except Exception as e:
        logger.error(f"Error exporting chain as JSON: {e}")
        return jsonify({"error": str(e)}), 500

# Add security headers
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {str(e)}")
    return jsonify({"error": "Internal server error"}), 500

@app.route('/health')
def health_check():
    """Health check endpoint for Docker"""
    return jsonify({
        "status": "healthy",
        "time": time.time(),
        "puzzle_count": len(Puzzle.get_all_puzzles())
    })

@app.route('/')
def index():
    static_folder = os.environ.get('STATIC_FOLDER', 'static')
    if not os.path.exists(os.path.join(static_folder, 'index.html')):
        logger.warning(f"Static file not found: {os.path.join(static_folder, 'index.html')}")
        return jsonify({"status": "API running", "error": "Frontend not available"}), 200
    return send_from_directory(static_folder, 'index.html')

@app.route('/<path:path>')
def static_files(path):
    static_folder = os.environ.get('STATIC_FOLDER', 'static')
    if not os.path.exists(os.path.join(static_folder, path)):
        logger.warning(f"Static file not found: {os.path.join(static_folder, path)}")
        return jsonify({"error": "File not found"}), 404
    return send_from_directory(static_folder, path)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    host = '0.0.0.0' if os.environ.get('IN_DOCKER') else 'localhost'
    
    logger.info(f"Starting Flask application on {host}:{port} (debug={debug})")
    app.run(host=host, port=port, debug=debug)