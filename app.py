import streamlit as st
import pandas as pd
import uuid
from datetime import datetime
from sqlalchemy import create_engine
import os
import psycopg2
import requests

# ---------------------------------------------------------
# Load secrets
# ---------------------------------------------------------
NEON_URL = os.getenv("NEON_URL")
NEON_PG  = os.getenv("NEON_PG")
ADDRESS_API_KEY = os.getenv("ADDRESS_API_KEY")

# ---------------------------------------------------------
# Connection Test
# ---------------------------------------------------------
st.write("Testing Neon database connection...")

try:
    conn = psycopg2.connect(NEON_PG)
    st.success("Connected to Neon successfully!")
    conn.close()
except Exception as e:
    st.error("Connection failed.")
    st.code(str(e))
    st.stop()

# ---------------------------------------------------------
# SQLAlchemy engine
# ---------------------------------------------------------
engine = create_engine(NEON_URL)

# ---------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------
st.title("RCCG Hope Centre – Sunday Transport Booking")

st.write("Please fill in your details below to book transport for Sunday service.")

# Consent
consent = st.checkbox("I give consent in compliance with GDPR")
if not consent:
    st.warning("You must give consent to continue.")
    st.stop()

# Postcode
postcode = st.text_input("Enter your postcode (e.g., CW1 2AB)").strip()

addresses = []

if postcode:
    try:
        url = f"https://api.ideal-postcodes.co.uk/v1/postcodes/{postcode}?api_key={ADDRESS_API_KEY}"
        response = requests.get(url).json()

        if response.get("result"):
            for addr in response["result"]["addresses"]:
                full = addr["formatted_address"]
                addresses.append(full)

            st.success("Postcode found. Please select your full address.")
        else:
            st.error("Postcode not found. Please check and try again.")
    except Exception as e:
        st.error("Error looking up postcode.")
        st.code(str(e))

# Address selection
full_address = None
if addresses:
    full_address = st.selectbox("Select your full address", addresses)

# Location
location = st.selectbox(
    "Preferred Pick-up Location",
    [
        "Burger King / KFC by Grand Junction",
        "ALDI by Nantwich Road",
        "ASDA",
        "LIDL / Costa Coffee by Mills Street",
        "Big Morissons"
    ]
)

# Pickup time
pickup_time = st.selectbox(
    "Preferred Pick-up Time",
    ["07:00","08:00","08:45","09:00","09:15","09:30","09:45","10:00"]
)

# Phone
phone = st.text_input("Phone Number")

# Comments
comments = st.text_area("Comments / Suggestions")

# ---------------------------------------------------------
# Submit booking
# ---------------------------------------------------------
if st.button("Submit Booking"):
    if not phone:
        st.error("Please enter a phone number.")
    elif not postcode:
        st.error("Please enter a postcode.")
    elif not full_address:
        st.error("Please select your full address.")
    else:
        booking_id = str(uuid.uuid4())

        df = pd.DataFrame([{
            "booking_id": booking_id,
            "consent": True,
            "location": location,
            "pickup_time": pickup_time,
            "phone": phone,
            "comments": comments,
            "driver": None,
            "checked_in": False,
            "created_at": datetime.now(),
            "postcode": postcode,
            "full_address": full_address
        }])

        df.to_sql(
            "bookings",
            engine,
            if_exists="append",
            index=False
        )

        st.success("Your booking has been received. Thank you!")
        st.balloons()

        st.info("No SMS or WhatsApp notifications are enabled at this time.")
