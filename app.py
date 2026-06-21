import streamlit as st
import requests
import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="SYD Business Scanner", layout="wide")
st.title("✈️ SYD -> Spain/China (Business Class)")
st.caption("Scans Skyscanner for deals under $2,500 AUD")

# --- API CONFIG ---
RAPIDAPI_KEY = st.secrets.get("RAPIDAPI_KEY", "")
HOST = "skyscanner-flights.p.rapidapi.com"  # <--- UPDATED HOST HERE

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
debug_mode = st.sidebar.checkbox("Show Debug Info (Raw API Response)")

# --- GLITCH SCANNER FUNCTION ---
def scan_glitch(origin, destination, max_price_aud=2500):
    today = datetime.date.today()
    date_from = (today + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
    date_to = (today + datetime.timedelta(days=180)).strftime("%Y-%m-%d")

    url = "https://skyscanner-flights.p.rapidapi.com/flights/search-roundtrip"
    
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
        
        if response.status_code != 200:
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
    st.info("Click the button above to search.")
