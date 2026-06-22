import streamlit as st
import requests
import datetime
import json

# --- PAGE CONFIG ---
st.set_page_config(page_title="SYD Business Scanner", layout="wide")
st.title("🚨 DIAGNOSTIC MODE ACTIVE 🚨")
st.caption("This version shows the RAW error from the API so we can fix it.")

# --- API CONFIG ---
SERP_API_KEY = st.secrets.get("SERP_API_KEY", "")
BASE_URL = "https://serpapi.com/search"

if not SERP_API_KEY:
    st.error("❌ SerpApi Key missing! Please add 'SERP_API_KEY' to your Streamlit secrets.")
    st.stop()

# --- DIAGNOSTIC SCANNER ---
def diagnostic_scan():
    future_date = (datetime.date.today() + datetime.timedelta(days=90)).strftime("%Y-%m-%d")
    
    # We use "LHR" (London Heathrow) because it is guaranteed to exist.
    params = {
        "api_key": SERP_API_KEY,
        "engine": "google_flights",
        "departure_id": "SYD",
        "arrival_id": "LHR",
        "outbound_date": future_date,
        "cabin_class": "business",
        "currency": "AUD",
        "hl": "en",
        "gl": "au"
    }

    st.write(f"**Sending request to SerpApi with key:** `{SERP_API_KEY[:10]}...`")
    
    try:
        response = requests.get(BASE_URL, params=params)
        
        # --- THIS IS THE DEBUGGING PART ---
        st.subheader("📡 RAW API RESPONSE")
        st.write(f"**HTTP Status Code:** {response.status_code}")
        
        if response.status_code != 200:
            st.error(f"API returned status code {response.status_code}. The request was rejected.")
            st.text("Raw response body:")
            st.code(response.text)
            return

        # Try to read the JSON
        data = response.json()
        
        # Check if SerpApi returned a specific error message inside the JSON
        if "error" in data:
            st.error(f"❌ SerpApi returned an error: {data['error']}")
            st.json(data) # Print the full error JSON
            return
            
        # If we made it here, the API succeeded.
        st.success("✅ API CONNECTION SUCCESSFUL! The key works and SerpApi responded.")
        st.json(data) # Show the raw data so we can see why it wasn't parsing before

    except Exception as e:
        st.error("🔥 The Python code crashed before the API could respond.")
        st.code(str(e))

# --- RUN DIAGNOSTIC ---
if st.button("🚀 RUN DIAGNOSTIC SCAN NOW"):
    diagnostic_scan()
else:
    st.info("Click the button above. The app will show you the EXACT error message from SerpApi.")