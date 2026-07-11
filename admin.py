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
    df = pd.read_sql("""
        SELECT 
            b.booking_id,
            b.created_at,
            b.preferred_name,
            b.location,
            b.children_count,
            b.pickup_time,
            b.phone,
            b.full_address,
            b.comments,
            b.driver_id,
            d.driver_name,
            b.checked_in
        FROM bookings b
        LEFT JOIN drivers d ON b.driver_id = d.driver_id
        ORDER BY b.created_at DESC
    """, engine)
except Exception as e:
    st.error("Unable to load bookings from database.")
    st.code(str(e))
    st.stop()

# ---------------------------------------------------------
# Display table
# ---------------------------------------------------------
st.subheader("📋 All Bookings")

st.dataframe(df, use_container_width=True)

# ---------------------------------------------------------
# Load drivers
# ---------------------------------------------------------
try:
    drivers_df = pd.read_sql("""
        SELECT driver_id, driver_name 
        FROM drivers 
        WHERE active = TRUE
        ORDER BY driver_name ASC
    """, engine)
except Exception as e:
    st.error("Unable to load drivers.")
    st.code(str(e))
    st.stop()

# ---------------------------------------------------------
# Driver assignment
# ---------------------------------------------------------
st.subheader("🚐 Assign Driver to Booking")

booking_ids = df["booking_id"].tolist()
selected_booking = st.selectbox("Select booking", booking_ids)

driver_names = drivers_df["driver_name"].tolist()
selected_driver_name = st.selectbox("Select driver", driver_names)

if st.button("Assign Driver"):
    try:
        # Get driver_id from selected driver name
        driver_id = int(
            drivers_df.loc[
                drivers_df["driver_name"] == selected_driver_name,
                "driver_id"
            ].iloc[0]
        )

        # Update booking
        with engine.begin() as conn:
            conn.execute(
                f"UPDATE bookings SET driver_id = {driver_id} WHERE booking_id = '{selected_booking}'"
            )

        st.success(f"Driver '{selected_driver_name}' assigned successfully.")
    except Exception as e:
        st.error("Failed to assign driver.")
        st.code(str(e))

# ---------------------------------------------------------
# Driver list
# ---------------------------------------------------------
st.subheader("🚗 Active Drivers")

st.dataframe(drivers_df, use_container_width=True)
