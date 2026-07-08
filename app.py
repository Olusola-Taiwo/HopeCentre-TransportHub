import streamlit as st
import pandas as pd
import uuid
from datetime import datetime
from sqlalchemy import create_engine
from twilio.rest import Client
import os
import psycopg2

# ---------------------------------------------------------
# Load secrets
# ---------------------------------------------------------
NEON_URL = os.getenv("NEON_URL")      # SQLAlchemy format
NEON_PG  = os.getenv("NEON_PG")       # psycopg2 format

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
SMS_FROM = os.getenv("SMS_FROM")
WA_FROM = os.getenv("WA_FROM")

client = Client(ACCOUNT_SID, AUTH_TOKEN)

# ---------------------------------------------------------
# Connection Test (correct format)
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
# SQLAlchemy engine (correct format)
# ---------------------------------------------------------
engine = create_engine(NEON_URL)

# ---------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------
st.title("RCCG Hope Centre – Sunday Transport Booking")

st.write("Please fill in your details below to book transport for Sunday service.")

consent = st.checkbox("I give consent in compliance with GDPR")
if not consent:
    st.warning("You must give consent to continue.")
    st.stop()

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

pickup_time = st.selectbox(
    "Preferred Pick-up Time",
    ["07:00","08:00","08:45","09:00","09:15","09:30","09:45","10:00"]
)

phone = st.text_input("Phone Number")
comments = st.text_area("Comments / Suggestions")

# ---------------------------------------------------------
# Submit booking
# ---------------------------------------------------------
if st.button("Submit Booking"):
    if not phone:
        st.error("Please enter a phone number.")
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
            "created_at": datetime.now()
        }])

        df.to_sql(
            "bookings",
            engine,
            if_exists="append",
            index=False
        )

        st.success("Your booking has been received. Thank you!")
        st.balloons()

        client.messages.create(
            body=f"RCCG Hope Centre: Your transport booking for {pickup_time} at {location} is confirmed.",
            from_=SMS_FROM,
            to=phone
        )

        client.messages.create(
            body=f"New booking: {location} at {pickup_time}. Phone: {phone}",
            from_=WA_FROM,
            to=f"whatsapp:{phone}"
        )
