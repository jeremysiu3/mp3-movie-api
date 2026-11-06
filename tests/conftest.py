from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from main import app, storage
from src.storage import MOVIE_COLUMNS


@pytest.fixture
def client():
    storage.save(pd.DataFrame(columns=MOVIE_COLUMNS))
    with TestClient(app) as test_client:
        yield test_client
    storage.save(pd.DataFrame(columns=MOVIE_COLUMNS))


@pytest.fixture
def sample_csv_bytes():
    filepath = Path("fixtures") / "sample_movies.csv"
    return filepath.read_bytes()


@pytest.fixture
def uploaded_movies(client, sample_csv_bytes):
    response = client.post(
        "/upload",
        files={
            "file": (
                "sample_movies.csv",
                sample_csv_bytes,
                "text/csv"
            )
        }
    )
    assert response.status_code == 200
    return response.json()


@pytest.fixture
def processing_body():
    return {
        "validation": {
            "required_columns": ["title", "rating"],
            "numeric_columns": ["rating"]
        },
        "processing": {
            "remove_duplicates": True,
            "missing": {
                "enabled": True,
                "axis": "rows"
            },
            "outliers": {
                "enabled": False,
                "columns": [],
                "method": "iqr",
                "threshold": 1.5
            }
        }
    }
