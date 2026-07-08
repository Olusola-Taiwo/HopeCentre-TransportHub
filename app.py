import streamlit as st
import pandas as pd
import uuid
from datetime import datetime
from sqlalchemy import create_engine
from twilio.rest import Client
import os

# ---------------------------------------------------------
# Load secrets from Streamlit Cloud
# ---------------------------------------------------------
SUPABASE_URL = "postgresql+psycopg2://postgres:Onpoint247%40Hismercy@db.ruslhscgzrpdljxjtbnx.supabase.co:5432/postgres"

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
SMS_FROM = os.getenv("SMS_FROM")
WA_FROM = os.getenv("WA_FROM")

client = Client(ACCOUNT_SID, AUTH_TOKEN)

# ---------------------------------------------------------
# Database engine (Supabase PostgreSQL)
# ---------------------------------------------------------
engine = create_engine(SUPABASE_URL)

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

        # Insert into Supabase PostgreSQL
        df.to_sql(
            "bookings",
            engine,
            if_exists="append",
            index=False
        )

        st.success("Your booking has been received. Thank you!")
        st.balloons()

        # SMS confirmation
        client.messages.create(
            body=f"RCCG Hope Centre: Your transport booking for {pickup_time} at {location} is confirmed.",
            from_=SMS_FROM,
            to=phone
        )

        # WhatsApp notification to admin
        client.messages.create(
            body=f"New booking: {location} at {pickup_time}. Phone: {phone}",
            from_=WA_FROM,
            to=f"whatsapp:{phone}"
        )
