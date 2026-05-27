import os
import logging
from pathlib import Path
from datetime import datetime

import pandas as pd

from dotenv import load_dotenv

from sqlalchemy import (
    create_engine,
    text
)

# ==========================================================
# PROJECT ROOT
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ==========================================================
# PATHS
# ==========================================================

CLEANED_DATA_PATH = (
    PROJECT_ROOT /
    "Data" /
    "CleanedData"
)

CONNECTION_PATH = (
    PROJECT_ROOT /
    "Connection"
)

LOG_PATH = CONNECTION_PATH / "logs"

METADATA_PATH = (
    CONNECTION_PATH /
    "metadata"
)

# ==========================================================
# CREATE DIRECTORIES
# ==========================================================

LOG_PATH.mkdir(
    parents=True,
    exist_ok=True
)

METADATA_PATH.mkdir(
    parents=True,
    exist_ok=True
)

# ==========================================================
# ENV VARIABLES
# ==========================================================

DATABASE_URL = os.getenv(
    "SUPABASE_DB_URL"
)

print(DATABASE_URL)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

# ==========================================================
# LOGGING
# ==========================================================

LOG_FILE = LOG_PATH / "database_load.log"

ERROR_FILE = LOG_PATH / "error.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(message)s"
    )
)

error_logger = logging.getLogger(
    "error_logger"
)

error_handler = logging.FileHandler(
    ERROR_FILE
)

error_logger.addHandler(error_handler)

error_logger.setLevel(logging.ERROR)

# ==========================================================
# METADATA FILE
# ==========================================================

METADATA_FILE = (
    METADATA_PATH /
    "load_metadata.csv"
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
# CREATE METADATA FILE
# ==========================================================

if not METADATA_FILE.exists():

    metadata_df = pd.DataFrame(columns=[

        "file_name",
        "table_name",
        "batch_id",
        "rows_loaded",
        "status",
        "loaded_at"

    ])

    metadata_df.to_csv(
        METADATA_FILE,
        index=False
    )

# ==========================================================
# READ METADATA
# ==========================================================

def read_metadata():

    return pd.read_csv(
        METADATA_FILE
    )

# ==========================================================
# WRITE METADATA
# ==========================================================

def write_metadata(
    file_name,
    table_name,
    batch_id,
    rows_loaded,
    status
):

    metadata = pd.DataFrame([{

        "file_name": file_name,
        "table_name": table_name,
        "batch_id": batch_id,
        "rows_loaded": rows_loaded,
        "status": status,
        "loaded_at": datetime.now()

    }])

    metadata.to_csv(
        METADATA_FILE,
        mode="a",
        header=False,
        index=False
    )

# ==========================================================
# CHECK FILE ALREADY LOADED
# ==========================================================

def already_loaded(file_name):

    metadata = read_metadata()

    if metadata.empty:

        return False

    return (
        file_name in
        metadata["file_name"].values
    )

# ==========================================================
# LOAD FILE
# ==========================================================

def load_file(file_path):

    file_name = file_path.name

    print(f"\nProcessing : {file_name}")

    # ======================================================
    # CHECK DUPLICATE
    # ======================================================

    if already_loaded(file_name):

        logging.warning(
            f"{file_name} already loaded"
        )

        print(
            f"SKIPPED : {file_name}"
        )

        return

    # ======================================================
    # IDENTIFY TABLE
    # ======================================================

    table_key = None

    lower_name = file_name.lower()

    for key in TABLE_MAPPING.keys():

        if key in lower_name:

            table_key = key
            break

    if table_key is None:

        logging.error(
            f"Unknown file type : "
            f"{file_name}"
        )

        return

    table_name = TABLE_MAPPING[table_key]

    # ======================================================
    # READ CSV
    # ======================================================

    df = pd.read_csv(file_path)

    if df.empty:

        logging.warning(
            f"{file_name} is empty"
        )

        return

    # ======================================================
    # BATCH CHECK
    # ======================================================

    if "batch_id" not in df.columns:

        raise ValueError(
            f"batch_id missing in "
            f"{file_name}"
        )

    batch_id = (
        df["batch_id"]
        .astype(str)
        .iloc[0]
    )

    rows_loaded = len(df)

    # ======================================================
    # LOAD TO DATABASE
    # ======================================================

    df.to_sql(
        table_name,
        con=engine,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=5000
    )

    # ======================================================
    # LOGGING
    # ======================================================

    logging.info(
        f"{file_name} loaded "
        f"into {table_name}"
    )

    write_metadata(
        file_name=file_name,
        table_name=table_name,
        batch_id=batch_id,
        rows_loaded=rows_loaded,
        status="SUCCESS"
    )

    print(
        f"SUCCESS : {file_name}"
    )

# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":

    try:

        print("=" * 60)

        print(
            "SUPABASE DATA LOAD STARTED"
        )

        print("=" * 60)

        # ==================================================
        # GET ALL CSV FILES
        # ==================================================

        csv_files = sorted(

            CLEANED_DATA_PATH.glob(
                "*.csv"
            )

        )

        if len(csv_files) == 0:

            print(
                "\nNo CSV files found"
            )

        # ==================================================
        # PROCESS FILES
        # ==================================================

        for file_path in csv_files:

            try:

                load_file(file_path)

            except Exception as e:

                logging.error(str(e))

                error_logger.error(str(e))

                print(
                    f"FAILED : "
                    f"{file_path.name}"
                )

        print("\nPipeline Completed")

    except Exception as e:

        logging.error(str(e))

        error_logger.error(str(e))

        print(
            f"\nPipeline Failed : {e}"
        )