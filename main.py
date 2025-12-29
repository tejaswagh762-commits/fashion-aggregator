import streamlit as st
from serpapi import GoogleSearch
import re
import pandas as pd

# --- CONFIG ---
# Using your provided API key
API_KEY = "fa0a9b0d2df08ac4b30b7ce86024abece4671522276eade67918f0c47306ce95"

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Fashion Finder | AI-Powered Shopping",
    page_icon="👕",
    layout="wide"
)

# Initialize session state
if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'search_performed' not in st.session_state:
    st.session_state.search_performed = False

# --- SIDEBAR ---
st.sidebar.header("🔍 Filter Your Style")

gender = st.sidebar.selectbox("Gender", ["Men", "Women"])

MEN_CATEGORIES = [
    "Shirt", "Formal Shirt", "Casual Shirt",
    "T-Shirt", "Polo T-Shirt",
    "Jeans", "Chinos", "Trousers",
    "Jacket", "Hoodie", "Sweater", "Blazer"
]

WOMEN_CATEGORIES = [
    "Top", "T-Shirt", "Kurti",
    "Dress", "Jeans", "Skirt",
    "Palazzo", "Jacket", "Hoodie",
    "Lehenga", "Saree"
]

category = st.sidebar.selectbox(
    "Category",
    MEN_CATEGORIES if gender == "Men" else WOMEN_CATEGORIES
)

color = st.sidebar.selectbox(
    "Color", ["Any", "Black", "White", "Blue", "Beige", "Green", "Grey", "Red", "Pink"]
)

price_range = st.sidebar.slider(
    "Budget (₹)", 199, 20000, (499, 3000), step=100
)

# Sort options
sort_by = st.sidebar.selectbox(
    "Sort by",
    ["Price: Low to High", "Price: High to Low", "Best Match"]
)

search_button = st.sidebar.button("🚀 Find Best Deals", type="primary", use_container_width=True)

# --- MAIN AREA ---
st.title("🛍️ AI Fashion Aggregator")
st.markdown("*Discover the best fashion deals across the web*")

# Display welcome message when no search performed
if not st.session_state.search_performed:
    col1, col2 = st.columns(2)
    with col1:
        st.info("""
        **🎯 How it works:**
        1. Select your preferences in the sidebar
        2. Click 'Find Best Deals'
        3. Browse curated fashion products
        4. Click 'Buy Now' to purchase
        """)
    with col2:
        st.info("""
        **💡 Tips for better results:**
        • Be specific with categories
        • Use broad color selections
        • Adjust price range as needed
        • Try different sort options
        """)

# --- HELPER FUNCTIONS ---
def extract_price(price_text):
    """Extract numeric price from text"""
    if not price_text:
        return None
    match = re.search(r'[\d,]+\.?\d*', str(price_text))
    if match:
        try:
            return int(float(match.group().replace(',', '')))
        except:
            return None
    return None

def normalize_url(url):
    """Ensure URL is properly formatted"""
    if not url:
        return None
    
    url = str(url).strip()
    
    if url.startswith("//"):
        url = "https:" + url
    elif not url.startswith(("http://", "https://")):
        url = "https://" + url
    
    return url

def get_buy_link(item):
    """Extract the best available purchase link"""
    link_keys = ["product_link", "merchant_link", "offers_link", "link", "source_link"]
    
    for key in link_keys:
        url = normalize_url(item.get(key))
        if url:
            return url
    
    # Try to construct from product_id
    product_id = item.get("product_id")
    if product_id:
        return f"https://www.google.com/shopping/product/{product_id}"
    
    return None

