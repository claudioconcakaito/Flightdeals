import streamlit as st
import requests
import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="SYD Business Scanner", layout="wide")
st.title("✈️ SYD -> Spain/China (Business Class)")
st.caption("Scans Skyscanner for deals under $2,500 AUD")

# --- API CONFIG ---
RAPIDAPI_KEY = st.secrets.get("RAPIDAPI_KEY", "")
HOST = "skyscanner80.p.rapidapi.com"

if not RAPIDAPI_KEY:
    st.error("❌ API Key missing! Please add 'RAPIDAPI_KEY' to your Streamlit secrets.")
    st.stop()

# --- ROUTES ---
ROUTES = {
    "Spain (Any City)": "ES", 
    "China (Any City)": "CN"   
}

# --- DEBUGGING TOGGLE (Add this to the sidebar) ---
st.sidebar.header("🛠️ Debug Panel")
debug_mode = st.sidebar.checkbox("Show Debug Info (Cheapest price found)")
test_mode = st.sidebar.checkbox("Force Test Deal ($99 Fake)")

# --- GLITCH SCANNER FUNCTION ---
def scan_glitch(origin, destination, max_price_aud=2500):
    today = datetime.date.today()
    date_from = (today + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
    date_to = (today + datetime.timedelta(days=180)).strftime("%Y-%m-%d")

    url = "https://skyscanner80.p.rapidapi.com/flights/search-roundtrip"
    
    querystring = {
        "fromId": origin,
        "toId": destination,
        "fromDate": date_from,
        "toDate": date_to,
        "cabinClass": "business",
        "adults": "1",
        "currency": "AUD",
        "market": "AU",
        "locale": "en-AU"
    }

    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": HOST
    }

    try:
        response = requests.get(url, headers=headers, params=querystring)
        data = response.json()
        
        deals = []
        all_prices = [] # Store all prices for debug mode
        
        if 'itineraries' in data:
            for flight in data['itineraries']:
                price = flight.get('price', {}).get('amount', 0)
                all_prices.append(price)
                
                if 500 < price < max_price_aud:
                    dest_airport = flight.get('segments', [{}])[0].get('destination', {}).get('id', destination)
                    date_str = flight.get('outbound', {}).get('departure', '')[:10]
                    link = f"https://www.google.com/travel/flights?q=flights+{origin}+to+{dest_airport}+{date_str}+business"
                    
                    deals.append({
                        "price": price,
                        "date": date_str,
                        "airline": flight.get('segments', [{}])[0].get('marketingCarrier', 'Unknown'),
                        "city": dest_airport,
                        "link": link
                    })
        
        deals.sort(key=lambda x: x['price'])
        return deals[:10], all_prices

    except Exception as e:
        st.error(f"API Error: {e}")
        return [], []

# --- UI ---
if st.button("🚀 Scan for Glitch Fares NOW"):
    st.write("---")
    for route_name, country_code in ROUTES.items():
        st.subheader(f"🔍 SYD to {route_name}")
        with st.spinner(f"Checking prices across all airports..."):
            found_deals, all_prices = scan_glitch("SYD", country_code)
            
            # --- DEBUG SECTION ---
            if debug_mode and all_prices:
                cheapest = min(all_prices)
                st.info(f"📊 **Debug:** The cheapest Business fare the API saw was **${cheapest} AUD**. If this is over $2,500, there are no glitches right now.")
            
            # --- TEST MODE SECTION ---
            if test_mode:
                st.warning("🧪 TEST MODE ACTIVE: Showing a fake $99 deal to prove the app works!")
                st.success(f"💰 **$99 AUD** to **MAD (Test)** on {datetime.date.today()} (Test Airline)")
                st.markdown(f"[🔗 Book on Google Flights](https://www.google.com/travel/flights)")
                
            # --- REAL RESULTS ---
            elif found_deals:
                st.success(f"**Top Deals Found:**")
                for deal in found_deals:
                    st.success(f"💰 **${deal['price']} AUD** to **{deal['city']}** on {deal['date']} ({deal['airline']})")
                    st.markdown(f"[🔗 Book on Google Flights]({deal['link']})")
            else:
                st.warning(f"No business class deals under $2,500 AUD to {route_name} found.")
                
    st.write("---")
    st.caption("If Debug mode shows a price > $2,500, come back tomorrow!")
else:
    st.info("Click the button above to search. Use the sidebar to toggle Debug/Test modes.")
