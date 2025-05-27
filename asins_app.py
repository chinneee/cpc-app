# asins_app.py
import streamlit as st
import pandas as pd
import numpy as np
import re
from gspread_dataframe import set_with_dataframe
from google.oauth2.service_account import Credentials
import gspread

def load_file(uploaded_file):
    if uploaded_file is not None:
        if uploaded_file.name.endswith('.csv'):
            return pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith('.xlsx'):
            return pd.read_excel(uploaded_file)
        else:
            st.error("⚠️ File không hợp lệ. Vui lòng upload file CSV hoặc Excel.")
            return None
    return None

def authorize_gsheet(json_file):
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(json_file, scopes=scopes)
    client = gspread.authorize(creds)
    return client

def asins_launching_app():
    st.title("🛠️ Extract Launching Ads & Data Ads Tool")

    tab1, tab2 = st.tabs(["📤 Extract Launching Ads", "📊 Data Ads"])

    # ============================== TAB 1 ==============================
    with tab1:
        st.subheader("📤 Upload Campaigns File")
        campaign_file = st.file_uploader("Chọn file Campaigns (CSV hoặc Excel)", type=["csv", "xlsx"])
        json_file_1 = st.file_uploader("🔐 Upload file JSON Credential để đẩy lên Google Sheets", type="json", key="json1")

        if campaign_file:
            df_campaign = load_file(campaign_file)
            if df_campaign is not None:
                st.success("✅ File đã được đọc thành công.")
                try:
                    df_campaign = df_campaign[['Campaigns','Start date','Top-of-search IS','Impressions','Clicks',
                                               'CTR','Spend(USD)','CPC(USD)','DPV','Orders','Sales(USD)','ACOS']]
                except KeyError:
                    st.error("⚠️ File không đủ cột cần thiết.")
                else:
                    st.dataframe(df_campaign.head())
                    if json_file_1 is not None:
                        json_content = json_file_1.read()
                        json_dict = eval(json_content.decode("utf-8"))
                        client = authorize_gsheet(json_dict)
                        sheet_id = "1clZBdst4_zHzy8IFYWR1xMTQUoR30lkH8fUwrgXexwo"
                        worksheet = client.open_by_key(sheet_id).worksheet("Port")
                        set_with_dataframe(worksheet, df_campaign)
                        st.success("✅ Dữ liệu đã được đẩy lên Google Sheet: Port")

    # ============================== TAB 2 ==============================
    with tab2:
        st.subheader("📊 Upload Search Term Report")
        dataads_file = st.file_uploader("Chọn file Search Term (CSV hoặc Excel)", type=["csv", "xlsx"], key="dataads")
        asin_main = st.text_input("🔍 Nhập ASIN chính (10 ký tự):").strip().upper()
        json_file_2 = st.file_uploader("🔐 Upload file JSON Credential để đẩy lên Google Sheets", type="json", key="json2")

        if dataads_file and asin_main:
            if len(asin_main) != 10 or not asin_main.isalnum():
                st.error("⚠️ ASIN không hợp lệ.")
            else:
                df_ads = load_file(dataads_file)
                if df_ads is not None:
                    df_ads.columns = df_ads.columns.str.strip()
                    valid_targeting = ['substitutes', 'complements', 'loose-match', 'close-match']
                    def update_match_type(row):
                        if row['Match Type'] == '-' and isinstance(row['Targeting'], str):
                            if row['Targeting'] in valid_targeting:
                                return row['Targeting']
                            match = re.search(r'(?:asin-expanded|asin)="(.*?)"', row['Targeting'])
                            if match:
                                return match.group(1)
                        return row['Match Type']
                    df_ads['Match Type'] = df_ads.apply(update_match_type, axis=1)
                    df_ads = df_ads[df_ads['Portfolio name'].str.contains(asin_main, na=False)].copy()

                    money_cols = ['Cost Per Click (CPC)', 'Spend', '7 Day Total Sales ',
                                  '7 Day Advertised SKU Sales ', '7 Day Other SKU Sales ']
                    for col in money_cols:
                        if col in df_ads.columns:
                            df_ads[col] = (
                                df_ads[col].astype(str)
                                    .replace(r'[\$,]', '', regex=True)
                                    .str.replace(',', '.')
                                    .astype(float)
                            )
                    if 'Cost Per Click (CPC)' in df_ads.columns:
                        df_ads['Cost Per Click (CPC)'] = df_ads['Cost Per Click (CPC)'].round(2)

                    percent_cols = ['Click-Thru Rate (CTR)', 'Total Advertising Cost of Sales (ACOS) ',
                                    '7 Day Conversion Rate']
                    for col in percent_cols:
                        if col in df_ads.columns:
                            df_ads[col] = (
                                df_ads[col].astype(str)
                                    .replace('%', '', regex=True)
                                    .str.replace(',', '.')
                                    .astype(float)
                                    .round(4)
                            )

                    st.markdown("### 📄 Dữ liệu sau xử lý:")
                    st.dataframe(df_ads.head())
                    if json_file_2 is not None:
                        json_content = json_file_2.read()
                        json_dict = eval(json_content.decode("utf-8"))
                        client = authorize_gsheet(json_dict)
                        sheet_id = '1clZBdst4_zHzy8IFYWR1xMTQUoR30lkH8fUwrgXexwo'
                        worksheet_name = 'TH MAY LAUNCHING'
                        worksheet = client.open_by_key(sheet_id).worksheet(worksheet_name)
                        set_with_dataframe(worksheet, df_ads)
                        st.success(f"✅ Dữ liệu đã được cập nhật lên Google Sheet: {worksheet_name}")
