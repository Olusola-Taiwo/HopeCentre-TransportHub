import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import os

# ---------------------------------------------------------
# Load DB
# ---------------------------------------------------------
NEON_URL = os.getenv("NEON_URL")
engine = create_engine(NEON_URL)

st.set_page_config(page_title="Driver Manifest", page_icon="🧑‍✈️", layout="wide")
st.title("🧑‍✈️ Driver Manifest – RCCG Hope Centre")

# ---------------------------------------------------------
# Load drivers
# ---------------------------------------------------------
drivers_df = pd.read_sql("SELECT driver_id, driver_name FROM drivers WHERE active = TRUE", engine)

# ---------------------------------------------------------
# Select driver
# ---------------------------------------------------------
driver_names = drivers_df["driver_name"].tolist()
selected_driver_name = st.selectbox("Select Driver", driver_names)

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
        b.preferred_name,
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

# ⭐ FIX: wrap SQL in text() so named parameters work
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
    st.dataframe(manifest_df, use_container_width=True)

    # Summary
    total_adults = manifest_df["adult_count"].sum()
    total_children = manifest_df["children_count"].sum()

    st.markdown("### Summary")
    st.markdown(f"- **Adults:** {total_adults}")
    st.markdown(f"- **Children:** {total_children}")
    st.markdown(f"- **Total passengers:** {total_adults + total_children}")
