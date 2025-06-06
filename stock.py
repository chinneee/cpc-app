import streamlit as st
import pandas as pd
import io
from datetime import datetime as dt
from gspread_dataframe import set_with_dataframe
import gspread
from google.oauth2.service_account import Credentials

def stock_app():
    st.subheader("⬆️ 1. Upload FBA Inventory File (.txt)")
    uploaded_file = st.file_uploader("Chọn file TXT từ Amazon FBA", type=["txt"])

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file, sep="\t", encoding="cp1252")

        # Preview
        st.subheader("📋 Xem trước 10 dòng đầu tiên:")
        st.dataframe(df.head(10))

        # Xử lý
        df_sorted = df.sort_values(by='Quantity Available', ascending=False)
        df_deduped = df_sorted.drop_duplicates(subset='asin', keep='first')
        df_filtered = df_deduped[(df_deduped['Warehouse-Condition-code'] == 'SELLABLE') & 
                                 (df_deduped['Quantity Available'] > 0)].copy()
        if 'condition-type' in df_filtered.columns:
            df_filtered.drop(columns=['condition-type'], inplace=True)

        df_filtered['Date'] = dt.now().strftime('%Y-%m-%d')

        # ✅ ASIN tồn kho ≥ 50
        st.subheader("⚠️ Những ASIN có Quantity Available >= 50")
        high_stock_df = df_filtered[df_filtered['Quantity Available'] <= 50]
        st.dataframe(high_stock_df)

        # Download file high-stock
        output_high = io.BytesIO()
        with pd.ExcelWriter(output_high, engine="openpyxl") as writer:
            high_stock_df.to_excel(writer, index=False, sheet_name="HighStock")
        st.download_button("📥 Tải file ASIN sắp hết hàng", data=output_high.getvalue(), file_name="HighStock_ASINs.xlsx")

        # Google Sheets upload
        st.subheader("🔐 2. Upload lên Google Sheets (tùy chọn)")
        json_file = st.file_uploader("Upload file credentials JSON", type=["json"])

        if json_file is not None:
            try:
                creds = Credentials.from_service_account_info(
                    json_file.read(), scopes=["https://www.googleapis.com/auth/spreadsheets"]
                )
                client = gspread.authorize(creds)
                sheet_id = st.text_input("🔗 Nhập Google Sheet ID:", "")
                if sheet_id:
                    worksheet = client.open_by_key(sheet_id).worksheet("DAILY_STOCK")
                    set_with_dataframe(worksheet, df_filtered)
                    st.success("✅ Đã đẩy dữ liệu lên Google Sheet thành công!")
            except Exception as e:
                st.error(f"Lỗi khi kết nối Google Sheets: {e}")

        # 🎯 Lọc theo danh sách ASIN người dùng nhập
        st.subheader("🔍 3. Dán danh sách ASIN cần kiểm tra")
        asin_input = st.text_area("Nhập danh sách ASIN cách nhau bằng dấu phẩy hoặc xuống dòng")

        if asin_input:
            asin_list = [a.strip() for a in asin_input.replace(",", "\n").splitlines() if a.strip()]
            found_df = df_filtered[df_filtered['asin'].isin(asin_list)]
            not_found = [a for a in asin_list if a not in df_filtered['asin'].values]

            st.write("📄 Kết quả lọc ASIN:")
            st.dataframe(found_df)

            output_found = io.BytesIO()
            with pd.ExcelWriter(output_found, engine="openpyxl") as writer:
                found_df.to_excel(writer, index=False, sheet_name="FilteredASINs")
            st.download_button("📥 Tải file ASIN đã lọc", data=output_found.getvalue(), file_name="Filtered_ASINs.xlsx")

            if not_found:
                st.warning("⚠️ Không tìm thấy các ASIN sau trong dữ liệu:")
                for nf in not_found:
                    st.write(f"- {nf}")
