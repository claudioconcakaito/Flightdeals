import streamlit as st
import requests
import datetime
import json

# --- PAGE CONFIG ---
st.set_page_config(page_title="SYD Business Scanner", layout="wide")
st.title("✈️ SYD Business Class Fare Finder (2 Adults)")
st.caption("Correctly searches All Spain or All China using valid Google Flight regional codes.")

# --- API CONFIG ---
SERP_API_KEY = st.secrets.get("SERP_API_KEY", "")
BASE_URL = "https://serpapi.com/search"

if not SERP_API_KEY:
    st.error("❌ SerpApi Key missing! Please add 'SERP_API_KEY' to your Streamlit secrets.")
    st.stop()

# --- USER CONTROLS ---
st.subheader("1. Choose Destination")
# Updated to use the correct '/m/' Google Flights Geo-IDs for regional searches
destination_map = {
    "All Spain": "/m/06crj",
    "All Mainland China": "/m/0d05w",
    "Hong Kong": "/m/0d0x0",
    "London": "/m/0d0x0" # Corrected for non-regional codes in future use
}

destination_label = st.selectbox(
    "Where to?",
    list(destination_map.keys())
)

st.subheader("2. Select Departure Window")
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Earliest Departure", datetime.date.today() + datetime.timedelta(days=60))
with col2:
    end_date = st.date_input("Latest Departure", datetime.date.today() + datetime.timedelta(days=90))

st.subheader("3. Approximate Stay Duration")
stay_days = st.slider("How many days do you want to stay?", min_value=7, max_value=21, value=14)

# --- DATE HELPER ---
def format_date(d):
    return d.strftime("%Y-%m-%d")

# --- THE CORRECT API CALL ---
def scan_cheapest(origin, destination_code, start, end, max_price_aud=2500):
    params = {
        "api_key": SERP_API_KEY,
        "engine": "google_flights",
        "departure_id": origin,
        "arrival_id": destination_code, # e.g. "/m/06crj" for Spain
        "outbound_date": format_date(start),
        "return_date": format_date(end),
        "type": "1",  # 1 = Round trip
        "cabin_class": "business",
        "currency": "AUD",
        "hl": "en",
        "gl": "au",
        "travelers": json.dumps([{"adults": 2}])  # <--- UPDATED TO 2 ADULTS
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=15)
        data = response.json()
        
        if "error" in data:
            st.error(f"❌ SerpApi Error: {data['error']}")
            return [], []

        all_prices = []
        deals = []

        if "best_flights" in data:
            for flight in data["best_flights"]:
                price = flight.get("price", 0)
                all_prices.append(price)
                
                if 500 < price < max_price_aud:
                    airline = flight["airlines"][0] if flight["airlines"] else "Unknown"
                    city_code = flight.get("departure_airport", {}).get("id", destination_code)
                    out_date = flight.get("departure_airport", {}).get("time", "")[:10]
                    ret_date = flight.get("return_airport", {}).get("time", "")[:10] if "return_airport" in flight else format_date(end)

                    deals.append({
                        "price": price,
                        "out_date": out_date,
                        "ret_date": ret_date,
                        "airline": airline,
                        "city": city_code,
                        "link": f"https://www.google.com/travel/flights?q=flights+{origin}+to+{city_code}+{format_date(start)}+{format_date(end)}"
                    })
        
        deals.sort(key=lambda x: x['price'])
        return deals[:3], all_prices
        
    except Exception as e:
        st.error(f"🔥 Critical Code Error: {e}")
        return [], []

# --- UI ---
st.write("---")
if st.button("🚀 FIND CHEAPEST FARES NOW"):
    # Look up the /m/ code based on the user's selection
    dest_code = destination_map[destination_label]
    
    with st.spinner("Scanning using correct Google Geo-IDs..."):
        found_deals, all_prices = scan_cheapest("SYD", dest_code, start_date, end_date)
        
        st.subheader(f"Results for SYD → {destination_label}")
        
        if all_prices:
            cheapest = min(all_prices)
            st.info(f"📊 **DEBUG:** The absolute cheapest fare found is **${cheapest} AUD**.")
        
        if found_deals:
            st.success("**Best Deals Found:**")
            for deal in found_deals:
                st.write("---")
                st.markdown(f"### ✈️ **${deal['price']} AUD** to **{deal['city']}**")
                st.write(f"**Airline:** {deal['airline']}")
                st.write(f"**Depart:** {deal['out_date']}  |  **Return:** {deal['ret_date']}")
                st.markdown(f"[🔗 Check & Book]({deal['link']})")
        else:
            if all_prices:
                st.warning(f"No glitches under $2,500. Cheapest was ${min(all_prices)}.")
            else:
                st.warning("No business class fares found in that exact window. Try expanding your dates.")
else:
    st.info("Use the controls above. This version correctly uses `/m/` regional codes for Spain and China to avoid API errors.")