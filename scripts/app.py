import os
import uuid
from datetime import datetime

import pandas as pd
import streamlit as st
from twilio.rest import Client
from sqlalchemy import create_engine

# -----------------------------
# Load secrets from environment
# -----------------------------

# Twilio
ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
SMS_FROM = os.getenv("SMS_FROM")
WA_FROM = os.getenv("WA_FROM")

client = Client(ACCOUNT_SID, AUTH_TOKEN)

# Databricks SQL Warehouse
DB_SERVER = os.getenv("DATABRICKS_SERVER")
DB_HTTP_PATH = os.getenv("DATABRICKS_HTTP_PATH")
DB_TOKEN = os.getenv("DATABRICKS_TOKEN")

engine = create_engine(
    f"databricks+connector://token:{DB_TOKEN}@{DB_SERVER}?http_path={DB_HTTP_PATH}"
)

# -----------------------------
# Streamlit UI
# -----------------------------

st.title("RCCG Hope Centre – Sunday Transport Booking")
st.write("Please book your Sunday pick‑up. You are gracefully welcome.")

consent_choice = st.radio(
    "Please tick this box to signify consent in compliance with GDPR",
    ["I give consent", "I do not consent"]
)

if consent_choice == "I do not consent":
    st.error("You must give consent to continue.")
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

# -----------------------------
# Submit booking
# -----------------------------

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

        # Write to Databricks table: rccg_hopecentre_transporthub.core.bookings
        df.to_sql(
            "bookings",
            engine,
            schema="core",
            if_exists="append",
            index=False
        )

        st.success("Your booking has been received. A member of the Transport Unit will contact you shortly.")
        st.balloons()

        # SMS to user
        client.messages.create(
            body=f"RCCG Hope Centre: Your transport booking for {pickup_time} at {location} is confirmed.",
            from_=SMS_FROM,
            to=phone
        )

        # WhatsApp to user
        client.messages.create(
            body=f"RCCG Hope Centre: Your transport booking for {pickup_time} at {location} is confirmed.",
            from_=WA_FROM,
            to=f"whatsapp:{phone}"
        )

        # Notify admins via WhatsApp
        admin_numbers = ["+447467246331", "+447831713494"]
        for admin in admin_numbers:
            client.messages.create(
                body=f"New booking: {location} at {pickup_time}. Phone: {phone}",
                from_=WA_FROM,
                to=f"whatsapp:{admin}"
            )
