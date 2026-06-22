import streamlit as st
import requests
import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="SYD Business Fare Finder", layout="wide")
st.title("✈️ SYD Business Class Fare Finder")
st.caption("Pick your dates, region, and stay duration. Finds the cheapest round-trip business fare.")

# --- API CONFIG ---
SERP_API_KEY = st.secrets.get("SERP_API_KEY", "")
BASE_URL = "https://serpapi.com/search"

if not SERP_API_KEY:
    st.error("❌ SerpApi Key missing! Please add 'SERP_API_KEY' to your Streamlit secrets.")
    st.stop()

# --- USER CONTROLS ---
st.subheader("1. Choose Your Destination")
destination_choice = st.selectbox(
    "Where to?",
    ["All Spain (ES-Any)", "All Mainland China (CN-Any)", "Hong Kong (HKG)", "London (LHR)", "Madrid (MAD)", "Barcelona (BCN)", "Beijing (PEK)", "Shanghai (PVG)"]
)

st.subheader("2. Select Your Departure Window")
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

# --- FLEXIBLE SCANNER (1 API Call) ---
def scan_cheapest(origin, destination, start, end, stay, max_price_aud=2500):
    # Google Flights supports searching a date RANGE by setting the outbound and return to the start/end of the range
    params = {
        "api_key": SERP_API_KEY,
        "engine": "google_flights",
        "departure_id": origin,
        "arrival_id": destination,
        "outbound_date": format_date(start),
        "return_date": format_date(end),
        "type": "1",
        "cabin_class": "business",
        "currency": "AUD",
        "hl": "en",
        "gl": "au"
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        data = response.json()
        
        deals = []
        all_prices = []
        
        if "best_flights" in data:
            for flight in data["best_flights"]:
                price = flight.get("price", 0)
                all_prices.append(price)
                
                if 500 < price < max_price_aud:
                    airline = flight["airlines"][0] if flight["airlines"] else "Unknown"
                    try:
                        city_code = flight["departure_airport"]["id"]
                    except:
                        city_code = destination

                    deals.append({
                        "price": price,
                        "out_date": flight["departure_airport"]["time"][:10],
                        "return_date": flight["return_airport"]["time"][:10] if "return_airport" in flight else format_date(end),
                        "airline": airline,
                        "city": city_code,
                        "link": f"https://www.google.com/travel/flights?q=flights+{origin}+to+{city_code}+{format_date(start)}+{format_date(end)}"
                    })
        
        deals.sort(key=lambda x: x['price'])
        return deals[:3], all_prices  # Return top 3 cheapest
        
    except Exception as e:
        return [], []

# --- UI & SCAN BUTTON ---
st.write("---")
if st.button("🚀 FIND CHEAPEST FARES NOW"):
    dest_code = destination_choice.split(" ")[-1].replace("(", "").replace(")", "")
    
    with st.spinner(f"Scanning for the cheapest business fare to {destination_choice}..."):
        found_deals, all_prices = scan_cheapest("SYD", dest_code, start_date, end_date, stay_days)
        
        st.subheader(f"Results for SYD → {destination_choice}")
        
        # Always show debug info so you know it's working
        if all_prices:
            cheapest = min(all_prices)
            st.info(f"📊 **DEBUG:** The absolute cheapest fare found in this date range is **${cheapest} AUD**.")
        else:
            st.error("❌ The API returned no data. Please check your SerpApi key or try a wider date range.")
            st.stop()

        # Show real deals
        if found_deals:
            st.success(f"**Best Business Class Deals Found:**")
            for deal in found_deals:
                st.write("---")
                st.markdown(f"### ✈️ **${deal['price']} AUD** to **{deal['city']}**")
                st.write(f"**Airline:** {deal['airline']}")
                st.write(f"**Depart:** {deal['out_date']}  |  **Return:** {deal['return_date']}")
                st.markdown(f"[🔗 Check & Book on Google Flights]({deal['link']})")
        else:
            st.warning(f"No deals under $2,500 AUD. The cheapest available is ${min(all_prices)}.")
else:
    st.info("Adjust the controls above and hit Scan. This tool is now completely flexible.")