# --- SEARCH FUNCTION ---
def perform_search(query, min_price, max_price):
    """Perform the search and return processed results"""
    try:
        params = {
            "engine": "google_shopping",
            "q": query,
            "gl": "in",
            "hl": "en",
            "google_domain": "google.co.in",
            "num": 50,  # Get 50 results for better filtering
            "api_key": API_KEY,
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        if "error" in results:
            st.error(f"API Error: {results['error']}")
            return []
        
        items = results.get("shopping_results", [])
        
        # Process and filter items
        processed_items = []
        for item in items:
            price_val = extract_price(item.get("price"))
            link = get_buy_link(item)
            
            # Skip items without price or link
            if not price_val or not link:
                continue
            
            # Apply price filter
            if price_val < min_price or price_val > max_price:
                continue
            
            # Skip items without thumbnail
            if not item.get("thumbnail"):
                continue
            
            processed_item = {
                "title": item.get("title", "Product")[:80],
                "price": price_val,
                "formatted_price": item.get("price", "Price on site"),
                "link": link,
                "thumbnail": item.get("thumbnail"),
                "source": item.get("source", "Unknown Store"),
                "rating": item.get("rating"),
                "reviews": item.get("reviews"),
                "price_value": price_val
            }
            
            processed_items.append(processed_item)
        
        return processed_items
        
    except Exception as e:
        st.error(f"Search failed: {str(e)}")
        return []

# --- MAIN SEARCH LOGIC ---
if search_button:
    with st.spinner("🔍 Searching across 1000+ stores..."):
        # Build query
        query_parts = [gender, category]
        if color != "Any":
            query_parts.append(color)
        query = " ".join(query_parts)
        
        min_price, max_price = price_range
        
        # Perform search
        results = perform_search(query, min_price, max_price)
        
        # Sort results
        if sort_by == "Price: Low to High":
            results.sort(key=lambda x: x["price_value"])
        elif sort_by == "Price: High to Low":
            results.sort(key=lambda x: x["price_value"], reverse=True)
        
        # Store in session state
        st.session_state.search_results = results
        st.session_state.search_performed = True

# --- DISPLAY RESULTS ---
if st.session_state.search_performed and st.session_state.search_results:
    results = st.session_state.search_results
    
    # Results header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.success(f"🎯 Found {len(results)} products matching your criteria")
    with col2:
        if results:
            avg_price = sum(r["price_value"] for r in results) / len(results)
            st.metric("Average Price", f"₹{int(avg_price):,}")
    
    # Display products in 5-column grid
    cols_per_row = 5
    for i in range(0, len(results), cols_per_row):
        cols = st.columns(cols_per_row)
        row_items = results[i:i + cols_per_row]
        
        for col_idx, item in enumerate(row_items):
            with cols[col_idx]:
                # Product card container
                with st.container(border=True):
                    # Product image
                    st.image(
                        item["thumbnail"],
                        use_container_width=True
                    )
                    
                    # Store name
                    st.markdown(f"<small>{item['source']}</small>", unsafe_allow_html=True)
                    
                    # Product title
                    st.markdown(f"**{item['title']}**")
                    
                    # Price
                    st.markdown(f"<b>₹{item['price']:,}</b>", unsafe_allow_html=True)
                    
                    # Rating if available
                    if item.get("rating"):
                        st.caption(f"⭐ {item['rating']}")
                    
                    # Buy button
                    st.link_button(
                        "🛒 Buy Now",
                        item["link"],
                        use_container_width=True,
                        help=f"Buy from {item['source']}"
                    )
    
    # Summary section
    if results:
        with st.expander("📊 Search Summary", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                min_price = min(r["price_value"] for r in results)
                max_price = max(r["price_value"] for r in results)
                st.metric("Price Range", f"₹{min_price:,} - ₹{max_price:,}")
            
            with col2:
                stores = len(set(r["source"] for r in results))
                st.metric("Stores Found", stores)
            
            with col3:
                total_value = sum(r["price_value"] for r in results)
                st.metric("Total Value", f"₹{total_value:,}")
            
            # Export button
            if results:
                st.download_button(
                    label="📥 Export Results to CSV",
                    data=pd.DataFrame(results).to_csv(index=False),
                    file_name="fashion_finder_results.csv",
                    mime="text/csv",
                    use_container_width=True
                )

elif st.session_state.search_performed and not st.session_state.search_results:
    st.warning("No products found. Try adjusting your filters.")
    col1, col2 = st.columns(2)
    with col1:
        st.info("**Suggestions:**")
        st.write("• Widen your price range")
        st.write("• Try different color")
        st.write("• Use more general category")
    with col2:
        st.info("**Popular searches:**")
        st.write("• Men T-Shirt Black")
        st.write("• Women Dress")
        st.write("• Men Jeans Blue")

# --- FOOTER ---
st.markdown("---")
footer_col1, footer_col2, footer_col3 = st.columns(3)
with footer_col1:
    st.caption("🛡️ Safe & Secure Shopping")
with footer_col2:
    st.caption("💰 Best Price Guarantee")
with footer_col3:
    st.caption("⚡ Real-time Updates")