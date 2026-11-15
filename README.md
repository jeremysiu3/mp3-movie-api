# MP 3: Persistent Storage and Caching

## Description
This FastAPI application stores, cleans, and retrieves a collection of movies that a client uploads as a CSV file. main.py holds the endpoints, and it uses the modules under src/ along with the data_pipeline that I created in MP1 to do the work. storage.py and database.py are the modules that save the movies to SQLite and read them back, and models.py defines the request and response models. When a CSV is uploaded, the app checks that it has the four movie columns and saves the rows to SQLite, replacing the previous collection. GET /movies checks the cache first, which is the MovieCache in cache.py that uses fakeredis, so a cache hit returns the saved response and a cache miss reads SQLite and caches the result for 90 seconds. POST /movies/process validates and cleans the stored movies using the data_pipeline and saves the cleaned movies back to SQLite. After every successful upload or processing save, the cache is cleared so the next retrieval reads the updated movies instead of the old ones.

## Run the API
```bash
python -m uvicorn main:app --reload
```
Open `http://127.0.0.1:8000/docs` to try the endpoints.

## Run the tests
```bash
python -m pytest tests -v
```

## Sample request and result
First upload `fixtures/sample_movies.csv` with `POST /upload`, then send this to `POST /movies/process`:

```json
{
  "validation": {
    "required_columns": ["title", "release_year", "rating", "genre"],
    "numeric_columns": ["release_year", "rating"]
  },
  "processing": {
    "remove_duplicates": true,
    "missing": {"enabled": true, "axis": "rows"},
    "outliers": {
      "enabled": true,
      "columns": ["rating"],
      "method": "iqr",
      "threshold": 1.5
    }
  }
}
```

Expected response for the 20-row sample:

```json
{
  "validation_rows_removed": 0,
  "cleaning_report": {
    "rows_before": 20,
    "rows_after": 16,
    "rows_removed": 4,
    "columns_before": 4,
    "columns_after": 4,
    "columns_removed": 0
  }
}
```