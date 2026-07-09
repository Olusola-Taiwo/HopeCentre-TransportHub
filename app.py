import streamlit as st
import pandas as pd
import uuid
from datetime import datetime
from sqlalchemy import create_engine
import os
import requests
import base64

# ---------------------------------------------------------
# Load secrets
# ---------------------------------------------------------
NEON_URL = os.getenv("NEON_URL")   # Example: postgres://user:pass@host/db
NEON_PG  = os.getenv("NEON_PG")    # Optional – not used at startup

# ---------------------------------------------------------
# SAFE BACKGROUND IMAGE + DARK OVERLAY
# ---------------------------------------------------------
def add_bg_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            encoded = base64.b64encode(img_file.read()).decode()
    except Exception:
        return  # Fail gracefully

    css = f"""
    <style>
        .stApp {{
            background-image: url("data:image/jpg;base64,{encoded}");
            background-size: cover;
            background-position: center center;
            background-repeat: no-repeat;
            background-attachment: fixed;
            position: relative;
        }}

        /* Dark overlay */
        .stApp::before {{
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.45);
            z-index: 0;
        }}

        /* Ensure all content stays above overlay */
        .main-content {{
            position: relative;
            z-index: 2;
        }}

        .form-card {{
            background: rgba(255, 255, 255, 0.92);
            padding: 35px;
            border-radius: 18px;
            box-shadow: 0px 4px 20px rgba(0,0,0,0.25);
            backdrop-filter: blur(6px);
            max-width: 700px;
            margin: auto;
        }}

        .hero {{
            background: rgba(255,255,255,0.85);
            padding: 50px 20px;
            text-align: center;
            border-radius: 18px;
            box-shadow: 0px 4px 20px rgba(0,0,0,0.15);
            margin-bottom: 40px;
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# ---------------------------------------------------------
# MAIN APP
# ---------------------------------------------------------
def main():

    st.set_page_config(
        page_title="RCCG Hope Centre Transport Booking",
        page_icon="🚐",
        layout="centered"
    )

    # SAFE background load
    add_bg_image("tp_bkground.jpg")

    st.markdown("<div class='main-content'>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # HERO SECTION
    # ---------------------------------------------------------
    st.markdown('<div class="hero">', unsafe_allow_html=True)

    st.image("hopecentre_logo.png", width=160)
    st.markdown("<h1>RCCG Hope Centre – Crewe</h1>", unsafe_allow_html=True)
    st.markdown("<h3>Centre for Hope, Love & Power</h3>", unsafe_allow_html=True)
    st.markdown("""
        <p>
            Welcome to our Sunday Transport Booking Hub.<br>
            We provide <strong>free transport</strong> every Sunday for worship service.<br>
            Please book your seat below.
        </p>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ---------------------------------------------------------
    # BOOKING FORM CARD
    # ---------------------------------------------------------
    st.markdown('<div class="form-card">', unsafe_allow_html=True)

    st.header("Sunday Transport Booking Form")

    # Consent
    consent = st.checkbox("I give consent in compliance with GDPR")
    if not consent:
        st.warning("You must give consent to continue.")
        st.stop()

    # Preferred Name (REQUIRED)
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

    children_count = None
    if location == "Home":
        children_count = st.number_input(
            "How many children will be travelling?",
            min_value=0,
            max_value=10,
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
                "full_address": full_address,
                "preferred_name": preferred_name.strip(),
                "children_count": int(children_count) if children_count is not None else None
            }])

            try:
                engine = create_engine(f"{NEON_URL}?sslmode=require")
                df.to_sql("bookings", engine, if_exists="append", index=False)
                st.success("Your booking has been received. Thank you!")
                st.balloons()
            except Exception as e:
                st.error("Database error — could not save booking.")
                st.code(str(e))

    st.markdown('</div></div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
