import os
from pathlib import Path

# Determine if we're running in Docker
IN_DOCKER = os.environ.get('IN_DOCKER', 'false').lower() == 'true'

# Base paths
if IN_DOCKER:
    BASE_DIR = Path('/app')
    DATA_DIR = Path('/app/data')
    EXPORT_DIR = Path('/app/exports')
    LOG_DIR = Path('/app/logs')
else:
    # When running locally, use relative paths from the root directory
    BASE_DIR = Path(__file__).absolute().parent
    DATA_DIR = BASE_DIR / 'backend' / 'data'
    EXPORT_DIR = BASE_DIR / 'backend' / 'exports'
    LOG_DIR = BASE_DIR / 'backend' / 'logs'

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
EXPORT_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

# Common data files
SOURCE_FILE = DATA_DIR / 'source.txt'