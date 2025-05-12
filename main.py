import streamlit as st
from daily_app import daily_tracking_app
from cpc_app import cpc_dashboard_app

st.set_page_config(page_title="📈 Unified Tracking App", layout="wide")
st.sidebar.title("📌 Menu")

option = st.sidebar.radio("Chọn công cụ:", ["📊 Daily Tracking", "🚀 CPC Launching & Daily"])

if option == "📊 Daily Tracking":
    daily_tracking_app()
elif option == "🚀 CPC Launching & Daily":
    cpc_dashboard_app()

st.set_page_config(page_title="📈 Unified Tracking App", layout="wide")
st.sidebar.title("📌 Menu")

option = st.sidebar.radio("Chọn công cụ:", ["📊 Daily Tracking", "🚀 CPC Launching & Daily"])

if option == "📊 Daily Tracking":
    daily_tracking_app()
elif option == "🚀 CPC Launching & Daily":
    cpc_dashboard_app()
