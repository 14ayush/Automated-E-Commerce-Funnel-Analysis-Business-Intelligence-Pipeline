import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta
import random
import os
import uuid
import logging
import json

# =====================================================
# INITIAL SETUP
# =====================================================

fake = Faker()

NUM_PRODUCTS = 200
NUM_USERS = 35000

# =====================================================
# BASE PATHS
# =====================================================

RAW_BASE_PATH = "Data/raw"

CONSOLIDATED_BASE_PATH = "Data/consolidated"

METADATA_BASE_PATH = "Data/metadata"

LOG_BASE_PATH = "Data/logs"

# =====================================================
# CREATE FOLDERS
# =====================================================

folders = [

    # RAW DATA
    f"{RAW_BASE_PATH}/users",
    f"{RAW_BASE_PATH}/sessions",
    f"{RAW_BASE_PATH}/events",
    f"{RAW_BASE_PATH}/orders",
    f"{RAW_BASE_PATH}/products",

    # CONSOLIDATED DATA
    f"{CONSOLIDATED_BASE_PATH}/consolidated_users",
    f"{CONSOLIDATED_BASE_PATH}/consolidated_sessions",
    f"{CONSOLIDATED_BASE_PATH}/consolidated_events",
    f"{CONSOLIDATED_BASE_PATH}/consolidated_orders",
    f"{CONSOLIDATED_BASE_PATH}/consolidated_products",

    # METADATA
    METADATA_BASE_PATH,

    # LOGS
    LOG_BASE_PATH
]

for folder in folders:

    os.makedirs(folder, exist_ok=True)

# =====================================================
# DATE CONFIGURATION
# =====================================================

today = datetime.today()

start_date = (
    today -
    timedelta(days=today.weekday() + 7)
)

end_date = (
    start_date +
    timedelta(days=6)
)

year = start_date.year

week_number = (
    start_date.isocalendar()[1]
)

batch_id = f"{year}_W{week_number}"

run_id = str(uuid.uuid4())

# =====================================================
# LOGGING CONFIGURATION
# =====================================================

log_file = (
    f"{LOG_BASE_PATH}/"
    f"pipeline_{batch_id}.txt"
)

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logging.info("Pipeline Started")

# =====================================================
# DYNAMIC TRAFFIC CONFIGURATION
# =====================================================

def get_week_multiplier(week_number):

    festival_weeks = {

        3: 1.15,
        12: 1.20,
        26: 1.35,
        33: 1.25,
        40: 1.80,
        41: 2.20,
        47: 1.70,
        51: 1.50
    }

    base_multiplier = random.uniform(
        0.85,
        1.20
    )

    return festival_weeks.get(
        week_number,
        base_multiplier
    )

weekly_multiplier = (
    get_week_multiplier(week_number)
)

base_traffic = random.randint(
    18000,
    35000
)

homepage_traffic = int(
    base_traffic * weekly_multiplier
)

FUNNEL_CONFIG = {

    "homepage_visit":
        homepage_traffic,

    "product_view_rate":
        random.uniform(0.60, 0.80),

    "product_add_to_cart":
        random.uniform(0.35, 0.55),

    "checkout_rate":
        random.uniform(0.50, 0.75),

    "order_purchased":
        random.uniform(0.70, 0.90)
}

logging.info(
    f"Homepage Traffic: {homepage_traffic}"
)

# =====================================================
# MASTER APPEND FUNCTION
# =====================================================

def append_to_master(df, master_path):

    if os.path.exists(master_path):

        existing_df = pd.read_csv(
            master_path
        )

        combined_df = pd.concat(
            [existing_df, df],
            ignore_index=True
        )

        combined_df.drop_duplicates(
            inplace=True
        )

        combined_df.to_csv(
            master_path,
            index=False
        )

    else:

        df.to_csv(
            master_path,
            index=False
        )

# =====================================================
# PRODUCT DATA
# =====================================================

categories = [
    "Electronics",
    "Fashion",
    "Home",
    "Beauty",
    "Sports",
    "Books"
]

