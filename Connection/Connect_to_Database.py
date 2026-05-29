import pandas as pd
import json
from pathlib import Path
from sqlalchemy import create_engine, text

# ======================================================
# DATABASE CONNECTION
# ======================================================

DATABASE_URL = (
    "postgresql://neondb_owner:"
    "npg_hagm3rYZw1Bu"
    "@ep-broad-darkness-aqwha3yo-pooler."
    "c-8.us-east-1.aws.neon.tech/"
    "Ecommerce"
    "?sslmode=require&channel_binding=require"
)

# ======================================================
# CREATE ENGINE
# ======================================================

print("\nConnecting to Neon...\n")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

# ======================================================
# PROJECT ROOT
# ======================================================

BASE_DIR = Path(
    r"e:\Automated-E-Commerce-Funnel-Analysis-Business-Intelligence-Pipeline"
)

# ======================================================
# METADATA FILE
# ======================================================

METADATA_PATH = (
    BASE_DIR
    / "Data"
    / "Metadata"
    / "latest_metadata.json"
)

# ======================================================
# LOAD METADATA
# ======================================================

with open(METADATA_PATH, "r") as f:

    metadata = json.load(f)

print("Metadata Loaded Successfully")

# ======================================================
# EXTRACT METADATA VALUES
# ======================================================

batch_id = metadata["batch_id"]

run_id = metadata["run_id"]

raw_paths = metadata["raw_data_paths"]

record_counts = metadata["record_counts"]

# ======================================================
# CHECK IF BATCH ALREADY EXISTS
# ======================================================

print(f"\nChecking Batch: {batch_id}")

batch_check_query = text("""

SELECT COUNT(*)

FROM metadata.pipeline_runs

WHERE batch_id = :batch_id

""")

with engine.connect() as conn:

    existing_batch = conn.execute(

        batch_check_query,

        {"batch_id": batch_id}

    ).scalar()

FORCE_RERUN = True

# ======================================================
# CHECK EXISTING BATCH
# ======================================================

if existing_batch > 0:

    print(f"\nBatch Already Exists: {batch_id}")

    if FORCE_RERUN:

        print("\nFORCE RERUN ENABLED")

        print("Cleaning Existing Batch Data...")

        with engine.begin() as conn:

            # ==========================================
            # DELETE FACT TABLE DATA
            # ==========================================

            conn.execute(text("""

                DELETE FROM analytics.fact_orders

                WHERE batch_id = :batch_id

            """), {"batch_id": batch_id})

            conn.execute(text("""

                DELETE FROM analytics.fact_events

                WHERE batch_id = :batch_id

            """), {"batch_id": batch_id})

            # ==========================================
            # DELETE STAGING DATA
            # ==========================================

            conn.execute(text("""

                DELETE FROM staging.orders_stg

                WHERE batch_id = :batch_id

            """), {"batch_id": batch_id})

            conn.execute(text("""

                DELETE FROM staging.events_stg

                WHERE batch_id = :batch_id

            """), {"batch_id": batch_id})

            conn.execute(text("""

                DELETE FROM staging.sessions_stg

                WHERE batch_id = :batch_id

            """), {"batch_id": batch_id})

            conn.execute(text("""

                DELETE FROM staging.users_stg

                WHERE batch_id = :batch_id

            """), {"batch_id": batch_id})

            conn.execute(text("""

                DELETE FROM staging.products_stg

                WHERE batch_id = :batch_id

            """), {"batch_id": batch_id})

            # ==========================================
            # DELETE METADATA
            # ==========================================

            conn.execute(text("""

                DELETE FROM metadata.file_tracker

                WHERE batch_id = :batch_id

            """), {"batch_id": batch_id})

            conn.execute(text("""

                DELETE FROM metadata.pipeline_runs

                WHERE batch_id = :batch_id

            """), {"batch_id": batch_id})

        print("Previous Failed Batch Cleaned")

    else:

        raise Exception(
            "Duplicate Batch Load Prevented"
        )

print(f"\nProceeding With Batch: {batch_id}")

print(f"\nNew Batch Found: {batch_id}")

