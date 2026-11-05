from pathlib import Path

import logging
import pandas as pd
import json
import yaml

logger = logging.getLogger(__name__)


def setup_logging(verbose=False):
    """Configure logging for data loader."""
    if verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)-8s %(message)s", datefmt="%H:%M:%S")
    else:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-8s %(message)s", datefmt="%H:%M:%S")

def load_csv(filepath):
    """Load a CSV file into a DataFrame.
    filepath is a Path object.
    """
    df = pd.read_csv(filepath)
    logger.info(f"Loaded CSV file: {filepath} ({len(df)} rows)")
    return df


def load_json(filepath):
    """Load a JSON file into a Python object (dict or list).
    filepath is a Path object.
    """
    with open(filepath, "r") as f:
        data = json.load(f)
    logger.info(f"Loaded JSON file: {filepath}")
    return data


def load_yaml(filepath):
    """Load a YAML file into a Python object.
    filepath is a Path object.
    """
    with open(filepath, "r") as f:
        config = yaml.safe_load(f)
    logger.info(f"Loaded YAML file: {filepath}")
    return config


def load_data(filepath):
    """Load a file based on its extension.
    filepath is a string, such as 'fixtures/sample.csv'
    """
    file_path = Path(filepath)
    if file_path.suffix == ".csv":
        return load_csv(file_path)
    elif file_path.suffix == ".json":
        return load_json(file_path)
    elif file_path.suffix == ".yaml":
        return load_yaml(file_path)
    else:
        logger.error(f"Unsupported file format: {file_path.suffix}")
        raise ValueError(f"Unsupported file format: {file_path.suffix}")
