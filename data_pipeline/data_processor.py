import logging
import pandas as pd

logger = logging.getLogger(__name__)

def remove_duplicates(df):
    """Remove duplicate rows."""
    before = len(df)
    df = df.drop_duplicates()
    logger.debug(f"remove_duplicates: {before} -> {len(df)} rows")
    return df


def handle_missing(df, axis="rows"):
    """Drop rows or columns containing missing values."""
    if axis == "rows":
        cleaned = df.dropna()
        logger.debug(f"handle_missing: {len(df)} -> {len(cleaned)} rows")
        return cleaned
    elif axis == "columns":
        cleaned = df.dropna(axis=1)
        logger.debug(f"handle_missing: {len(df.columns)} -> {len(cleaned.columns)} columns")
        return cleaned
    else:
        logger.error("Error: Invalid axis value. Must be 'rows' or 'columns'.")
        raise ValueError("Invalid axis value. Must be 'rows' or 'columns'.")
    return df

def remove_outliers(df, columns, method, threshold):
    """Remove outliers from the specified numeric columns."""
    if method not in ["iqr", "zscore"]:
        logger.error(f"Unsupported outlier method: {method}")
        raise ValueError(f"Unsupported outlier method: {method}")

    for col in columns:
        if col not in df.columns:
            logger.warning(f"Column not found: {col}")
            continue
        if df[col].dtype.kind not in 'iuf':
            logger.warning(f"Column {col} is not numeric.")
            continue
        before = len(df)
        if method == "iqr":
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            lower = q1 - threshold * iqr
            upper = q3 + threshold * iqr
            df = df[(df[col] >= lower) & (df[col] <= upper)]
            logger.debug(f"{col}: method={method}, threshold={threshold}, removed={before - len(df)}")
        elif method == "zscore":
            mean = df[col].mean()
            std = df[col].std()
            z_scores = (df[col] - mean) / std
            df = df[z_scores.abs() <= threshold]
            logger.debug(f"{col}: method={method}, threshold={threshold}, removed={before - len(df)}")

    return df
    

def process_data(df, config):
    """Apply the processing steps enabled in the configuration."""
    settings = config["processing"]

    if settings["remove_duplicates"]:
        df = remove_duplicates(df)

    if settings["missing"]["enabled"]:
        df = handle_missing(df, settings["missing"]["axis"])

    if settings["outliers"]["enabled"]:
        outliers = settings["outliers"]
        df = remove_outliers(df, outliers["columns"], outliers["method"], outliers["threshold"])

    return df


def create_cleaning_report(df_before, df_after):
    """Return a dictionary summarizing the cleaning results."""
    return {
        "rows_before": len(df_before),
        "rows_after": len(df_after),
        "rows_removed": len(df_before) - len(df_after),
        "columns_before": len(df_before.columns),
        "columns_after": len(df_after.columns),
        "columns_removed": len(df_before.columns) - len(df_after.columns)
    }
