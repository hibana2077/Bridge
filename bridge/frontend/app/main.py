import streamlit as st
import httpx
import json
import pandas as pd
import time
from datetime import datetime
import os

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://backend:8000")

# Page configuration
st.set_page_config(
    page_title="TradingView Alert Bridge",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# App title
st.title("📈 TradingView Alert Bridge")
st.subheader("Connect TradingView alerts to crypto exchanges")

# Sidebar navigation
page = st.sidebar.radio("Navigation", ["Dashboard", "Exchange API Keys", "Alert Configurations", "Alert History", "Documentation"])

# Helper functions for API calls
def api_get(endpoint, params=None):
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{API_BASE_URL}{endpoint}", params=params)
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"API Error ({response.status_code}): {response.text}")
                return None
    except Exception as e:
        st.error(f"Connection error: {str(e)}")
        return None

def api_post(endpoint, data):
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(f"{API_BASE_URL}{endpoint}", json=data)
            if response.status_code in (200, 201):
                return response.json()
            else:
                st.error(f"API Error ({response.status_code}): {response.text}")
                return None
    except Exception as e:
        st.error(f"Connection error: {str(e)}")
        return None

def api_delete(endpoint):
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.delete(f"{API_BASE_URL}{endpoint}")
            if response.status_code in (200, 204):
                return response.json() if response.content else {"success": True}
            else:
                st.error(f"API Error ({response.status_code}): {response.text}")
                return None
    except Exception as e:
        st.error(f"Connection error: {str(e)}")
        return None

# Dashboard page
def show_dashboard():
    st.header("Dashboard")
    
    col1, col2 = st.columns(2)
    
    # Get statistics
    with col1:
        st.subheader("System Status")
        
        # Check API connectivity
        with st.spinner("Checking API connectivity..."):
            api_status = api_get("/")
            if api_status:
                st.success("✅ Backend API is connected and running")
            else:
                st.error("❌ Backend API connection failed")
        
        # Show system information
        st.info("System Information")
        st.code(f"""
API URL: {API_BASE_URL}
Frontend Version: 1.0.0
Date & Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """)
    
    with col2:
        st.subheader("Quick Setup Guide")
        st.markdown("""
        **Complete these steps to get started:**
        
        1. Add your exchange API keys in the **Exchange API Keys** section
        2. Create alert configurations in the **Alert Configurations** section
        3. Configure TradingView alerts to send webhooks to your alert endpoint
        
        See the **Documentation** section for detailed instructions.
        """)
    
    # Show alert webhook URL
    st.subheader("Your TradingView Webhook URL")
    webhook_url = f"{API_BASE_URL}/webhook/tradingview"
    st.code(webhook_url)
    st.info("Use this URL in your TradingView alert webhooks. Include 'config_name' and 'user_id' fields in your JSON payload.")

# Exchange API Keys page
def show_api_keys():
    st.header("Exchange API Keys")
    
    # Fetch supported exchanges
    exchanges = api_get("/api/exchanges")
    if not exchanges:
        st.error("Could not fetch supported exchanges")
        return
        
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Add API Keys")
        selected_exchange = st.selectbox("Select Exchange", options=exchanges)
        
        with st.form("api_key_form"):
            api_key = st.text_input("API Key", type="password")
            api_secret = st.text_input("API Secret", type="password")
            submit_button = st.form_submit_button("Save API Keys")
            
            if submit_button:
                if api_key and api_secret:
                    # Submit API keys
                    result = api_post("/api/keys", {
                        "exchange": selected_exchange,
                        "api_key": api_key,
                        "api_secret": api_secret
                    })
                    
                    if result and result.get("success"):
                        st.success(f"API keys saved for {selected_exchange}")
                    else:
                        st.error("Failed to save API keys")
                else:
                    st.error("API Key and Secret are required")
    
    with col2:
        st.subheader("Configured Exchanges")
        if st.button("Refresh"):
            st.info("Refreshing exchange status...")
            
        st.write("Exchanges with API keys configured:")
        
        # Create placeholder for exchange status table
        table_placeholder = st.empty()
        
        # Get status for each exchange
        exchange_status = []
        for exchange in exchanges:
            status = api_get(f"/api/keys/{exchange}")
            if status:
                exchange_status.append({
                    "Exchange": exchange.capitalize(),
                    "API Keys Configured": "✅" if status.get("has_keys") else "❌",
                    "Actions": exchange if status.get("has_keys") else None
                })
        
        # Show exchange status table
        if exchange_status:
            df = pd.DataFrame(exchange_status)
            table_placeholder.dataframe(df, hide_index=True, use_container_width=True)
            
            # Add delete functionality
            delete_exchange = st.selectbox(
                "Select exchange to remove API keys",
                options=[e["Actions"] for e in exchange_status if e["Actions"] is not None],
                index=None
            )
            
            if delete_exchange and st.button("Delete API Keys"):
                confirm = st.checkbox("Confirm deletion")
                if confirm:
                    result = api_delete(f"/api/keys/{delete_exchange}")
                    if result and result.get("success"):
                        st.success(f"API keys for {delete_exchange} deleted")
                        st.rerun()
                    else:
                        st.error(f"Failed to delete API keys for {delete_exchange}")
        else:
            table_placeholder.info("No exchanges configured yet")

