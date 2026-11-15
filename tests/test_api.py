import pytest

from src import MovieStorage
import main

def test_movies_persist(client, test_storage, uploaded_movies):
    reopened = MovieStorage(test_storage.db_path)
    df = reopened.get()
    assert len(df) == 20
    assert list(df.columns) == ["title", "release_year", "rating", "genre"]
    assert list(df["title"]) == [
        "Movie A", "Movie B", "Movie B", "Movie C", "Movie D",
        "Movie D", "Movie E", "Movie F", "Movie G", "Movie H",
        "Movie I", "Movie J", "Movie K", "Movie L", "Movie M",
        "Movie N", "Movie O", "Movie P", "Movie Q", "Movie R"
    ]

    stored_ids = [row["id"] for row in reopened.select_columns(["title"], 100)]
    response = client.get("/movies", params={"limit": 100})
    assert response.status_code == 200
    api_ids = [row["id"] for row in response.json()["data"]]
    assert stored_ids == list(range(1, 21))
    assert api_ids == list(range(1, 21))


def test_cache_and_processing(client, uploaded_movies, processing_body):
    first = client.get("/movies", params={"limit": 100})
    assert first.status_code == 200
    assert main.cache.get(100) == first.json()

    second = client.get("/movies", params={"limit": 1})
    assert second.status_code == 200
    assert main.cache.get(1) == second.json()

    repeat = client.get("/movies", params={"limit": 100})
    assert repeat.status_code == 200
    assert repeat.json() == first.json()

    response = client.post("/movies/process", json=processing_body)
    assert response.status_code == 200
    body = response.json()
    assert body["validation_rows_removed"] == 0
    assert body["cleaning_report"]["rows_before"] == 20
    assert body["cleaning_report"]["rows_after"] == 16
    assert body["cleaning_report"]["rows_removed"] == 4
    assert main.cache.get(100) is None
    assert main.cache.get(1) is None

    response = client.get("/movies", params={"limit": 100})
    assert response.status_code == 200
    body = response.json()
    assert body["total_rows"] == 16
    assert [row["title"] for row in body["data"]] == [f"Movie {c}" for c in "ABCDEFGHIJKLMNOP"]
    assert [row["id"] for row in body["data"]] == list(range(1, 17))
    assert main.cache.get(100) == body


def test_cache_hit_skips_database(client, uploaded_movies, monkeypatch):
    first = client.get("/movies", params={"limit": 100})
    assert first.status_code == 200

    def fail_if_called(*args, **kwargs):
        pytest.fail("A cache hit should not query the database")

    monkeypatch.setattr(main.storage, "select_columns", fail_if_called)
    monkeypatch.setattr(main.storage, "count_movies", fail_if_called)

    second = client.get("/movies", params={"limit": 100})
    assert second.status_code == 200
    assert first.json() == second.json()
