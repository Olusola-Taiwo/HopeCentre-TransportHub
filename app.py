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
st.title("RCCG Hope Centre – Free Transport Booking Hub")

st.write("Please fill in your details below to book transport for Sunday service.")

# Consent
consent = st.checkbox("I give consent in compliance with GDPR")
if not consent:
    st.warning("You must give consent to continue.")
    st.stop()

# ---------------------------------------------------------
# Postcode input (cleaned)
# ---------------------------------------------------------
postcode = st.text_input("Enter your postcode (e.g., CW1 2AB)").strip().replace(" ", "").upper()

postcode_valid = False

if postcode:
    try:
        url = f"https://api.postcodes.io/postcodes/{postcode}"
        response = requests.get(url).json()

        if response["status"] == 200:
            postcode_valid = True
            st.success("Postcode is valid. Please enter your house number and street name.")
        else:
            st.error("Postcode not found. Please check and try again.")
    except Exception as e:
        st.error("Error validating postcode.")
        st.code(str(e))

# ---------------------------------------------------------
# Address fields (always visible)
# ---------------------------------------------------------
house_number = st.text_input("House Number (e.g., 12)")
street_name = st.text_input("Street Name (e.g., Oak Street)")

# ---------------------------------------------------------
# Pick-up location
# ---------------------------------------------------------
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

# ---------------------------------------------------------
# Pick-up time
# ---------------------------------------------------------
pickup_time = st.selectbox(
    "Preferred Pick-up Time",
    ["07:00","08:00","08:45","09:00","09:15","09:30","09:45","10:00"]
)

# ---------------------------------------------------------
# Phone number
# ---------------------------------------------------------
phone = st.text_input("Phone Number")

# ---------------------------------------------------------
# Comments
# ---------------------------------------------------------
comments = st.text_area("Comments / Suggestions")

# ---------------------------------------------------------
# Submit booking
# ---------------------------------------------------------
if st.button("Submit Booking"):

    # Validation
    if not phone.strip():
        st.error("Please enter a phone number.")
    elif not postcode_valid:
        st.error("Please enter a valid postcode.")
    elif not house_number.strip():
        st.error("Please enter your house number.")
    elif not street_name.strip():
        st.error("Please enter your street name.")
    else:
        full_address = f"{house_number.strip()} {street_name.strip()}, {postcode}"

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
            "house_number": house_number.strip(),
            "street_name": street_name.strip(),
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
