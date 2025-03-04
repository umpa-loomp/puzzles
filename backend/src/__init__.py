import sys
from pathlib import Path
from importlib import util

# Get root config
config_path = Path(__file__).parent.parent / "config.py"
spec = util.spec_from_file_location("config", config_path)
config = util.module_from_spec(spec)
spec.loader.exec_module(config)

# Export config variables
__all__ = [name for name in dir(config) if not name.startswith('_')]
globals().update({name: getattr(config, name) for name in __all__})