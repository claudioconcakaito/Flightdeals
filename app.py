import streamlit as st
import requests
import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="SYD Business Glitch Scanner", layout="wide")
st.title("✈️ SYD -> Spain/China Business Class Glitch Finder")
st.caption("Scans Skyscanner for business class deals under $2,500 AUD")

# --- API CONFIG ---
# You will store this key in Streamlit Cloud "Secrets" (instructions below)
RAPIDAPI_KEY = st.secrets.get("RAPIDAPI_KEY", "")
HOST = "skyscanner80.p.rapidapi.com"

if not RAPIDAPI_KEY:
    st.error("❌ API Key missing! Please add 'RAPIDAPI_KEY' to your Streamlit secrets.")
    st.stop()

# --- ROUTES ---
ROUTES = {
    "Spain (Barcelona)": "BCN",
    "China (Beijing)": "PEK"
}

# --- GLITCH SCANNER FUNCTION ---
def scan_glitch(origin, destination, max_price_aud=2500):
    # Search dates from 30 days to 180 days from now
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
        
        # Parse the response
        if 'itineraries' in data:
            for flight in data['itineraries']:
                price = flight.get('price', {}).get('amount', 0)
                
                # FILTER: Must be above $500 (kills economy spam) and below max_price
                if 500 < price < max_price_aud:
                    # Build a Google Flights link for easy booking
                    date_str = flight.get('outbound', {}).get('departure', '')[:10]
                    link = f"https://www.google.com/travel/flights?q=flights+{origin}+to+{destination}+{date_str}+business"
                    
                    deals.append({
                        "price": price,
                        "date": date_str,
                        "airline": flight.get('segments', [{}])[0].get('marketingCarrier', 'Unknown'),
                        "link": link
                    })
        
        # Sort by cheapest price first
        deals.sort(key=lambda x: x['price'])
        return deals[:5]  # Return only the top 5 cheapest

    except Exception as e:
        st.error(f"API Error: {e}")
        return []

# --- UI ---
if st.button("🚀 Scan for Glitch Fares NOW"):
    st.write("---")
    for route_name, dest_code in ROUTES.items():
        st.subheader(f"🔍 SYD to {route_name}")
        with st.spinner(f"Checking prices from 1 month to 6 months out..."):
            found_deals = scan_glitch("SYD", dest_code)
            
            if found_deals:
                for deal in found_deals:
                    st.success(f"💰 **${deal['price']} AUD** - {deal['date']} on {deal['airline']}")
                    st.markdown(f"[🔗 Book on Google Flights]({deal['link']})")
            else:
                st.warning(f"No business class deals under $2,500 AUD found for this route right now.")
    st.write("---")
    st.caption("Glitch fares vanish fast. Book immediately if you see one!")
else:
    st.info("Click the button above to search for deals across the next 6 months.")