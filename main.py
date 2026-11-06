import io
import logging
from pathlib import Path
import pandas as pd
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from src import HealthResponse, setup_logging, ProcessConfig, log_requests, MovieStorage, MovieUploadInfo, MovieDataResponse, MovieProcessingReport
from data_pipeline import create_cleaning_report, process_data, validate_dataframe
from src.storage import MOVIE_COLUMNS

setup_logging(verbose=True)
logger = logging.getLogger(__name__)

app = FastAPI(title="Data Processing API", version="1.0.0")
app.middleware("http")(log_requests)
storage = MovieStorage()

@app.get("/health", response_model=HealthResponse)
def health_check():
    """Return the application status and version."""
    return {"status": "ok", "version": "1.0.0"}

@app.post("/upload", response_model=MovieUploadInfo)
async def upload_movies(file: UploadFile = File(...)):
    """Read a CSV upload and replace the stored movie collection."""
    suffix = Path(file.filename).suffix.lower()
    if suffix != ".csv":
        logger.warning(f"Unsupported file format: {suffix}")
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    contents = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(contents))
    except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError) as error:
        logger.warning(f"Cannot read CSV: {error}")
        raise HTTPException(status_code=400, detail="Cannot read the uploaded CSV.")

    if sorted(df.columns) != sorted(MOVIE_COLUMNS):
        logger.warning(f"Unexpected columns: {list(df.columns)}")
        raise HTTPException(status_code=400, detail=f"CSV columns must be exactly: {MOVIE_COLUMNS}")
    if df.empty:
        logger.warning("Uploaded CSV has no data rows")
        raise HTTPException(status_code=400, detail="CSV must contain at least one data row.")
    df = df[MOVIE_COLUMNS]

    storage.save(df)
    logger.info(f"Uploaded movies: filename={file.filename}, rows={len(df)}")
    return {
        "filename": file.filename,
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": list(df.columns),
    }

@app.get("/movies", response_model=MovieDataResponse)
def get_movies(limit: int = Query(default=100, ge=1)):
    """Return up to limit stored movies."""
    records = storage.select_columns(MOVIE_COLUMNS, limit)
    total = storage.count_movies()
    logger.info(f"Retrieved movies: returned_rows={len(records)}, total_rows={total}")
    return {"data": records, "total_rows": total}

@app.get("/movies/search", response_model=list[dict])
def query_movies(
    columns: list[str] = Query(default=["title"]),
    min_rating: float = Query(default=0, ge=0, le=10),
    limit: int = Query(default=100, ge=1)
):
    """Return selected fields from movies with rating >= min_rating."""
    try:
        records = storage.query_movies(columns, min_rating, limit)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    logger.info(f"Queried movies: columns={columns}, min_rating={min_rating}, returned_rows={len(records)}")
    return records

@app.post("/movies/process", response_model=MovieProcessingReport)
def process_movies(config: ProcessConfig):
    """Validate and process the stored movies using MP1 functions."""
    df = storage.get()
    if df.empty:
        logger.warning("No movies stored")
        raise HTTPException(status_code=400, detail="No movies stored. Upload a CSV first.")

    config_dict = config.model_dump()
    validation = config_dict["validation"]

    try:
        for col in validation["numeric_columns"]:
            if col not in df.columns:
                raise ValueError(f"Missing numeric column: {col}")

        validated = validate_dataframe(df, validation["required_columns"], validation["numeric_columns"])
        validation_removed = len(df) - len(validated)
        validated = validated.copy()
        processed = process_data(validated, config_dict)
    except ValueError as error:
        logger.warning(f"Processing failed: error={error}")
        raise HTTPException(status_code=400, detail=str(error))

    report = create_cleaning_report(validated, processed)
    storage.save(processed)
    logger.info(f"Processed movies: validation_removed={validation_removed}, " f"rows_before={report['rows_before']}, rows_after={report['rows_after']}")
    return {
        "validation_rows_removed": validation_removed,
        "cleaning_report": report
    }