brands = [
    "Nike",
    "Samsung",
    "Nokia",
    "Apple",
    "Puma",
    "Sony",
    "Adidas",
    "Boat",
    "Noise",
    "Dell"
]

products = []

try:

    for i in range(NUM_PRODUCTS):

        cost_price = round(
            random.uniform(850, 5000),
            2
        )

        selling_price = round(
            cost_price *
            random.uniform(1.5, 2.5),
            2
        )

        products.append({

            "run_id": run_id,
            "batch_id": batch_id,

            "product_id": f"P{i+1}",

            "product_name":
                fake.word().title(),

            "category":
                random.choice(categories),

            "brand":
                random.choice(brands),

            "cost_price":
                cost_price,

            "selling_price":
                selling_price
        })

    product_df = pd.DataFrame(products)

    logging.info(
        "Products Generated Successfully"
    )

except Exception as e:

    logging.error(
        f"Product Generation Failed: {str(e)}"
    )

# =====================================================
# USER DATA
# =====================================================

channels = [
    "Google Ads",
    "Facebook",
    "Instagram",
    "Organic",
    "Email",
    "Direct"
]

segments = [
    "Premium",
    "Regular",
    "Occasional"
]

cities = [
    "Delhi",
    "Mumbai",
    "Bangalore",
    "Hyderabad",
    "Pune",
    "Chennai",
    "Kolkata",
    "Jaipur",
    "Lucknow",
    "Noida"
]

users = []

try:

    for i in range(NUM_USERS):

        sign_up_date = fake.date_between(
            start_date="-2y",
            end_date=today
        )

        users.append({

            "run_id": run_id,
            "batch_id": batch_id,

            "user_id": f"U{i+1}",

            "sign_up_date":
                sign_up_date,

            "gender":
                random.choice([
                    "Male",
                    "Female",
                    "Prefer not to disclose"
                ]),

            "age_group":
                random.choice([
                    "18-24",
                    "25-34",
                    "35-44",
                    "45+"
                ]),

            "country":
                "India",

            "city":
                random.choice(cities),

            "acquisition_channel":
                random.choice(channels),

            "customer_segment":
                random.choice(segments)
        })

    user_df = pd.DataFrame(users)

    logging.info(
        "Users Generated Successfully"
    )

except Exception as e:

    logging.error(
        f"User Generation Failed: {str(e)}"
    )

# =====================================================
# SESSION DATA
# =====================================================

device_distribution = [
    "Mobile",
    "Desktop",
    "Tablet"
]

browsers = [
    "Chrome",
    "Firefox",
    "Edge",
    "Safari"
]

sessions = []

try:

    total_sessions = int(
        homepage_traffic * 0.20
    )

    for i in range(total_sessions):

        user = random.choice(
            user_df["user_id"].tolist()
        )

        start_time = fake.date_time_between(
            start_date=start_date,
            end_date=end_date
        )

        duration = random.randint(1, 40)

        end_time = (
            start_time +
            timedelta(minutes=duration)
        )

        sessions.append({

            "run_id": run_id,
            "batch_id": batch_id,

            "session_id": f"S{i+1}",

            "user_id": user,

            "session_start":
                start_time,

            "session_end":
                end_time,

            "traffic_source":
                random.choice(channels),

            "campaign_name":
                fake.word().title(),

            "device_type":
                random.choice(
                    device_distribution
                ),

            "browser":
                random.choice(browsers),

            "operating_system":
                random.choice([
                    "Android",
                    "Windows",
                    "iOS",
                    "MacOS"
                ]),

            "landing_page":
                random.choice([
                    "/home",
                    "/products",
                    "/offers"
                ])
        })

    sessions_df = pd.DataFrame(sessions)

    logging.info(
        "Sessions Generated Successfully"
    )

except Exception as e:

    logging.error(
        f"Session Generation Failed: {str(e)}"
    )

# =====================================================
# EVENTS DATA
# =====================================================

