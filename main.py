import io
import json
import logging
from pathlib import Path
import pandas as pd
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from src import DatasetInfo, DatasetStorage, HealthResponse, setup_logging, ProcessConfig, ProcessingReport, log_requests
from data_pipeline import create_cleaning_report, process_data, validate_dataframe

setup_logging(verbose=True)
logger = logging.getLogger(__name__)

app = FastAPI(title="Data Processing API", version="1.0.0")
app.middleware("http")(log_requests)
storage = DatasetStorage()

@app.get("/health", response_model=HealthResponse)
def health_check():
    """Return the application status and version."""
    return {"status": "ok", "version": "1.0.0"}

@app.post("/upload", response_model=DatasetInfo)
async def upload_dataset(file: UploadFile = File(...)):
    """Read and store a CSV upload."""
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

    dataset_id = storage.save(df, file.filename)
    logger.info(f"Uploaded dataset: id={dataset_id}, filename={file.filename}, rows={len(df)}")
    return storage.get_metadata(dataset_id)

@app.get("/datasets/{dataset_id}")
def get_dataset(dataset_id: int, limit: int = Query(default=100, ge=1)):
    """Return up to limit rows from a stored dataset."""
    df = storage.get(dataset_id)
    if df is None:
        logger.warning(f"Dataset not found: id={dataset_id}")
        raise HTTPException(status_code=404, detail="Dataset not found.")

    records = json.loads(df.head(limit).to_json(orient="records"))
    logger.info(f"Retrieved dataset: id={dataset_id}, returned_rows={len(records)}")
    return {"id": dataset_id, "data": records, "total_rows": len(df)}

@app.post(
    "/datasets/{dataset_id}/process",
    response_model=ProcessingReport
)
def process_dataset(dataset_id: int, config: ProcessConfig):
    """Validate and process a stored dataset using MP1 functions."""
    df = storage.get(dataset_id)
    if df is None:
        logger.warning(f"Dataset not found: id={dataset_id}")
        raise HTTPException(status_code=404, detail="Dataset not found.")

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
        logger.warning(f"Processing failed: id={dataset_id}, error={error}")
        raise HTTPException(status_code=400, detail=str(error))

    report = create_cleaning_report(validated, processed)
    storage.update(dataset_id, processed)
    logger.info(f"Processed dataset: id={dataset_id}, validation_removed={validation_removed}, " f"rows_before={report['rows_before']}, rows_after={report['rows_after']}")
    return {
        "id": dataset_id,
        "validation_rows_removed": validation_removed,
        "cleaning_report": report
    }

