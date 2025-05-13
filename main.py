import streamlit as st
from daily_app import daily_tracking_app
from cpc_app import cpc_dashboard_app, estimate_cpc_launching_app  # Thêm estimate vào import

# Cấu hình giao diện
st.set_page_config(page_title="📈 Data Integration Application", layout="wide")

# Menu chính
st.sidebar.title("📌 Menu")
main_option = st.sidebar.radio("Chọn công cụ:", ["Daily Tracking", "CPC Launching & Daily"])

if main_option == "Daily Tracking":
    daily_tracking_app()

elif main_option == "CPC Launching & Daily":
    sub_option = st.sidebar.radio("Chọn loại CPC:", ["CPC Launching", "CPC Daily", "Estimate CPC Launching"])
    
    if sub_option in ["CPC Launching", "CPC Daily"]:
        cpc_dashboard_app(mode=sub_option)
    elif sub_option == "Estimate CPC Launching":
        estimate_cpc_launching_app()  # Gọi đúng hàm mới


