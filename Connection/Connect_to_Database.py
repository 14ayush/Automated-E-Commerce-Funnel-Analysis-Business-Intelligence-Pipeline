
import os
import logging
from pathlib import Path
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# ==========================================================
# PROJECT ROOT
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Example:
# scripts/push_to_supabase.py
#             ↑
# parent = scripts
# parent.parent = project root

# ==========================================================
# FOLDER PATHS
# ==========================================================

CLEANED_DATA_PATH = PROJECT_ROOT / "Data" / "CleanedData"

CONNECTION_PATH = PROJECT_ROOT / "Connection"

LOG_PATH = CONNECTION_PATH / "logs"

METADATA_PATH = CONNECTION_PATH / "metadata"

# ==========================================================
# CREATE FOLDERS
# ==========================================================

LOG_PATH.mkdir(parents=True, exist_ok=True)

METADATA_PATH.mkdir(parents=True, exist_ok=True)

# ==========================================================
# ENVIRONMENT VARIABLES
# ==========================================================

load_dotenv(PROJECT_ROOT / ".env")

HOST = os.getenv("SUPABASE_HOST")
PORT = os.getenv("SUPABASE_PORT")
DATABASE = os.getenv("SUPABASE_DATABASE")
USER = os.getenv("SUPABASE_USER")
PASSWORD = os.getenv("SUPABASE_PASSWORD")

# ==========================================================
# DATABASE CONNECTION
# ==========================================================

DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{USER}:{PASSWORD}@"
    f"{HOST}:{PORT}/{DATABASE}"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

# ==========================================================
# LOGGING CONFIGURATION
# ==========================================================

LOG_FILE = LOG_PATH / "database_load.log"

ERROR_FILE = LOG_PATH / "error.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

error_logger = logging.getLogger("error_logger")

error_handler = logging.FileHandler(ERROR_FILE)

error_logger.addHandler(error_handler)

error_logger.setLevel(logging.ERROR)

# ==========================================================
# METADATA FILES
# ==========================================================

BATCH_METADATA_FILE = (
    METADATA_PATH / "batch_metadata.csv"
)

PIPELINE_STATUS_FILE = (
    METADATA_PATH / "pipeline_status.csv"
)

# ==========================================================
# TABLE MAPPING
# ==========================================================

TABLE_MAPPING = {
    "users": "users_raw",
    "sessions": "sessions_raw",
    "events": "events_raw",
    "orders": "orders_raw",
    "products": "products_raw"
}

# ==========================================================
# METADATA WRITER
# ==========================================================

def write_batch_metadata(
    batch_id,
    table_name,
    file_name,
    rows_in_file,
    rows_loaded,
    status,
    message=""
):

    metadata = pd.DataFrame([{
        "batch_id": batch_id,
        "table_name": table_name,
        "file_name": file_name,
        "rows_in_file": rows_in_file,
        "rows_loaded": rows_loaded,
        "status": status,
        "message": message,
        "timestamp": datetime.now()
    }])

    if BATCH_METADATA_FILE.exists():

        metadata.to_csv(
            BATCH_METADATA_FILE,
            mode="a",
            header=False,
            index=False
        )

    else:

        metadata.to_csv(
            BATCH_METADATA_FILE,
            index=False
        )

# ==========================================================
# PIPELINE STATUS WRITER
# ==========================================================

def write_pipeline_status(
    batch_id,
    status,
    message=""
):

    status_df = pd.DataFrame([{
        "batch_id": batch_id,
        "status": status,
        "message": message,
        "timestamp": datetime.now()
    }])

    if PIPELINE_STATUS_FILE.exists():

        status_df.to_csv(
            PIPELINE_STATUS_FILE,
            mode="a",
            header=False,
            index=False
        )

    else:

        status_df.to_csv(
            PIPELINE_STATUS_FILE,
            index=False
        )

# ==========================================================
# CHECK IF BATCH ALREADY EXISTS
# ==========================================================

def batch_exists(
    table_name,
    batch_id
):

    query = text(f"""
        SELECT COUNT(*)
        FROM {table_name}
        WHERE batch_id = :batch_id
    """)

    with engine.connect() as conn:

        count = conn.execute(
            query,
            {"batch_id": batch_id}
        ).scalar()

    return count > 0

# ==========================================================
# LOAD SINGLE TABLE
# ==========================================================

def load_table(
    folder_name,
    table_name
):

    folder_path = (
        CLEANED_DATA_PATH /
        folder_name
    )

    csv_files = sorted(
        folder_path.glob("*.csv")
    )

    if not csv_files:

        logging.warning(
            f"No files found in {folder_name}"
        )

        return

    latest_file = csv_files[-1]

    print(
        f"Processing : {latest_file.name}"
    )

    df = pd.read_csv(latest_file)

    rows_in_file = len(df)

    if "batch_id" not in df.columns:

        raise ValueError(
            f"batch_id missing in "
            f"{latest_file.name}"
        )

    batch_id = df["batch_id"].iloc[0]

    # ==========================================
    # DUPLICATE CHECK
    # ==========================================

    if batch_exists(
        table_name,
        batch_id
    ):

        message = (
            f"Batch {batch_id} "
            f"already loaded"
        )

        logging.warning(message)

        write_batch_metadata(
            batch_id=batch_id,
            table_name=table_name,
            file_name=latest_file.name,
            rows_in_file=rows_in_file,
            rows_loaded=0,
            status="SKIPPED",
            message=message
        )

        return

    # ==========================================
    # LOAD DATA
    # ==========================================

    df.to_sql(
        table_name,
        engine,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=5000
    )

    logging.info(
        f"{table_name} loaded "
        f"Rows={rows_in_file}"
    )

    write_batch_metadata(
        batch_id=batch_id,
        table_name=table_name,
        file_name=latest_file.name,
        rows_in_file=rows_in_file,
        rows_loaded=rows_in_file,
        status="SUCCESS",
        message="Loaded Successfully"
    )

# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":

    pipeline_start = datetime.now()

    current_batch = "UNKNOWN"

    try:

        print("=" * 60)
        print("SUPABASE DATA LOAD STARTED")
        print("=" * 60)

        for folder_name, table_name in (
            TABLE_MAPPING.items()
        ):

            try:

                load_table(
                    folder_name,
                    table_name
                )

            except Exception as table_error:

                error_logger.error(
                    str(table_error)
                )

                logging.error(
                    f"{table_name} failed : "
                    f"{table_error}"
                )

        write_pipeline_status(
            batch_id=current_batch,
            status="SUCCESS",
            message="Pipeline completed"
        )

        print("\nPipeline Completed")

    except Exception as e:

        error_logger.error(str(e))

        write_pipeline_status(
            batch_id=current_batch,
            status="FAILED",
            message=str(e)
        )

        print(f"\nPipeline Failed : {e}")