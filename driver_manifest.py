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

st.title("🚐 My Passengers")
st.markdown("### Select your name below to see your assigned passengers.")

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
        b.preferred_name AS passenger_name,
        b.location,
        b.children_count,
        b.adult_count,
        b.pickup_time,
        b.phone,
        b.full_address,
        b.comments
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
# Display manifest
# ---------------------------------------------------------
st.subheader(f"Passenger List for {selected_driver_name}")

if manifest_df.empty:
    st.info("No passengers assigned yet.")
else:
    # Make phone numbers clickable
    manifest_df["phone"] = manifest_df["phone"].apply(
        lambda x: f"📞 {x}"
    )

    st.dataframe(manifest_df, use_container_width=True)

    # Summary section
    total_adults = manifest_df["adult_count"].sum()
    total_children = manifest_df["children_count"].sum()
    total_passengers = total_adults + total_children

    st.markdown("### Summary")
    st.markdown(f"- **Adults:** {total_adults}")
    st.markdown(f"- **Children:** {total_children}")
    st.markdown(f"- **Total passengers:** {total_passengers}")

    st.markdown("---")
    st.markdown("### Tips for Drivers")
    st.markdown("- Tap the phone number to call the passenger.")
    st.markdown("- Follow pickup times in order.")
    st.markdown("- Check comments for special instructions.")
