import streamlit as st
import requests
import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="SYD Business Scanner", layout="wide")
st.title("✈️ SYD -> Europe & China (Target Dates)")
st.caption("Scans exact dates ±3 days to find the absolute lowest Round-Trip Business fare.")

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

# --- TARGET DATES (August 28 to September 12) ---
# You can change these to whatever dates you want.
TARGET_START = datetime.date(2026, 8, 28)
TARGET_END = datetime.date(2026, 9, 12)

# --- DATE HELPER ---
def format_date(d):
    return d.strftime("%Y-%m-%d")

# --- TARGET DATE SCANNER ---
def scan_glitch(origin, destination, max_price_aud=2500):
    all_deals = []
    all_prices = []

    # Step 1: Generate all departure dates in our target range
    delta = TARGET_END - TARGET_START
    for i in range(delta.days + 1):
        out_date = TARGET_START + datetime.timedelta(days=i)
        
        # Step 2: For each departure, check returns -3 to +3 days
        for j in range(-3, 4): # -3, -2, -1, 0, 1, 2, 3
            ret_date = out_date + datetime.timedelta(days=j)
            
            # Ensure return is after departure
            if ret_date <= out_date:
                continue

            # Step 3: Call the API for this specific date pair
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
                response = requests.get(BASE_URL, params=params)
                data = response.json()
                
                if "best_flights" in data:
                    for flight in data["best_flights"]:
                        price = flight.get("price", 0)
                        all_prices.append(price)
                        
                        if 500 < price < max_price_aud:
                            try:
                                destination_code = flight["departure_airport"]["id"]
                            except:
                                destination_code = destination
                                
                            link = f"https://www.google.com/travel/flights?q=flights+{origin}+to+{destination_code}+{format_date(out_date)}+{format_date(ret_date)}"
                            
                            all_deals.append({
                                "price": price,
                                "out_date": format_date(out_date),
                                "ret_date": format_date(ret_date),
                                "airline": flight["airlines"][0],
                                "city": destination_code,
                                "link": link
                            })
            except:
                # If one date fails (API limit etc), skip it silently
                continue
    
    # Sort by absolute cheapest price
    all_deals.sort(key=lambda x: x['price'])
    return all_deals[:5], all_prices

# --- UI ---
st.sidebar.header("📅 Date Settings")
st.sidebar.write(f"**Checking:** {TARGET_START.strftime('%b %d')} to {TARGET_END.strftime('%b %d, %Y')}")
st.sidebar.write(f"**Flexibility:** ±3 days on return")

if st.button("🚀 Scan Target Dates NOW"):
    st.write("---")
    
    # --- SANITY CHECK (SYD to LHR) ---
    with st.spinner("Running system test..."):
        test_deals, test_prices = scan_glitch("SYD", "LHR")
        if test_prices:
            cheapest_test = min(test_prices)
            st.success(f"✅ **SYSTEM ONLINE.** Test returned **${cheapest_test} AUD**. Key is working!")
        else:
            st.error("❌ **SYSTEM ERROR.** Test route failed. Please check your SerpApi key.")
            st.stop()

    # --- REAL SCANS ---
    st.warning("⚠️ Scanning multiple date combinations may use several API calls. Please wait...")
    for route_name, airport_code in ROUTES.items():
        st.subheader(f"🔍 SYD to {route_name}")
        with st.spinner(f"Scanning all date combinations..."):
            found_deals, all_prices = scan_glitch("SYD", airport_code)
            
            if all_prices:
                cheapest = min(all_prices)
                st.info(f"📊 **DEBUG:** The absolute cheapest Round-Trip fare found is **${cheapest} AUD**.")
            
            if found_deals:
                st.success(f"**Cheapest Round-Trip Deals Found:**")
                for deal in found_deals:
                    st.success(f"💰 **${deal['price']} AUD** to **{deal['city']}**")
                    st.write(f"   ➡️ Out: {deal['out_date']} | ↩️ Ret: {deal['ret_date']} ({deal['airline']})")
                    st.markdown(f"[🔗 Book on Google Flights]({deal['link']})")
            else:
                if all_prices:
                    st.warning(f"No glitches under $2,500. Cheapest was ${min(all_prices)}.")
                else:
                    st.warning(f"No round-trip deals found.")
    st.write("---")
else:
    st.info("Click the button above. It scans all date combinations in your target range.")