# ======================================================
# LOAD CSV FILES
# ======================================================

print("\nLoading CSV Files...\n")

products_df = pd.read_csv(
    BASE_DIR / raw_paths["products"]
)

users_df = pd.read_csv(
    BASE_DIR / raw_paths["users"]
)

sessions_df = pd.read_csv(
    BASE_DIR / raw_paths["sessions"]
)

events_df = pd.read_csv(
    BASE_DIR / raw_paths["events"]
)

orders_df = pd.read_csv(
    BASE_DIR / raw_paths["orders"]
)

print("All CSV Files Loaded Successfully")

# ======================================================
# INSERT PIPELINE RUN METADATA
# ======================================================

print("\nInserting Pipeline Metadata...\n")

pipeline_run_df = pd.DataFrame([{

    "run_id":
        run_id,

    "batch_id":
        batch_id,

    "year":
        metadata["year"],

    "week_number":
        metadata["week_number"],

    "pipeline_start":
        metadata["generated_at"],

    "pipeline_end":
        metadata["generated_at"],

    "status":
        metadata["status"],

    "total_records_loaded":
        sum(record_counts.values())
}])

pipeline_run_df.to_sql(

    name="pipeline_runs",

    schema="metadata",

    con=engine,

    if_exists="append",

    index=False,

    method="multi",

    chunksize=5000
)

print("Pipeline Metadata Inserted")

# ======================================================
# LOAD STAGING TABLES
# ======================================================

print("\nLoading Staging Tables...\n")

table_mapping = {

    "products_stg":
        products_df,

    "users_stg":
        users_df,

    "sessions_stg":
        sessions_df,

    "events_stg":
        events_df,

    "orders_stg":
        orders_df
}

for table_name, dataframe in table_mapping.items():

    print(f"Loading {table_name}...")

    dataframe.to_sql(

        name=table_name,

        schema="staging",

        con=engine,

        if_exists="append",

        index=False,

        method="multi",

        chunksize=5000
    )

    print(f"{table_name} Loaded Successfully")

# ======================================================
# INSERT FILE TRACKER
# ======================================================

print("\nUpdating File Tracker...\n")

file_tracker_records = []

for dataset_name, path in raw_paths.items():

    file_tracker_records.append({

        "run_id":
            run_id,

        "batch_id":
            batch_id,

        "dataset_name":
            dataset_name,

        "file_name":
            Path(path).name,

        "file_path":
            path,

        "record_count":
            record_counts[dataset_name],

        "file_type":
            "RAW",

        "ingestion_time":
            metadata["generated_at"],

        "is_latest":
            True
    })

file_tracker_df = pd.DataFrame(
    file_tracker_records
)

file_tracker_df.to_sql(

    name="file_tracker",

    schema="metadata",

    con=engine,

    if_exists="append",

    index=False,

    method="multi"
)

print("File Tracker Updated Successfully")

# ======================================================
# EXECUTE STORED PROCEDURES
# ======================================================

print("\nExecuting SQL Procedures...\n")

with engine.begin() as conn:

    conn.execute(
        text(
            "CALL analytics.sp_load_dimensions();"
        )
    )

    conn.execute(
        text(
            "CALL analytics.sp_load_facts();"
        )
    )

    conn.execute(
        text(
            "CALL analytics.sp_refresh_weekly_summary();"
        )
    )

print("SQL Procedures Executed Successfully")

# ======================================================
# CLEAN STAGING TABLES
# ======================================================

print("\nCleaning Staging Tables...\n")

staging_tables = [

    "products_stg",
    "users_stg",
    "sessions_stg",
    "events_stg",
    "orders_stg"
]

with engine.begin() as conn:

    for table in staging_tables:

        conn.execute(

            text(
                f"TRUNCATE TABLE staging.{table};"
            )
        )

print("Staging Tables Cleaned Successfully")

# ======================================================
# FINAL OUTPUT
# ======================================================

print("\n" + "=" * 60)

print("NEON ETL PIPELINE EXECUTED SUCCESSFULLY")

print("=" * 60)

print(f"Batch ID : {batch_id}")

print(f"Run ID   : {run_id}")

print("=" * 60)