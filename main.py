import streamlit as st
from daily_app import daily_tracking_app
from cpc_app import cpc_dashboard_app

# Cấu hình giao diện
st.set_page_config(page_title="📈 Data Integration Application", layout="wide")

# Menu chính
st.sidebar.title("📌 Menu")
main_option = st.sidebar.radio("Chọn công cụ:", ["📊 Daily Tracking", "🚀 CPC Launching & Daily"])

if main_option == "📊 Daily Tracking":
    daily_tracking_app()

elif main_option == "🚀 CPC Launching & Daily":
    # Menu phụ trong CPC
    sub_option = st.sidebar.radio("Chọn loại CPC:", ["CPC Launching", "CPC Daily"])
    cpc_dashboard_app(mode=sub_option)
