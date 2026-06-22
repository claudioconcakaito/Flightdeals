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

# --- ROUTES ---
ROUTES = {
    "All Spain": "ES-Any",
    "All Mainland China": "CN-Any",
    "Hong Kong (HKG)": "HKG"
}

# --- SCANNER FUNCTION ---
def scan_glitch(origin, destination, max_price_aud=2500):
    future_date = (datetime.date.today() + datetime.timedelta(days=90)).strftime("%Y-%m-%d")
    params = {
        "api_key": SERP_API_KEY,
        "engine": "google_flights",
        "departure_id": origin,
        "arrival_id": destination,
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
                
                if 500 < price < max_price_aud:
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
        return deals, all_prices
        
    except Exception as e:
        return [], []

# --- UI ---
if st.button("🚀 Scan ALL Airports NOW"):
    st.write("---")
    
    # --- 1. THE SANITY CHECK (Testing the API) ---
    with st.spinner("Running system test..."):
        test_deals, test_prices = scan_glitch("SYD", "LON")
        if test_prices:
            cheapest_test = min(test_prices)
            st.success(f"✅ **SYSTEM ONLINE.** The test route (SYD->London) returned a price of **${cheapest_test} AUD**. Your app is alive!")
        else:
            st.error("❌ **SYSTEM ERROR.** The test route returned nothing. Your SerpApi key is either invalid, expired, or has hit its monthly limit. Please check your SerpApi dashboard.")
            st.stop()

    # --- 2. REAL SCANS ---
    for route_name, airport_code in ROUTES.items():
        st.subheader(f"🔍 SYD to {route_name}")
        with st.spinner(f"Scanning..."):
            found_deals, all_prices = scan_glitch("SYD", airport_code)
            
            # Debug block (now prints ALWAYS)
            if all_prices:
                cheapest = min(all_prices)
                st.info(f"📊 **DEBUG:** The lowest Business fare Google found for this route is **${cheapest} AUD**.")
            else:
                st.warning("⚠️ The API returned no data for this specific route.")
            
            # Real deals
            if found_deals:
                st.success(f"**Cheapest Deals Found:**")
                for deal in found_deals:
                    st.success(f"💰 **${deal['price']} AUD** to **{deal['city']}** on {deal['date']} ({deal['airline']})")
                    st.markdown(f"[🔗 Book on Google Flights]({deal['link']})")
            else:
                if all_prices:
                    st.warning(f"No glitches under $2,500. Cheapest was ${min(all_prices)}.")
                else:
                    st.warning(f"No deals found.")
    st.write("---")
else:
    st.info("Click the button above. The system will self-test first to guarantee the API is working.")