import streamlit as st
import requests
import datetime

st.set_page_config(page_title="SYD Business Scanner", layout="wide")
st.title("✈️ SYD -> Europe & China (Business Round-Trip)")
st.caption("Uses 1 API call per destination to find the absolute cheapest fare in the next 6 months.")

SERP_API_KEY = st.secrets.get("SERP_API_KEY", "")
BASE_URL = "https://serpapi.com/search"

if not SERP_API_KEY:
    st.error("❌ SerpApi Key missing! Please add 'SERP_API_KEY' to your Streamlit secrets.")
    st.stop()

ROUTES = {
    "All Spain": "ES-Any",
    "All Mainland China": "CN-Any"
}

def scan_glitch(origin, destination, max_price_aud=2500):
    # Search 6 months from now
    outbound_date = (datetime.date.today() + datetime.timedelta(days=180)).strftime("%Y-%m-%d")
    return_date = (datetime.date.today() + datetime.timedelta(days=194)).strftime("%Y-%m-%d") # 14 days later

    params = {
        "api_key": SERP_API_KEY,
        "engine": "google_flights",
        "departure_id": origin,
        "arrival_id": destination,
        "outbound_date": outbound_date,
        "return_date": return_date,
        "type": "1",
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
                        "airline": flight["airlines"][0],
                        "city": destination_code,
                        "link": f"https://www.google.com/travel/flights?q=flights+{origin}+to+{destination_code}+{outbound_date}+{return_date}"
                    })
        
        deals.sort(key=lambda x: x['price'])
        return deals[:5], all_prices
        
    except Exception as e:
        return [], []

if st.button("🚀 Scan NOW"):
    st.write("---")
    
    with st.spinner("Running system test..."):
        test_deals, test_prices = scan_glitch("SYD", "LHR")
        if test_prices:
            cheapest_test = min(test_prices)
            st.success(f"✅ **SYSTEM ONLINE.** Test returned **${cheapest_test} AUD**.")
        else:
            st.error("❌ **SYSTEM ERROR.** Test route failed.")
            st.stop()

    for route_name, airport_code in ROUTES.items():
        st.subheader(f"🔍 SYD to {route_name}")
        with st.spinner(f"Scanning..."):
            found_deals, all_prices = scan_glitch("SYD", airport_code)
            
            if all_prices:
                cheapest = min(all_prices)
                st.info(f"📊 **DEBUG:** Lowest Round-Trip fare found is **${cheapest} AUD**.")
            
            if found_deals:
                st.success(f"**Cheapest Deal Found:**")
                for deal in found_deals:
                    st.success(f"💰 **${deal['price']} AUD** to **{deal['city']}** ({deal['airline']})")
                    st.markdown(f"[🔗 Book on Google Flights]({deal['link']})")
            else:
                if all_prices:
                    st.warning(f"No glitches under $2,500. Cheapest was ${min(all_prices)}.")
                else:
                    st.warning(f"No deals found.")
    st.write("---")
else:
    st.info("Click the button. Uses 3 API calls max. Instant results.")