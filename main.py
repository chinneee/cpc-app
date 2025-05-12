import streamlit as st
from daily_app import daily_tracking_app
from cpc_app import cpc_dashboard_app

# Cấu hình giao diện
st.set_page_config(page_title="📈 Unified Tracking App", layout="wide")

# Menu chính
st.sidebar.title("📌 Menu")
main_option = st.sidebar.radio("Chọn công cụ:", ["📊 Daily Tracking", "🚀 CPC Launching & Daily"])

# Hàm review dữ liệu từ Google Sheets
def review_data(sheet_id, data_type):
    st.write(f"Hiển thị dữ liệu {data_type} từ Google Sheet: {sheet_id}")
    # Đọc và xử lý dữ liệu từ Google Sheet
    # Tùy thuộc vào data_type, bạn có thể thêm các hàm xử lý khác nhau ở đây

# Tiêu đề ứng dụng
st.title("Ứng dụng Tổng hợp CPC và Doanh số")

# Tab để chọn loại chức năng cần xem
tab = st.selectbox("Chọn chức năng", ["Review Daily Tracking", "Review CPC Launching", "Review CPC Daily"])

# Xử lý cho các loại dữ liệu
if tab == "Review Daily Tracking":
    sheet_id = st.text_input("Nhập Sheet ID để xem Daily Tracking:")
    if sheet_id:
        review_data(sheet_id, "Daily Tracking")

elif tab == "Review CPC Launching":
    sheet_id = st.text_input("Nhập Sheet ID để xem CPC Launching:")
    if sheet_id:
        review_data(sheet_id, "CPC Launching")

elif tab == "Review CPC Daily":
    sheet_id = st.text_input("Nhập Sheet ID để xem CPC Daily:")
    if sheet_id:
        review_data(sheet_id, "CPC Daily")

# Điều hướng dựa trên lựa chọn menu chính
if main_option == "📊 Daily Tracking":
    daily_tracking_app()

elif main_option == "🚀 CPC Launching & Daily":
    # Menu phụ trong CPC
    sub_option = st.sidebar.radio("Chọn loại CPC:", ["CPC Launching", "CPC Daily"])
    cpc_dashboard_app(mode=sub_option)
