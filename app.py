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
NEON_URL = os.getenv("NEON_URL")     # SQLAlchemy URL
NEON_PG  = os.getenv("NEON_PG")      # psycopg2 URL

# ---------------------------------------------------------
# Database connection test (visible if broken)
# ---------------------------------------------------------
db_ok = True
try:
    test_conn = psycopg2.connect(NEON_PG)
    test_conn.close()
except Exception as e:
    db_ok = False
    st.error("❌ Database connection failed. Please check NEON_PG.")
    st.code(str(e))

# ---------------------------------------------------------
# Page configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="RCCG Hope Centre Transport Booking",
    page_icon="🚐",
    layout="centered"
)

# ---------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------
st.markdown("""
    <style>
        body {
            background: linear-gradient(135deg, #ff9a9e 0%, #fad0c4 40%, #fbc2eb 100%);
            background-attachment: fixed;
        }

        .hero {
            background: rgba(255,255,255,0.85);
            padding: 50px 20px;
            text-align: center;
            border-radius: 18px;
            box-shadow: 0px 4px 20px rgba(0,0,0,0.15);
            margin-bottom: 40px;
        }

        .form-card {
            background-color: #ffffff;
            padding: 35px;
            border-radius: 18px;
            box-shadow: 0px 4px 20px rgba(0,0,0,0.15);
            max-width: 700px;
            margin: auto;
        }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# HERO SECTION
# ---------------------------------------------------------
st.markdown('<div class="hero">', unsafe_allow_html=True)

st.image("hopecentre_logo.png", width=160)
st.markdown("<h1>RCCG Hope Centre – Crewe</h1>", unsafe_allow_html=True)
st.markdown("<h3>Centre for Hope, Love & Power</h3>", unsafe_allow_html=True)
st.markdown("""
    <p>
        Welcome to our Transport Booking Hub.<br>
        We provide <strong>free transport</strong> to support your journey to worship.<br>
        Please book your seat below.
    </p>
""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# BOOKING FORM
# ---------------------------------------------------------
st.markdown('<div class="form-card">', unsafe_allow_html=True)
st.header("Sunday Transport Booking Form")

# Consent
consent = st.checkbox("I give consent in compliance with GDPR")
if not consent:
    st.warning("You must give consent to continue.")
    st.stop()

# Preferred Name
preferred_name = st.text_input("Preferred Name (required)")

# Postcode
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

# Address fields
house_number = st.text_input("House Number (e.g., 12)")
street_name = st.text_input("Street Name (e.g., Oak Street)")

# Number of Adults (always required)
adult_count = st.number_input(
    "Number of Adults",
    min_value=1,
    max_value=100,
    step=1
)

# Number of Children (general)
children_general = st.number_input(
    "Number of Children",
    min_value=0,
    max_value=100,
    step=1
)

# Pick-up location
location = st.selectbox(
    "Preferred Pick-up Location",
    [
        "Burger King / KFC by Grand Junction",
        "ALDI by Nantwich Road",
        "ASDA",
        "LIDL / Costa Coffee by Mills Street",
        "Big Morissons",
        "Home"
    ]
)

# Children travelling (auto-populated when Home is selected)
children_count = None
if location == "Home":
    children_count = st.number_input(
        "How many children will be travelling?",
        min_value=children_general,
        max_value=100,
        step=1
    )

    if children_count == 0:
        st.error("Sorry, home pickup is only available for parents with kids.")

# Pick-up time
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

    if not preferred_name.strip():
        st.error("Please enter your preferred name.")
    elif adult_count < 1:
        st.error("At least one adult must be travelling.")
    elif location == "Home" and children_count == 0:
        st.error("Sorry, home pickup is only available for parents with kids.")
    elif not phone.strip():
        st.error("Please enter a phone number.")
    elif not postcode_valid:
        st.error("Please enter a valid postcode.")
    elif not house_number.strip():
        st.error("Please enter your house number.")
    elif not street_name.strip():
        st.error("Please enter your street name.")
    elif not db_ok:
        st.error("❌ Booking cannot be saved because the database is not connected.")
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
            "checked_in": False,
            "created_at": datetime.now(),
            "postcode": postcode,
            "house_number": house_number.strip(),
            "street_name": street_name.strip(),
            "full_address": full_address,
            "preferred_name": preferred_name.strip(),
            "adult_count": int(adult_count),
            "children_count": int(children_count) if children_count is not None else int(children_general),
            "driver_id": None   # FIXED — matches your database schema
        }])

        # ---------------------------------------------------------
        # Correct SQLAlchemy engine with SSL + stability
        # ---------------------------------------------------------
        try:
            engine = create_engine(
                NEON_URL,
                connect_args={"sslmode": "require"},
                pool_pre_ping=True,
                pool_recycle=300
            )

            df.to_sql("bookings", engine, if_exists="append", index=False)

            st.success("Your booking has been received. Thank you!")
            st.balloons()

        except Exception as e:
            st.error("❌ Failed to save booking to database.")
            st.code(str(e))

st.markdown('</div>', unsafe_allow_html=True)