events = []

homepage_visits = (
    FUNNEL_CONFIG["homepage_visit"]
)

product_views = int(
    homepage_visits *
    FUNNEL_CONFIG["product_view_rate"]
)

add_to_carts = int(
    product_views *
    FUNNEL_CONFIG["product_add_to_cart"]
)

checkouts = int(
    add_to_carts *
    FUNNEL_CONFIG["checkout_rate"]
)

purchases = int(
    checkouts *
    FUNNEL_CONFIG["order_purchased"]
)

event_counts = {

    "homepage_visit":
        homepage_visits,

    "product_view":
        product_views,

    "add_to_cart":
        add_to_carts,

    "begin_checkout":
        checkouts,

    "purchase":
        purchases
}

event_id = 1

try:

    for event_type, count in (
        event_counts.items()
    ):

        for _ in range(count):

            session = (
                sessions_df
                .sample(1)
                .iloc[0]
            )

            selected_product = (
                product_df
                .sample(1)
                .iloc[0]
            )

            events.append({

                "run_id": run_id,
                "batch_id": batch_id,

                "event_id": event_id,

                "user_id":
                    session["user_id"],

                "session_id":
                    session["session_id"],

                "event_timestamp":
                    fake.date_time_between(
                        start_date=start_date,
                        end_date=end_date
                    ),

                "event_type":
                    event_type,

                "product_id":
                    selected_product[
                        "product_id"
                    ],

                "variant":
                    random.choice(
                        ["A", "B"]
                    )
            })

            event_id += 1

    events_df = pd.DataFrame(events)

    logging.info(
        "Events Generated Successfully"
    )

except Exception as e:

    logging.error(
        f"Events Generation Failed: {str(e)}"
    )

# =====================================================
# ORDERS DATA
# =====================================================

orders = []

purchase_events = events_df[
    events_df["event_type"] ==
    "purchase"
]

try:

    for idx, row in (
        purchase_events.iterrows()
    ):

        product = product_df[
            product_df["product_id"] ==
            row["product_id"]
        ].iloc[0]

        quantity = random.randint(1, 4)

        discount = round(
            random.uniform(0, 0.15)
            * product["selling_price"]
            * quantity,
            2
        )

        gross_revenue = (
            product["selling_price"]
            * quantity
        )

        net_revenue = (
            gross_revenue - discount
        )

        shipping_cost = round(
            random.uniform(50, 200),
            2
        )

        tax_amount = round(
            net_revenue * 0.18,
            2
        )

        orders.append({

            "run_id": run_id,
            "batch_id": batch_id,

            "order_id": f"O{idx+1}",

            "user_id":
                row["user_id"],

            "product_id":
                row["product_id"],

            "order_date":
                row["event_timestamp"],

            "quantity":
                quantity,

            "unit_price":
                product["selling_price"],

            "discount":
                discount,

            "shipping_cost":
                shipping_cost,

            "tax_amount":
                tax_amount,

            "gross_revenue":
                gross_revenue,

            "net_revenue":
                net_revenue,

            "payment_method":
                random.choice([
                    "UPI",
                    "Credit Card",
                    "Debit Card",
                    "Wallet"
                ]),

            "order_status":
                "Completed"
        })

    orders_df = pd.DataFrame(orders)

    logging.info(
        "Orders Generated Successfully"
    )

except Exception as e:

    logging.error(
        f"Orders Generation Failed: {str(e)}"
    )

# =====================================================
# SAVE RAW WEEKLY FILES
# =====================================================

products_weekly_path = (
    f"{RAW_BASE_PATH}/products/"
    f"products_{batch_id}.csv"
)

users_weekly_path = (
    f"{RAW_BASE_PATH}/users/"
    f"users_{batch_id}.csv"
)

sessions_weekly_path = (
    f"{RAW_BASE_PATH}/sessions/"
    f"sessions_{batch_id}.csv"
)

events_weekly_path = (
    f"{RAW_BASE_PATH}/events/"
    f"events_{batch_id}.csv"
)

