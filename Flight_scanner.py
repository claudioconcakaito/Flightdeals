import streamlit as st
import requests
import datetime

# --- CONFIG ---
RAPIDAPI_KEY = st.secrets["RAPIDAPI_KEY"] # Store this in Streamlit secrets, NOT in code!
HOST = "skyscanner80.p.rapidapi.com"

# The routes
ROUTES = {
    "Spain (BCN)": "BCN",
    "China (PEK)": "PEK"
}

st.set_page_config(page_title="Glitch Scanner", layout="wide")
st.title("✈️ Business Class Glitch Tracker")
st.write("Scans SYD -> Spain/China for deals under $2,500 AUD")

# Search trigger
if st.button("🔄 Run Scan Now"):
    with st.spinner("Scanning for glitches..."):
        for name, dest in ROUTES.items():
            st.subheader(f"Checking SYD to {name}")
            
            # (Paste your search function from my previous message here)
            # Simulated result for example:
            st.success(f"✅ Checked SYD -> {dest}: $2,100 AUD found! [Book on Google]")
            st.error(f"⚠️ No glitches found yet for SYD -> {dest}.")
            
else:
    st.info("Click 'Run Scan Now' to check for current deals.")
