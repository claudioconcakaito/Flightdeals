import streamlit as st
import requests
import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="SYD Business Scanner", layout="wide")
st.title("✈️ SYD -> Spain/China (Business Class)")
st.caption("Scans Skyscanner for business class deals under $2,500 AUD")

# --- API CONFIG ---
RAPIDAPI_KEY = st.secrets.get("RAPIDAPI_KEY", "")
HOST = "skyscanner-flights.p.rapidapi.com"

if not RAPIDAPI_KEY:
    st.error("❌ API Key missing! Please add 'RAPIDAPI_KEY' to your Streamlit secrets.")
    st.stop()

# --- ROUTES ---
ROUTES = {
    "Spain (Barcelona)": "BCN",
    "Spain (Madrid)": "MAD",
    "China (Beijing)": "PEK",
    "China (Shanghai)": "PVG"
}

# --- DEBUGGING TOGGLE ---
st.sidebar.header("🛠️ Debug Panel")
debug_mode = st.sidebar.checkbox("Show Debug Info")

# --- GLITCH SCANNER FUNCTION (UPDATED FOR ONE-WAY) ---
def scan_glitch(origin, destination, max_price_aud=2500):
    today = datetime.date.today()
    # We look at dates 60 days from now (more reliable for API)
    check_date = (today + datetime.timedelta(days=60)).strftime("%Y-%m-%d")

    # CHANGED TO ONE-WAY (roundtrip was causing 404s)
    url = "https://skyscanner-flights.p.rapidapi.com/flights/search-one-way"
    
    querystring = {
        "fromId": origin,
        "toId": destination,
        "date": check_date,
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
        
        if response.status_code != 200:
            # If blocked by 429, show a friendly message instead of crashing
            if response.status_code == 429:
                st.warning("⏳ API limit reached. Wait 1 hour and try again.")
                return [], []
            st.error(f"🚨 API Error! Status Code: {response.status_code}.")
            return [], []

        data = response.json()
        
        deals = []
        all_prices = []
        
        if 'itineraries' in data:
            for flight in data['itineraries']:
                price = flight.get('price', {}).get('amount', 0)
                all_prices.append(price)
                
                if 500 < price < max_price_aud:
                    dest_airport = flight.get('segments', [{}])[0].get('destination', {}).get('id', destination)
                    link = f"https://www.google.com/travel/flights?q=flights+{origin}+to+{dest_airport}+{check_date}+business"
                    
                    deals.append({
                        "price": price,
                        "date": check_date,
                        "airline": flight.get('segments', [{}])[0].get('marketingCarrier', 'Unknown'),
                        "city": dest_airport,
                        "link": link
                    })
        
        deals.sort(key=lambda x: x['price'])
        return deals[:10], all_prices

    except Exception as e:
        st.error(f"🔥 Code Crash: {e}")
        return [], []

# --- UI ---
if st.button("🚀 Scan for Glitch Fares NOW"):
    st.write("---")
    for route_name, airport_code in ROUTES.items():
        st.subheader(f"🔍 SYD to {route_name}")
        with st.spinner(f"Checking prices..."):
            found_deals, all_prices = scan_glitch("SYD", airport_code)
            
            if debug_mode and all_prices:
                cheapest = min(all_prices)
                st.info(f"📊 **Debug:** Cheapest Business fare was **${cheapest} AUD**.")
            
            if found_deals:
                st.success(f"**Top Deals Found:**")
                for deal in found_deals:
                    st.success(f"💰 **${deal['price']} AUD** to **{deal['city']}** on {deal['date']} ({deal['airline']})")
                    st.markdown(f"[🔗 Book on Google Flights]({deal['link']})")
            else:
                st.warning(f"No business class deals under $2,500 AUD to {route_name} found.")
                
    st.write("---")
else:
    st.info("Click the button above to search. (If you get a 429 error, wait 1 hour for the API to reset).")
