import streamlit as st
from daily_app import daily_tracking_app
from cpc_app import cpc_dashboard_app
from asins_app import asins_launching_app
from extract import extract_keywords
from stock import stock_app 

# Cấu hình giao diện
st.set_page_config(page_title="Data Integration Application", layout="wide")

# Giao diện sidebar
st.sidebar.title("📌 Data Integration Tool")
main_option = st.sidebar.radio("Main Functions:", ["🗓️ Daily Tracking", "📊 CPC Tools", "🚀 ASINs Launching", "📤 Extract Keywords", "📦 FBA Inventory"])

# Xử lý lựa chọn menu
if main_option == "🗓️ Daily Tracking":
    st.title("🗓️ Daily Tracking Report")
    daily_tracking_app()

elif main_option == "📊 CPC Tools":
    st.title("📊 CPC Launching & Daily Analysis")
    sub_option = st.sidebar.radio("CPC Analysis Mode:", ["CPC Launching", "CPC Daily"])
    cpc_dashboard_app(mode=sub_option)

elif main_option == "🚀 ASINs Launching":
    st.title("🚀 ASINs Launching Campaign Upload")
    asins_launching_app()  

elif main_option == "📤 Extract Keywords":
    st.title("📤 Extract Keywords To Google Sheets")
    extract_keywords()  

elif main_option == "📦 FBA Inventory":
    st.title("📦 Amazon FBA Inventory Review")
    stock_app()  