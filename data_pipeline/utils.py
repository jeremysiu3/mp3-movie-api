import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def setup_logging(verbose=False):
    """Configure logging for the pipeline."""
    if verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)-8s %(name)s — %(message)s", datefmt="%H:%M:%S")
    else:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-8s %(name)s — %(message)s", datefmt="%H:%M:%S")

def validate_input(filepath):
    """Check whether the input path exists and is a file."""
    if Path(filepath).is_file():
        logger.info("Input file validated: " + filepath)
        return True
    else:
        logger.error("Input file not found: " + filepath)
        return False