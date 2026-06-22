import streamlit as st
import requests
import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="SYD Business Fare Finder", layout="wide")
st.title("✈️ SYD Business Class Fare Finder")
st.caption("Find the cheapest Business Class round-trip for your specific travel dates.")

# --- API CONFIG ---
SERP_API_KEY = st.secrets.get("SERP_API_KEY", "")
BASE_URL = "https://serpapi.com/search"

if not SERP_API_KEY:
    st.error("❌ SerpApi Key missing! Please add 'SERP_API_KEY' to your Streamlit secrets.")
    st.stop()

# --- USER INPUTS ---
st.sidebar.header("1️⃣ Choose Your Route")
destination_choice = st.sidebar.selectbox(
    "Where to?",
    ["All Spain (ES-Any)", "All Mainland China (CN-Any)", "Hong Kong (HKG)", "London (LHR)"]
)

st.sidebar.header("2️⃣ Select Your Dates")
start_date = st.sidebar.date_input("Earliest Departure", datetime.date.today() + datetime.timedelta(days=60))
end_date = st.sidebar.date_input("Latest Departure", datetime.date.today() + datetime.timedelta(days=90))

# --- DATE HELPER ---
def format_date(d):
    return d.strftime("%Y-%m-%d")

# --- SCANNER FUNCTION ---
def scan_glitch(origin, destination, start, end, max_price_aud=2500):
    # Check 3 specific dates within the user's chosen range
    check_dates = [
        start,
        start + datetime.timedelta(days=(end - start).days // 2),
        end
    ]

    all_deals = []
    all_prices = []

    for out_date in check_dates:
        ret_date = out_date + datetime.timedelta(days=14)
        
        params = {
            "api_key": SERP_API_KEY,
            "engine": "google_flights",
            "departure_id": origin,
            "arrival_id": destination,
            "outbound_date": format_date(out_date),
            "return_date": format_date(ret_date),
            "type": "1",
            "cabin_class": "business",
            "currency": "AUD",
            "hl": "en",
            "gl": "au"
        }

        try:
            response = requests.get(BASE_URL, params=params, timeout=10)
            data = response.json()
            
            if "best_flights" in data:
                for flight in data["best_flights"]:
                    price = flight.get("price", 0)
                    all_prices.append(price)
                    
                    if 500 < price < max_price_aud:
                        airline = flight["airlines"][0] if flight["airlines"] else "Unknown"
                        
                        # Extract the exact city airport code (e.g. MAD, BCN, PVG)
                        try:
                            city_code = flight["departure_airport"]["id"]
                        except:
                            city_code = destination

                        all_deals.append({
                            "price": price,
                            "out_date": format_date(out_date),
                            "ret_date": format_date(ret_date),
                            "airline": airline,
                            "city": city_code,
                            "link": f"https://www.google.com/travel/flights?q=flights+{origin}+to+{city_code}+{format_date(out_date)}+{format_date(ret_date)}"
                        })
        except:
            continue

    # Sort by absolute cheapest price
    all_deals.sort(key=lambda x: x['price'])
    return all_deals[:5], all_prices

# --- UI & MAIN SCAN BUTTON ---
if st.button("🚀 Scan for Cheapest Business Fares NOW"):
    st.write("---")
    
    # 1. Sanity Check (Test the API)
    with st.spinner("Connecting to Google Flights..."):
        test_deals, test_prices = scan_glitch("SYD", "LHR", start_date, end_date)
        if test_prices:
            st.success(f"✅ **API ONLINE**. Test route (London) found fares starting at **${min(test_prices)} AUD**.")
        else:
            st.error("❌ Test failed. API may be down or key expired.")
            st.stop()

    # 2. Real Scan (Strip the label to get the code like ES-Any or CN-Any)
    dest_code = destination_choice.split(" ")[-1].replace("(", "").replace(")", "")
    
    with st.spinner(f"Checking SYD to {destination_choice} for your selected dates..."):
        found_deals, all_prices = scan_glitch("SYD", dest_code, start_date, end_date)
        
        st.subheader(f"Results for SYD → {destination_choice}")
        
        # Show debug info so you know it's working
        if all_prices:
            cheapest = min(all_prices)
            st.info(f"📊 **Current Lowest Price Found:** **${cheapest} AUD**")
        
        # Show real deals
        if found_deals:
            st.success(f"**Best Business Class Deals:**")
            for deal in found_deals:
                st.write("---")
                st.markdown(f"### ✈️ **${deal['price']} AUD** to **{deal['city']}**")
                st.write(f"**Airline:** {deal['airline']}")
                st.write(f"**Depart:** {deal['out_date']}  |  **Return:** {deal['ret_date']}")
                st.markdown(f"[🔗 Check & Book on Google Flights]({deal['link']})")
        else:
            if all_prices:
                st.warning(f"No deals under $2,500. The cheapest fare found was ${min(all_prices)}.")
            else:
                st.warning(f"No business class fares found for those exact dates. Try expanding your date range.")
else:
    st.info("Use the sidebar to set your route and date range, then click Scan.")