# Alert Configurations page
def show_alert_configs():
    st.header("Alert Configurations")
    
    # Fetch supported exchanges
    exchanges = api_get("/api/exchanges")
    if not exchanges:
        st.error("Could not fetch supported exchanges")
        return
    
    tabs = st.tabs(["Create Configuration", "Manage Configurations"])
    
    with tabs[0]:
        st.subheader("Create Alert Configuration")
        
        with st.form("config_form"):
            name = st.text_input("Configuration Name")
            exchange = st.selectbox("Exchange", options=exchanges)
            symbol = st.text_input("Trading Pair (e.g., BTC/USDT)")
            
            col1, col2 = st.columns(2)
            with col1:
                order_type = st.selectbox("Order Type", options=["market", "limit", "stop_loss", "take_profit"])
                position_side = st.selectbox("Position Side", options=["long", "short"])
                
            with col2:
                use_percentage = st.checkbox("Use percentage of balance")
                if use_percentage:
                    quantity_percentage = st.number_input("Percentage of Balance (%)", min_value=1, max_value=100, value=10)
                    quantity = None
                else:
                    quantity = st.number_input("Quantity", min_value=0.0, value=0.01, step=0.01)
                    quantity_percentage = None
                
                if order_type != "market":
                    price = st.number_input("Price", min_value=0.0, step=0.01)
                else:
                    price = None
            
            description = st.text_area("Description (optional)")
            
            submit_button = st.form_submit_button("Save Configuration")
            
            if submit_button:
                if not name or not symbol:
                    st.error("Name and Symbol are required")
                else:
                    # Prepare data
                    config_data = {
                        "name": name,
                        "exchange": exchange,
                        "symbol": symbol,
                        "order_type": order_type,
                        "position_side": position_side,
                        "description": description
                    }
                    
                    if use_percentage and quantity_percentage:
                        config_data["quantity_percentage"] = quantity_percentage
                    elif quantity:
                        config_data["quantity"] = quantity
                        
                    if price:
                        config_data["price"] = price
                    
                    # Submit config
                    result = api_post("/api/config", config_data)
                    
                    if result and result.get("success"):
                        st.success(f"Alert configuration '{name}' saved")
                    else:
                        st.error("Failed to save alert configuration")
    
    with tabs[1]:
        st.subheader("Manage Configurations")
        
        if st.button("Refresh"):
            st.info("Refreshing configurations...")
        
        # Fetch existing configurations
        configs = api_get("/api/config")
        
        if not configs:
            st.info("No alert configurations found")
            return
            
        # Display configurations
        for idx, config in enumerate(configs):
            with st.expander(f"{config['name']} ({config['exchange']} - {config['symbol']})"):
                st.json(config)
                
                # Delete button
                if st.button(f"Delete {config['name']}", key=f"delete_{idx}"):
                    confirm = st.checkbox(f"Confirm deletion of {config['name']}", key=f"confirm_{idx}")
                    if confirm:
                        result = api_delete(f"/api/config/{config['name']}")
                        if result and result.get("success"):
                            st.success(f"Configuration '{config['name']}' deleted")
                            st.rerun()
                        else:
                            st.error(f"Failed to delete configuration '{config['name']}'")

# Alert History page
def show_alert_history():
    st.header("Alert History")
    
    # Parameters for history
    limit = st.slider("Number of records to show", min_value=5, max_value=100, value=20, step=5)
    
    if st.button("Refresh"):
        st.info("Refreshing alert history...")
    
    # Fetch alert history
    history = api_get("/api/history", params={"limit": limit})
    
    if not history:
        st.info("No alert history found")
        return
        
    # Format as dataframe
    records = []
    for entry in history:
        record = {
            "Timestamp": entry.get("timestamp"),
            "Config": entry.get("config_name"),
            "Symbol": entry.get("symbol", "N/A"),
            "Side": entry.get("side", "N/A"),
            "Price": entry.get("price", "N/A"),
            "Status": "Success" if entry.get("success") else "Failed",
            "Message": entry.get("message", "N/A"),
        }
        records.append(record)
    
    if records:
        df = pd.DataFrame(records)
        st.dataframe(df, hide_index=True, use_container_width=True)
        
        # Show details for selected record
        selected_idx = st.selectbox("Select record to see details", options=range(len(records)))
        if selected_idx is not None:
            st.json(history[selected_idx])
    else:
        st.info("No alert history records found")

# Documentation page
def show_documentation():
    st.header("Documentation")
    
    st.markdown("""
    ## How to Configure TradingView Alerts
    
    ### 1. Create an Alert Configuration
    First, create an alert configuration in the **Alert Configurations** section. This defines how your orders will be executed.
    
    ### 2. Set Up TradingView Alert
    1. In TradingView, go to your chart and click on "Alerts" (bell icon)
    2. Create a new alert with your trigger condition
    3. Scroll down to "Webhook URL" and enter your webhook URL:
    """)
    
    webhook_url = f"{API_BASE_URL}/webhook/tradingview"
    st.code(webhook_url)
    
    st.markdown("""
    ### 3. Configure Alert Message
    
    Your webhook message should be in JSON format and include:
    """)
    
    st.code("""
    {
        "config_name": "your_config_name",
        "user_id": "default",
        "price": {{close}},
        "symbol": "{{ticker}}",
        "message": "{{strategy.order.comment}}"
    }
    """)
    
    st.markdown("""
    ### 4. Testing Your Setup
    
    1. Add API keys for your exchange
    2. Create an alert configuration
    3. Set up a TradingView alert with the webhook
    4. When the alert triggers, check the Alert History for the result
    
    ## Security Considerations
    
    * API keys are encrypted in the database
    * Use IP restrictions for your exchange API keys when possible
    * For production use, set up authentication for the webhook
    """)

# Route to the correct page based on sidebar selection
if page == "Dashboard":
    show_dashboard()
elif page == "Exchange API Keys":
    show_api_keys()
elif page == "Alert Configurations":
    show_alert_configs()
elif page == "Alert History":
    show_alert_history()
elif page == "Documentation":
    show_documentation()

# Footer
st.markdown("---")
st.markdown("TradingView Alert Bridge &copy; 2023")