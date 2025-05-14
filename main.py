import streamlit as st
from daily_app import daily_tracking_app
from cpc_app import cpc_dashboard_app, estimate_cpc_launching  # ✅ Thêm hàm mới

# Cấu hình giao diện
st.set_page_config(page_title="📈 Data Integration Application", layout="wide")

# Giao diện sidebar
st.sidebar.title("📌 Công cụ tổng hợp dữ liệu")
main_option = st.sidebar.radio("Chọn chức năng chính:", ["🗓️ Daily Tracking", "📊 CPC Tools"])

# Xử lý lựa chọn menu
if main_option == "🗓️ Daily Tracking":
    st.title("🗓️ Daily Tracking Report")
    daily_tracking_app()

elif main_option == "📊 CPC Tools":
    st.title("📊 CPC Launching & Daily Analysis")

    # ✅ Menu phụ cập nhật đầy đủ
    sub_option = st.sidebar.radio(
        "Chọn chế độ phân tích CPC:",
        ["CPC Launching", "CPC Daily", "Estimate CPC Launching"]
    )

    if sub_option in ["CPC Launching", "CPC Daily"]:
        cpc_dashboard_app(mode=sub_option)

    elif sub_option == "Estimate CPC Launching":
        estimate_cpc_launching()  # ✅ Gọi hàm ước lượng CPC
