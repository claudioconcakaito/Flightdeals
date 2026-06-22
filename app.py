import streamlit as st
import requests
import datetime
import json

# --- PAGE CONFIG ---
st.set_page_config(page_title="SYD Business Fare Finder", layout="wide")
st.title("✈️ SYD Business Class Fare Finder")
st.caption("Finally fixed. Finds the cheapest round-trip business fare for your dates.")

# --- API CONFIG ---
SERP_API_KEY = st.secrets.get("SERP_API_KEY", "")
BASE_URL = "https://serpapi.com/search"

if not SERP_API_KEY:
    st.error("❌ SerpApi Key missing! Please add 'SERP_API_KEY' to your Streamlit secrets.")
    st.stop()

# --- USER CONTROLS ---
st.subheader("1. Choose Destination")
destination_choice = st.selectbox(
    "Where to?",
    ["All Spain (ES-Any)", "All Mainland China (CN-Any)", "Hong Kong (HKG)", "London (LHR)"]
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
def scan_cheapest(origin, destination, start, end, stay, max_price_aud=2500):
    params = {
        "api_key": SERP_API_KEY,
        "engine": "google_flights",
        "departure_id": origin,
        "arrival_id": destination,
        "outbound_date": format_date(start),
        "return_date": format_date(end),
        "type": "1",  # 1 = Round trip
        "cabin_class": "business",
        "currency": "AUD",
        "hl": "en",
        "gl": "au",
        "travelers": json.dumps([{"adults": 1}])  # <--- THE CRITICAL FIX
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=15)
        data = response.json()
        
        # --- CATCH SERPAPI ERRORS DIRECTLY ---
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
                    city_code = flight.get("departure_airport", {}).get("id", destination)
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
    dest_code = destination_choice.split(" ")[-1].replace("(", "").replace(")", "")
    
    with st.spinner("Scanning..."):
        found_deals, all_prices = scan_cheapest("SYD", dest_code, start_date, end_date, stay_days)
        
        st.subheader(f"Results for SYD → {destination_choice}")
        
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
                st.error("The API returned 0 results. Try widening your date window.")
else:
    st.info("Hit Scan. If it fails, it will show the exact SerpApi error.")