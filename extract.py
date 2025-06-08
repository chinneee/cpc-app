# extract_keywords
import streamlit as st
import pandas as pd
import numpy as np
import re
import json
import gspread
from datetime import datetime as dt
from gspread_dataframe import set_with_dataframe
from google.oauth2.service_account import Credentials

def extract_keywords():

    # Step 1: Upload CSV files
    uploaded_files = st.file_uploader("📁 Upload one or more CSV files", type="csv", accept_multiple_files=True)

    if uploaded_files:
        # Combine uploaded CSVs
        df_combined = pd.concat([pd.read_csv(file) for file in uploaded_files], ignore_index=True)

        # Step 2: Add missing columns
        df_combined["Keyword"] = ""
        df_combined["Match_Type"] = ""

        # Step 3: Calculate CVR safely
        df_combined["CVR"] = df_combined["Orders"] / df_combined["Clicks"].replace(0, np.nan)
        df_combined["CVR"] = df_combined["CVR"].fillna(0)

        # Step 4: Extract keyword and match type
        def extract_keyword_type(campaign):
            campaign = str(campaign).strip().lower()
            campaign = re.sub(r'[_\s]*\d{1,2}h(?:\d{1,2}m?)?$', '', campaign)
            if campaign.endswith('_product exp'):
                return pd.Series(['product', 'exp'])
            if 'auto' in campaign:
                match = re.search(r'(auto\s?\d*(?:h\d*)?)', campaign, re.IGNORECASE)
                return pd.Series([match.group(1).strip(), 'auto']) if match else pd.Series([None, 'auto'])
            if 'all key' in campaign:
                match = re.search(r'(all\s?key(?:\s?\w+)*)', campaign, re.IGNORECASE)
                return pd.Series([match.group(1).strip(), 'all key']) if match else pd.Series([None, 'all key'])
            match = re.search(r'^(.*?)[_\s]+(?:asin[_\s]*)?((?:b,p|a,b|p|b|ex|exp))(?:(?:\s*\d+h\d+|\s*\d+h|\s*\d+|)?)$', campaign)
            if match:
                keyword_part = match.group(1).strip()
                type_part = match.group(2).strip()
                parts = keyword_part.split('_')
                if len(parts) > 3:
                    keyword = ' '.join(parts[3:])
                elif len(parts) > 1:
                    keyword = ' '.join(parts[1:])
                else:
                    keyword = keyword_part
                return pd.Series([keyword.strip(), type_part])
            return pd.Series([None, None])

        df_combined[["Keyword", "Match_Type"]] = df_combined["Campaigns"].apply(extract_keyword_type)

        # Step 5: Format date & CPC
        df_combined['Start date'] = pd.to_datetime(df_combined['Start date'], format='%m/%d/%y', errors='coerce')
        df_combined['Start date'] = df_combined['Start date'].dt.strftime('%d/%m/%Y')
        df_combined['CPC(USD)'] = df_combined['CPC(USD)'].replace({r'\$': '', ',': '.'}, regex=True).replace('', '0').astype(float)

        # Step 6: Show preview
        st.subheader("✅ Data to be Appended")
        st.dataframe(df_combined, use_container_width=True)

        st.subheader("⚠️ Campaigns with Missing Keyword/Match_Type")
        unmatched_rows = df_combined[df_combined['Keyword'].isna() & df_combined['Match_Type'].isna()][['Campaigns']]
        st.dataframe(unmatched_rows, use_container_width=True)

        # Step 7: Upload credentials
        st.subheader("🔑 Upload your `credentials.json` file")
        cred_file = st.file_uploader("Upload `credentials.json` to enable export", type="json", key="cred")

        if cred_file is not None:
            try:
                service_account_info = json.load(cred_file)
                creds = Credentials.from_service_account_info(
                    service_account_info,
                    scopes=["https://www.googleapis.com/auth/spreadsheets"]
                )
                client = gspread.authorize(creds)

                # Sheet info
                SHEET_ID = "1vaKOc9re-xBwVhJ3oOOGtjmGVembMsAUq93krQo0mpc"
                worksheet_name = "LAUNCHING 2025"

                if st.button("📤 Export to Google Sheets"):
                    sheet = client.open_by_key(SHEET_ID).worksheet(worksheet_name)

                    headers = sheet.row_values(1)
                    df_export = df_combined[[col for col in headers if col in df_combined.columns]]

                    current_data = sheet.get_all_values()
                    start_row = len(current_data) + 1

                    set_with_dataframe(sheet, df_export, row=start_row, col=1, include_column_header=False)
                    st.success(f"✅ Appended {len(df_export)} rows to Google Sheets starting from row {start_row}.")

            except Exception as e:
                st.error(f"❌ Error: {e}")