orders_weekly_path = (
    f"{RAW_BASE_PATH}/orders/"
    f"orders_{batch_id}.csv"
)

product_df.to_csv(
    products_weekly_path,
    index=False
)

user_df.to_csv(
    users_weekly_path,
    index=False
)

sessions_df.to_csv(
    sessions_weekly_path,
    index=False
)

events_df.to_csv(
    events_weekly_path,
    index=False
)

orders_df.to_csv(
    orders_weekly_path,
    index=False
)

logging.info(
    "Raw Weekly Files Saved Successfully"
)

# =====================================================
# CONSOLIDATED FILES
# =====================================================

append_to_master(
    product_df,
    f"{CONSOLIDATED_BASE_PATH}/"
    f"consolidated_products/"
    f"master_products.csv"
)

append_to_master(
    user_df,
    f"{CONSOLIDATED_BASE_PATH}/"
    f"consolidated_users/"
    f"master_users.csv"
)

append_to_master(
    sessions_df,
    f"{CONSOLIDATED_BASE_PATH}/"
    f"consolidated_sessions/"
    f"master_sessions.csv"
)

append_to_master(
    events_df,
    f"{CONSOLIDATED_BASE_PATH}/"
    f"consolidated_events/"
    f"master_events.csv"
)

append_to_master(
    orders_df,
    f"{CONSOLIDATED_BASE_PATH}/"
    f"consolidated_orders/"
    f"master_orders.csv"
)

logging.info(
    "Consolidated Files Updated Successfully"
)

# =====================================================
# METADATA JSON
# =====================================================

metadata = {

    "batch_id":
        batch_id,

    "run_id":
        run_id,

    "year":
        year,

    "week_number":
        week_number,

    "generated_at":
        str(datetime.now()),

    "raw_data_paths": {

        "products":
            products_weekly_path,

        "users":
            users_weekly_path,

        "sessions":
            sessions_weekly_path,

        "events":
            events_weekly_path,

        "orders":
            orders_weekly_path
    },

    "consolidated_data_paths": {

        "products":
            f"{CONSOLIDATED_BASE_PATH}/"
            f"consolidated_products/"
            f"master_products.csv",

        "users":
            f"{CONSOLIDATED_BASE_PATH}/"
            f"consolidated_users/"
            f"master_users.csv",

        "sessions":
            f"{CONSOLIDATED_BASE_PATH}/"
            f"consolidated_sessions/"
            f"master_sessions.csv",

        "events":
            f"{CONSOLIDATED_BASE_PATH}/"
            f"consolidated_events/"
            f"master_events.csv",

        "orders":
            f"{CONSOLIDATED_BASE_PATH}/"
            f"consolidated_orders/"
            f"master_orders.csv"
    },

    "record_counts": {

        "products":
            len(product_df),

        "users":
            len(user_df),

        "sessions":
            len(sessions_df),

        "events":
            len(events_df),

        "orders":
            len(orders_df)
    },

    "status":
        "SUCCESS"
}

# Weekly Metadata JSON

weekly_metadata_json = (
    f"{METADATA_BASE_PATH}/"
    f"metadata_{batch_id}.json"
)

with open(
    weekly_metadata_json,
    "w"
) as json_file:

    json.dump(
        metadata,
        json_file,
        indent=4
    )

# Latest Metadata JSON

latest_metadata_json = (
    f"{METADATA_BASE_PATH}/"
    f"latest_metadata.json"
)

with open(
    latest_metadata_json,
    "w"
) as json_file:

    json.dump(
        metadata,
        json_file,
        indent=4
    )

logging.info(
    "Metadata JSON Files Saved Successfully"
)

# =====================================================
# FINAL OUTPUT
# =====================================================

print("=" * 60)
print("Weekly Ecommerce Data Generated Successfully")
print(f"Batch ID: {batch_id}")
print(f"Run ID: {run_id}")
print("=" * 60)

logging.info(
    "Pipeline Completed Successfully"
)