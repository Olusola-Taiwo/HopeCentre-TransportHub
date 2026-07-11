import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import os

# ---------------------------------------------------------
# Load secrets
# ---------------------------------------------------------
NEON_URL = os.getenv("NEON_URL")

# ---------------------------------------------------------
# Page config
# ---------------------------------------------------------
st.set_page_config(
    page_title="Hope Centre Admin Dashboard",
    page_icon="🛠️",
    layout="wide"
)

st.title("🛠️ RCCG Hope Centre – Admin Dashboard")
st.write("View and manage all transport bookings.")

# ---------------------------------------------------------
# Database connection
# ---------------------------------------------------------
engine = create_engine(NEON_URL)

# ---------------------------------------------------------
# Load bookings
# ---------------------------------------------------------
try:
    df = pd.read_sql("SELECT * FROM bookings ORDER BY created_at DESC", engine)
except Exception as e:
    st.error("Unable to load bookings from database.")
    st.code(str(e))
    st.stop()

# ---------------------------------------------------------
# Display table
# ---------------------------------------------------------
st.subheader("📋 All Bookings")

# Reorder columns for clarity
columns_order = [
    "created_at",
    "preferred_name",
    "location",
    "children_count",
    "pickup_time",
    "phone",
    "full_address",
    "comments",
    "driver",
    "checked_in",
    "booking_id"
]

df = df[columns_order]

st.dataframe(df, use_container_width=True)

# ---------------------------------------------------------
# Driver assignment (simple version)
# ---------------------------------------------------------
st.subheader("🚐 Assign Driver")

booking_ids = df["booking_id"].tolist()
selected_booking = st.selectbox("Select booking", booking_ids)

driver_name = st.text_input("Driver Name")

if st.button("Assign Driver"):
    try:
        with engine.begin() as conn:
            conn.execute(
                f"UPDATE bookings SET driver = '{driver_name}' WHERE booking_id = '{selected_booking}'"
            )
        st.success("Driver assigned successfully.")
    except Exception as e:
        st.error("Failed to assign driver.")
        st.code(str(e))
