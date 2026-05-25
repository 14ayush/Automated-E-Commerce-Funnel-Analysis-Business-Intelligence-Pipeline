import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta
import random
import os
import uuid

fake=Faker()
# now we are configuration of our requirements.

Num_products=200
Num_user=15000

# before generate the random data we must set the funnel like how much visit the website to how much order the product 

FUNNEL_CONFIG= {
    "homepage_visit":15000,
    "product_view_rate":0.70,
    "product_add_to_cart":0.45,
    "checkout_rate":0.60,
    "order_purchased":.80
}
BASE_PATH = "Data/raw"
folders = [
    f"{BASE_PATH}/users",
    f"{BASE_PATH}/sessions",
    f"{BASE_PATH}/events",
    f"{BASE_PATH}/orders",
    f"{BASE_PATH}/products"
]
for folder in folders:
    os.makedirs(folder, exist_ok=True)

print("All folders created successfully!")
today = datetime.today()

start_date = today - timedelta(days=today.weekday() + 7)
end_date = start_date + timedelta(days=6)

year = start_date.year
week_number = start_date.isocalendar()[1]

batch_id = f"{year}_W{week_number}"
load_timestamp = datetime.now()


# now the task is to setup the date range part like we are automating the things 

today=datetime.today()

start_date=today-timedelta(days=today.weekday()+7)
end_date=start_date+timedelta(days=6)

# now we are adding the products and categories

category=[
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

products=[]

for i in range(Num_products):
    cost_price=round(random.uniform(850,5000),2)

    selling_price=round(cost_price*random.uniform(1.5,2.5),2)

    products.append({
        "product_id":f"P{i+1}",
        "product_name":fake.word().title(),
        "category":random.choice(category),
        "brand":random.choice(brands),
        "cost_price":cost_price,
        "selling_price":selling_price,
        })

product_df=pd.DataFrame(products)

#now we are creating the user data set.

Channels=[
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

users=[]

for i in range(Num_user):
    sign_up_date=fake.date_between(start_date="-2y",end_date=today)
    
    users.append({
        "user_id":f"U{i+1}",
        "sign_up_date":sign_up_date,
        "gender":random.choice(["Male","Female","Prefer not to disclose"]),
        "age_group":random.choice(["18-24", "25-34", "35-44", "45+"]),
        "Country":"India",
        "city":random.choice(cities),
        "acquisition_channel": random.choice(Channels),
        "customer_segment": random.choice(segments)
    })
user_df=pd.DataFrame(users)

# now wea re creating the data for sessions 
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
session=[]

for i in range(5000):
    user=random.choice(user_df["user_id"].tolist())

    start_time=fake.date_time_between(start_date=start_date,end_date=end_date)
    duration=random.randint(1,40)
    end_time=start_time+timedelta(minutes=duration)

    session.append({
        "session_id": f"S{i+1}",
        "user_id": user,
        "session_start": start_time,
        "session_end": end_time,
        "traffic_source": random.choice(Channels),
        "campaign_name": fake.word().title(),
        "device_type": random.choice(device_distribution),
        "browser": random.choice(browsers),
        "operating_system": random.choice(
            ["Android", "Windows", "iOS", "MacOS"]
        ),
        "landing_page": random.choice(
            ["/home", "/products", "/offers"]
        )
    })

sessions_df = pd.DataFrame(session)

# lets create events

events = []

homepage_visits = FUNNEL_CONFIG["homepage_visit"]

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
    "homepage_visit": homepage_visits,
    "product_view": product_views,
    "add_to_cart": add_to_carts,
    "begin_checkout": checkouts,
    "purchase": purchases
}

event_id = 1

for event_type, count in event_counts.items():

    for _ in range(count):

        session = sessions_df.sample(1).iloc[0]

        events.append({
            "event_id": event_id,
            "user_id": session["user_id"],
            "session_id": session["session_id"],
            "event_timestamp":
                fake.date_time_between(
                    start_date=start_date,
                    end_date=end_date
                ),
            "event_type": event_type,
            "product_id":
                random.choice(
                    product_df["product_id"].tolist()
                ),
            "variant":
                random.choice(["A", "B"])
        })

        event_id += 1

events_df = pd.DataFrame(events)

# =====================================================
# ORDERS
# =====================================================

orders = []

purchase_events = events_df[
    events_df["event_type"] == "purchase"
]

for idx, row in purchase_events.iterrows():

    product = product_df[
        product_df["product_id"] == row["product_id"]
    ].iloc[0]

    quantity = random.randint(1, 4)

    discount = round(
        random.uniform(0, 0.15) *
        product["selling_price"] *
        quantity,
        2
    )

    gross_revenue = (
        product["selling_price"] *
        quantity
    )

    net_revenue = gross_revenue - discount

    shipping_cost = round(
        random.uniform(50, 200),
        2
    )

    tax_amount = round(
        net_revenue * 0.18,
        2
    )

    orders.append({
        "order_id": f"O{idx+1}",
        "user_id": row["user_id"],
        "product_id": row["product_id"],
        "order_date": row["event_timestamp"],
        "quantity": quantity,
        "unit_price": product["selling_price"],
        "discount": discount,
        "shipping_cost": shipping_cost,
        "tax_amount": tax_amount,
        "gross_revenue": gross_revenue,
        "net_revenue": net_revenue,
        "payment_method":
            random.choice(
                [
                    "UPI",
                    "Credit Card",
                    "Debit Card",
                    "Wallet"
                ]
            ),
        "order_status": "Completed"
    })

orders_df = pd.DataFrame(orders)

# lets create the data and save into files 

product_df.to_csv(
    f"{BASE_PATH}/products/products_{year}_week_{week_number}.csv",
    index=False
)

user_df.to_csv(
    f"{BASE_PATH}/users/users_{year}_week_{week_number}.csv",
    index=False
)

sessions_df.to_csv(
    f"{BASE_PATH}/sessions/sessions_{year}_week_{week_number}.csv",
    index=False
)

events_df.to_csv(
    f"{BASE_PATH}/events/events_{year}_week_{week_number}.csv",
    index=False
)

orders_df.to_csv(
    f"{BASE_PATH}/orders/orders_{year}_week_{week_number}.csv",
    index=False
)

print("=" * 50)
print("Weekly Ecommerce Data Generated Successfully")
print(f"Batch ID: {batch_id}")
print(f"Week Number: {week_number}")
print("=" * 50)
