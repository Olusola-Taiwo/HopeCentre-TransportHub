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
# Try database connection silently (no UI message)
# ---------------------------------------------------------
db_ok = True
try:
    conn = psycopg2.connect(NEON_PG)
    conn.close()
except:
    db_ok = False

# ---------------------------------------------------------
# Page configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="RCCG Hope Centre Transport Booking",
    page_icon="🚐",
    layout="centered"
)

# ---------------------------------------------------------
# Custom CSS for professional background + card layout
# ---------------------------------------------------------
st.markdown("""
    <style>
        body {
            background-color: #f5f7fa;
        }
        .main {
            background-color: #ffffff;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0px 0px 12px rgba(0,0,0,0.1);
        }
        .title {
            text-align: center;
            font-size: 32px;
            font-weight: bold;
            color: #003366;
            margin-bottom: 10px;
        }
        .subtitle {
            text-align: center;
            font-size: 16px;
            color: #555;
            margin-bottom: 25px;
        }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Header
# ---------------------------------------------------------
st.markdown('<div class="title">RCCG Hope Centre – Free Transport Booking Hub</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Please fill in your details below to book transport for Sunday service.</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# Consent
# ---------------------------------------------------------
consent = st.checkbox("I give consent in compliance with GDPR")
if not consent:
    st.warning("You must give consent to continue.")
    st.stop()

# ---------------------------------------------------------
# Postcode input
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
# Address fields
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

        engine = create_engine(NEON_URL)
        df.to_sql("bookings", engine, if_exists="append", index=False)

        st.success("Your booking has been received. Thank you!")
        st.balloons()

        st.info("No SMS or WhatsApp notifications are enabled at this time.")
