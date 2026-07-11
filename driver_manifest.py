import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import os

# ---------------------------------------------------------
# Load DB
# ---------------------------------------------------------
NEON_URL = os.getenv("NEON_URL")
engine = create_engine(NEON_URL)

# ---------------------------------------------------------
# Page setup
# ---------------------------------------------------------
st.set_page_config(page_title="My Passengers", page_icon="🚐", layout="wide")

st.title("🚐 My Passengers & Check‑In")
st.markdown("### Select your name to see your passengers and check them in.")

# ---------------------------------------------------------
# Load drivers
# ---------------------------------------------------------
drivers_df = pd.read_sql("SELECT driver_id, driver_name FROM drivers WHERE active = TRUE", engine)

driver_names = drivers_df["driver_name"].tolist()
selected_driver_name = st.selectbox("Driver Name", driver_names)

# Get driver_id
driver_id = int(
    drivers_df.loc[
        drivers_df["driver_name"] == selected_driver_name,
        "driver_id"
    ].iloc[0]
)

# ---------------------------------------------------------
# Load bookings for this driver
# ---------------------------------------------------------
query = """
    SELECT 
        b.booking_id,
        b.preferred_name AS passenger_name,
        b.location,
        b.children_count,
        b.adult_count,
        b.pickup_time,
        b.phone,
        b.full_address,
        b.comments,
        b.checked_in
    FROM bookings b
    WHERE b.driver_id = :driver_id
    ORDER BY b.pickup_time ASC
"""

manifest_df = pd.read_sql(
    text(query),
    engine,
    params={"driver_id": driver_id}
)

# ---------------------------------------------------------
# Display manifest + check‑in
# ---------------------------------------------------------
st.subheader(f"Passengers Assigned to {selected_driver_name}")

if manifest_df.empty:
    st.info("No passengers assigned yet.")
else:
    for index, row in manifest_df.iterrows():
        passenger = row["passenger_name"]
        booking_id = row["booking_id"]
        checked_in = row["checked_in"]

        col1, col2, col3, col4 = st.columns([4, 2, 2, 2])

        with col1:
            st.write(f"**{passenger}** — {row['location']}")
            st.write(f"📍 {row['full_address']}")
            st.write(f"📞 {row['phone']}")

        with col2:
            st.write(f"🕒 {row['pickup_time']}")

        with col3:
            st.write(f"👨 {row['adult_count']} adults")
            st.write(f"🧒 {row['children_count']} children")

        with col4:
            if checked_in:
                st.success("Checked In")
            else:
                if st.button(f"Check In", key=booking_id):
                    with engine.begin() as conn:
                        conn.execute(
                            text("UPDATE bookings SET checked_in = TRUE WHERE booking_id = :bid"),
                            {"bid": booking_id}
                        )
                    st.experimental_rerun()

    # Summary section
    total_adults = manifest_df["adult_count"].sum()
    total_children = manifest_df["children_count"].sum()
    total_passengers = total_adults + total_children

    st.markdown("---")
    st.markdown("### Summary")
    st.markdown(f"- **Adults:** {total_adults}")
    st.markdown(f"- **Children:** {total_children}")
    st.markdown(f"- **Total passengers:** {total_passengers}")
