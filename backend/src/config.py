import os
from pathlib import Path

# Detect environment
IN_DOCKER = os.environ.get('IN_DOCKER', '').lower() == 'true' or os.path.exists('/.dockerenv')

# Base paths
if IN_DOCKER:
    BASE_DIR = Path('/app')
    DATA_DIR = Path('/app/data')
    EXPORT_DIR = Path('/app/exports')
    LOGS_DIR = Path('/app/logs')
    STATIC_DIR = Path('/app/static')
else:
    SCRIPT_DIR = Path(__file__).resolve().parent
    BASE_DIR = SCRIPT_DIR.parent.parent
    DATA_DIR = BASE_DIR / 'backend' / 'data'
    EXPORT_DIR = BASE_DIR / 'backend' / 'exports'
    LOGS_DIR = BASE_DIR / 'backend' / 'logs'
    STATIC_DIR = BASE_DIR / 'frontend'

# Create directories
os.makedirs(EXPORT_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# Dataset paths
SOURCE_PATH = DATA_DIR / 'source.txt'
DATASET_PATHS = {
    "default": SOURCE_PATH,
    "small_random": DATA_DIR / "small_random.txt",
    "medium_random": DATA_DIR / "medium_random.txt",
    "small_connected": DATA_DIR / "small_connected.txt",
    "medium_connected": DATA_DIR / "medium_connected.txt",
    "large_connected": DATA_DIR / "large_connected.txt", 
    "complex": DATA_DIR / "complex.txt",
    "cyclic": DATA_DIR / "cyclic.txt"
}

# Application settings
TIMEOUT = int(os.environ.get('TIMEOUT', 3600))
PORT = int(os.environ.get('PORT', 5000))
DEBUG = os.environ.get('FLASK_DEBUG', '').lower() == 'true'
STATIC_FOLDER = os.environ.get('STATIC_FOLDER', 'static')

# Print configuration when module is imported
print(f"Loading config - Environment: {'Docker' if IN_DOCKER else 'Local'}")
print(f"Base directory: {BASE_DIR}")
print(f"Data directory: {DATA_DIR}")
print(f"Source path: {SOURCE_PATH}")
print(f"Source exists: {os.path.exists(SOURCE_PATH)}")