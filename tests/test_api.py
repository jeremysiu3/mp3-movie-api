def test_upload_csv(client, sample_csv_bytes):
    response = client.post("/upload", files={"file": ("sample_movies.csv", sample_csv_bytes, "text/csv")})
    assert response.status_code == 200
    body = response.json()
    assert body["rows"] == 20
    assert body["columns"] == 4


def test_process_and_retrieve(
    client, uploaded_movies, processing_body
):
    response = client.post("/movies/process", json=processing_body)
    assert response.status_code == 200
    body = response.json()
    assert body["validation_rows_removed"] == 0
    assert body["cleaning_report"]["rows_before"] == 20
    assert body["cleaning_report"]["rows_after"] == 18

    response = client.get("/movies")
    assert response.status_code == 200
    body = response.json()
    assert body["total_rows"] == 18
    assert [row["title"] for row in body["data"]] == [f"Movie {c}" for c in "ABCDEFGHIJKLMNOPQR"]


def test_retrieve_empty_movies(client):
    response = client.get("/movies")
    assert response.status_code == 200
    assert response.json() == {"data": [], "total_rows": 0}
