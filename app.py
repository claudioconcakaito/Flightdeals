import streamlit as st
import requests
import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="SYD Business Fare Finder", layout="wide")
st.title("✈️ SYD Business Class Fare Finder")
st.caption("Finds the absolute cheapest round-trip fare within your chosen date window.")

# --- API CONFIG ---
SERP_API_KEY = st.secrets.get("SERP_API_KEY", "")
BASE_URL = "https://serpapi.com/search"

if not SERP_API_KEY:
    st.error("❌ SerpApi Key missing! Please add 'SERP_API_KEY' to your Streamlit secrets.")
    st.stop()

# --- USER INPUTS ---
st.subheader("1. Choose Your Route")
destination_choice = st.selectbox(
    "Where to?",
    ["All Spain (ES-Any)", "All Mainland China (CN-Any)", "Hong Kong (HKG)", "London (LHR)"]
)

st.subheader("2. Select Your Date Window")
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Earliest Departure", datetime.date.today() + datetime.timedelta(days=60))
with col2:
    end_date = st.date_input("Latest Departure", datetime.date.today() + datetime.timedelta(days=90))

# --- DATE HELPER ---
def format_date(d):
    return d.strftime("%Y-%m-%d")

# --- REVISED SCANNER (Flexible Date Window) ---
def scan_glitch(origin, destination, start, end, max_price_aud=2500):
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
        
        # Google returns an array of "best flights" for the window
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
        return deals[:5], all_prices
        
    except Exception as e:
        return [], []

# --- UI & MAIN SCAN BUTTON ---
if st.button("🚀 Scan for Cheapest Business Fares NOW"):
    st.write("---")
    
    # 1. Sanity Check (SYD to LHR)
    with st.spinner("Testing API connection..."):
        test_deals, test_prices = scan_glitch("SYD", "LHR", start_date, end_date)
        if test_prices:
            st.success(f"✅ **API ONLINE**. Test route (London) found fares starting at **${min(test_prices)} AUD**.")
        else:
            st.error("❌ Test failed. No fares found for London. Please check your date range.")
            st.stop()

    # 2. Real Scan (Strip labels to get code like ES-Any)
    dest_code = destination_choice.split(" ")[-1].replace("(", "").replace(")", "")
    
    with st.spinner(f"Checking SYD to {destination_choice} for your selected window..."):
        found_deals, all_prices = scan_glitch("SYD", dest_code, start_date, end_date)
        
        st.subheader(f"Results for SYD → {destination_choice}")
        
        if all_prices:
            cheapest = min(all_prices)
            st.info(f"📊 **DEBUG:** The cheapest fare Google found in your window is **${cheapest} AUD**.")
        
        if found_deals:
            st.success(f"**Best Business Class Deals Found:**")
            for deal in found_deals:
                st.write("---")
                st.markdown(f"### ✈️ **${deal['price']} AUD** to **{deal['city']}**")
                st.write(f"**Airline:** {deal['airline']}")
                st.write(f"**Depart:** {deal['out_date']}  |  **Return:** {deal['return_date']}")
                st.markdown(f"[🔗 Check & Book on Google Flights]({deal['link']})")
        else:
            if all_prices:
                st.warning(f"No deals under $2,500. The cheapest fare found was ${min(all_prices)}.")
            else:
                st.warning(f"No business class fares found in that date range. Try expanding your window.")
else:
    st.info("Select dates and a route, then click Scan.")
