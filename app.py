import streamlit as st
import requests
import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="SYD Business Scanner", layout="wide")
st.title("✈️ SYD -> Europe & China (Business Class)")
st.caption("Scans ALL major airports for the absolute lowest Business fare")

# --- API CONFIG ---
SERP_API_KEY = st.secrets.get("SERP_API_KEY", "")
BASE_URL = "https://serpapi.com/search"

if not SERP_API_KEY:
    st.error("❌ SerpApi Key missing! Please add 'SERP_API_KEY' to your Streamlit secrets.")
    st.stop()

# --- ROUTES (Wide net) ---
# -iata:Any allows Google Flights to check every airport in that country/region
# HKG is included because it's a major international hub for cheap Aus flights
ROUTES = {
    "All Spain": "ES-Any",
    "All Mainland China": "CN-Any",
    "Hong Kong (HKG)": "HKG"
}

# --- GLITCH SCANNER ---
def scan_glitch(origin, destination, max_price_aud=2500):
    # Search 90 days from now
    future_date = (datetime.date.today() + datetime.timedelta(days=90)).strftime("%Y-%m-%d")

    params = {
        "api_key": SERP_API_KEY,
        "engine": "google_flights",
        "departure_id": origin,
        "arrival_id": destination, # e.g. "ES-Any", "CN-Any", "HKG"
        "outbound_date": future_date,
        "cabin_class": "business",
        "currency": "AUD",
        "hl": "en",
        "gl": "au"
    }

    try:
        response = requests.get(BASE_URL, params=params)
        data = response.json()
        
        deals = []
        all_prices = []
        
        if "best_flights" in data:
            for flight in data["best_flights"]:
                price = flight.get("price", 0)
                all_prices.append(price)
                
                # Show any Business fare above $500 (economy filter) and below max
                if 500 < price < max_price_aud:
                    # Get the exact city code the deal landed at (e.g., MAD, PVG)
                    try:
                        destination_code = flight["departure_airport"]["id"]
                    except:
                        destination_code = destination
                        
                    deals.append({
                        "price": price,
                        "date": flight["departure_airport"]["time"][:10],
                        "airline": flight["airlines"][0],
                        "city": destination_code,
                        "link": f"https://www.google.com/travel/flights?q=flights+{origin}+to+{destination_code}+{future_date}"
                    })
        
        deals.sort(key=lambda x: x['price'])
        return deals[:5], all_prices
        
    except Exception as e:
        return [], []

# --- UI ---
st.sidebar.header("🛠️ Debug")
debug_mode = st.sidebar.checkbox("Show Absolute Cheapest Price")

if st.button("🚀 Scan ALL Airports NOW"):
    st.write("---")
    for route_name, airport_code in ROUTES.items():
        st.subheader(f"🔍 SYD to {route_name}")
        with st.spinner(f"Scanning every airport in this region..."):
            found_deals, all_prices = scan_glitch("SYD", airport_code)
            
            if debug_mode and all_prices:
                cheapest = min(all_prices)
                st.info(f"📊 **Debug:** Absolute cheapest fare found was **${cheapest} AUD**.")
            
            if found_deals:
                st.success(f"**Cheapest Deals Found:**")
                for deal in found_deals:
                    st.success(f"💰 **${deal['price']} AUD** to **{deal['city']}** on {deal['date']} ({deal['airline']})")
                    st.markdown(f"[🔗 Book on Google Flights]({deal['link']})")
            else:
                if debug_mode and all_prices:
                    st.warning(f"Cheapest was ${min(all_prices)}. No deals under $2,500.")
                else:
                    st.warning(f"No deals under $2,500 AUD found.")
    st.write("---")
else:
    st.info("Click the button above. Turn on 'Debug' in the sidebar to see the absolute lowest price, even if it's expensive.")