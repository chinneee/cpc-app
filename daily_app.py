import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
import gspread
from gspread_dataframe import set_with_dataframe
from google.oauth2.service_account import Credentials
import json
import altair as alt

def add_date_column(df, date_str):
    df['Date'] = pd.to_datetime(date_str, format='%Y-%m-%d').date()
    cols = [col for col in df.columns if col != 'Date'] + ['Date']
    return df[cols]

def load_and_clean_reports(br_file, ads_file, date_str):
    br = pd.read_csv(br_file)[['(Parent) ASIN', '(Child) ASIN', 'Sessions - Total', 'Units Ordered']]
    br.columns = ['Parent_ASIN', 'Child_ASIN', 'Sessions', 'Units_Ordered']
    br['Sessions'] = br['Sessions'].astype(str).str.replace(',', '').astype(int)
    br['Units_Ordered'] = br['Units_Ordered'].astype(str).str.replace(',', '').astype(int)
    br = add_date_column(br, date_str)

    ads = pd.read_csv(ads_file)[['Products', 'Clicks', 'Spend(USD)']]
    ads.columns = ['Child_ASIN', 'Clicks_Ads', 'Spend_Ads']
    ads['Child_ASIN'] = ads['Child_ASIN'].str[:10]
    ads = add_date_column(ads, date_str)

    merged = pd.merge(br, ads, on=["Child_ASIN", "Date"], how="left").fillna(0)
    merged["Clicks_Ads"] = merged["Clicks_Ads"].astype(int)
    merged["Spend_Ads"] = merged["Spend_Ads"].astype(float)
    return merged

def export_to_gsheet(df, sheet_id, credential_json, worksheet_name, start_row):
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(credential_json, scopes=scopes)
    client = gspread.authorize(creds)
    worksheet = client.open_by_key(sheet_id).worksheet(worksheet_name)
    set_with_dataframe(worksheet, df, row=start_row, include_column_header=False)

def load_full_gsheet_data(sheet_id, credential_json, worksheet_name):
    creds = Credentials.from_service_account_info(credential_json, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    client = gspread.authorize(creds)
    worksheet = client.open_by_key(sheet_id).worksheet(worksheet_name)
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    # Date is day/month/year format
    df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')
    df['Sessions'] = df['Sessions'].astype(int)
    df['Units_Ordered'] = df['Units_Ordered'].astype(int)
    df['Clicks_Ads'] = df['Clicks_Ads'].astype(int)
    df['Spend_Ads'] = df['Spend_Ads'].astype(float)
    return df

def volatility_analysis_ui(sheet_id, worksheet_name):
    st.subheader("📊 Daily Volatility Analysis")
    uploaded_cred = st.file_uploader("🔐 Upload Google Credentials JSON", type="json", key="volatility_json")

    if uploaded_cred:
        try:
            cred_dict = json.loads(uploaded_cred.read())
            full_df = load_full_gsheet_data(sheet_id, cred_dict, worksheet_name)

            full_df['Month'] = full_df['Date'].dt.to_period('M')
            available_months = full_df['Month'].astype(str).sort_values().unique().tolist()
            selected_month = st.selectbox("📅 Month", options=available_months, index=len(available_months) - 1)

            metric = st.selectbox("📌 Select Fluctuation Criteria:", options=["Sessions", "Units_Ordered", "Spend_Ads"])

            month_df = full_df[full_df['Month'].astype(str) == selected_month]
            month_df = month_df.sort_values(['Child_ASIN', 'Date'])

            month_df['Change_Pct'] = month_df.groupby('Child_ASIN')[metric].pct_change().abs()
            volatility = month_df.groupby('Child_ASIN')['Change_Pct'].mean().reset_index()
            top10_asins = volatility.sort_values(by='Change_Pct', ascending=False).head(10)['Child_ASIN'].tolist()
            top10_df = month_df[month_df['Child_ASIN'].isin(top10_asins)]

            st.markdown(f"### 🔟 Top 10 ASINs with the Strongest Movements `{metric}` in {selected_month}")
            st.dataframe(top10_df[['Child_ASIN', 'Date', metric, 'Change_Pct']])

            chart = alt.Chart(top10_df).mark_line(point=True).encode(
                x='Date:T',
                y=alt.Y(f'{metric}:Q', title=metric),
                color='Child_ASIN:N',
                tooltip=['Child_ASIN', 'Date', metric]
            ).properties(title=f'{metric} Daily - Top 10 Most Volatile ASINs')

            st.altair_chart(chart, use_container_width=True)

        except Exception as e:
            st.error(f"❌ Unable to analyze volatility: {e}")

def daily_tracking_app():
    st.title("📊 Daily Data Merger & GSheet Exporter")
    st.markdown("Upload 2 CSV files: Business Report + Ads Report")

    br_file = st.file_uploader("📎 Upload Business Report CSV", type="csv")
    ads_file = st.file_uploader("📎 Upload Ads Report CSV", type="csv")
    date_input = st.text_input("📅 Enter Report Date (YYYY-MM-DD)", value=datetime.today().strftime("%Y-%m-%d"))

    if br_file and ads_file and date_input:
        try:
            merged_df = load_and_clean_reports(br_file, ads_file, date_input)
            st.success("✅ File merged successfully!")
            st.dataframe(merged_df)

            buffer = BytesIO()
            merged_df.to_excel(buffer, index=False)
            st.download_button("📥 Download Merged Excel", buffer.getvalue(), file_name="merged_daily_summary.xlsx")

            if st.checkbox("📤 Push to Google Sheets"):
                uploaded_cred = st.file_uploader("🔐 Upload Google Credentials JSON", type="json", key="push_json")

                if uploaded_cred:
                    cred_dict = json.loads(uploaded_cred.read())

                    try:
                        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
                        creds = Credentials.from_service_account_info(cred_dict, scopes=scopes)
                        client = gspread.authorize(creds)
                        worksheet = client.open_by_key("18juLU-AmJ8GVnKdGFrBrDT_qxqxcu_aLNK-2LYOsuYk").worksheet("DAILY_TH")
                        current_row = len(worksheet.get_all_values()) + 1
                        st.write("🔢 **Start Row in Sheet:**", current_row)

                        df_final = merged_df[['Child_ASIN', 'Sessions', 'Units_Ordered', 'Clicks_Ads', 'Spend_Ads', 'Date']].sort_values(['Date', 'Child_ASIN'])
                        set_with_dataframe(worksheet, df_final, row=current_row, include_column_header=False)
                        st.success(f"✅ Data pushed to Google Sheets (start row: {current_row})!")

                    except Exception as e:
                        st.error(f"❌ Could not push to Google Sheets: {e}")

        except Exception as e:
            st.error(f"❌ Error during merging or processing files: {e}")

    # --- Phân tích biến động TÁCH RIÊNG ---
    # st.markdown("### 📊 Daily Volatility Analysis")
    volatility_analysis_ui(sheet_id="18juLU-AmJ8GVnKdGFrBrDT_qxqxcu_aLNK-2LYOsuYk", worksheet_name="DAILY_TH")

