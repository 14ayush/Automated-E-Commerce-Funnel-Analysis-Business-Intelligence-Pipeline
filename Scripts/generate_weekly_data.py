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
Num_user=1500

# before generate the random data we must set the funnel like how much visit the website to how much order the product 

FUNNEL_CONFIG= {
    "homepage_visit":1500,
    "product_view_rate":0.70,
    "product_add_to_cart":0.45,
    "checkout_rate":0.60,
    "order_purchased":.80
}
# creating the directory
OUTPUT_DIR=".../Data/raw"
os.makedirs(OUTPUT_DIR, exist_ok=True)

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

    selling_price=round(cost_price*random(1.5,2.5),2)

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
        "gender":random.choice("Male","Female","Prefer not to disclose"),
        "age_group":random.choice(["18-24", "25-34", "35-44", "45+"]),
        "Country":"India",
        "city":random.choice(cities),
        "acquisition_channel": random.choice(Channels),
        "customer_segment": random.choice(segments)
    })
user_df=pd.DataFrame(users)



