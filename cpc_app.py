import pandas as pd
import numpy as np
import re
import glob
import streamlit as st
from datetime import datetime as dt
from gspread_dataframe import set_with_dataframe
import gspread
from google.oauth2.service_account import Credentials

# =========================
# Streamlit UI
# =========================
st.set_page_config(page_title="Keyword Cleaner", layout="wide")
st.title("📊 Keyword Analysis & GSheet Uploader")

uploaded_files = st.file_uploader("Upload CSV file(s)", type=["csv"], accept_multiple_files=True)

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

    match = re.search(
        r'^(.*?)[_\s]+(?:asin[_\s]*)?((?:b,p|a,b|p|b|ex|exp))(?:(?:\s*\d+h\d+|\s*\d+h|\s*\d+|)?)$',
        campaign
    )
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

def clean_match_type(value):
    if pd.isna(value): return value
    value = str(value).strip().lower()
    return re.sub(r'auto\s*\d+[h\d]*', 'auto', value)

# =========================
# Handle File Uploads
# =========================
df_combined = pd.DataFrame()

if uploaded_files:
    dfs = [pd.read_csv(f) for f in uploaded_files]
    df_combined = pd.concat(dfs, ignore_index=True)
    st.success(f"Uploaded and merged {len(uploaded_files)} file(s).")

    # Clean and enrich
    df_combined['Keyword'] = ""
    df_combined['Match_Type'] = ""
    df_combined[['Keyword', 'Match_Type']] = df_combined['Campaigns'].apply(extract_keyword_type)
    df_combined['Match_Type'] = df_combined['Match_Type'].apply(clean_match_type)
    df_combined['CVR'] = df_combined['Orders'] / df_combined['Clicks']
    df_combined['CVR'] = df_combined['CVR'].fillna(0)
    df_combined['CPC(USD)'] = df_combined['CPC(USD)'].replace({r'\$': '', ',': '.'}, regex=True).replace('', '0').astype(float)

    st.dataframe(df_combined.head())

    # Optional push to Google Sheets
    if st.checkbox("Push to Google Sheet"):
        start_row = st.number_input("Start row in Google Sheet", min_value=1, value=2)
        cred_file = st.file_uploader("Upload your credential JSON file", type="json")

        if cred_file:
            creds = Credentials.from_service_account_info(
                pd.read_json(cred_file).to_dict(),
                scopes=["https://www.googleapis.com/auth/spreadsheets"]
            )
            client = gspread.authorize(creds)

            sheet_id = st.text_input("Enter your Google Sheet ID")
            sheet_name = st.text_input("Enter sheet name", value="LAUNCHING 2025")

            if sheet_id and sheet_name:
                try:
                    worksheet = client.open_by_key(sheet_id).worksheet(sheet_name)
                    set_with_dataframe(worksheet, df_combined, row=start_row, col=1, include_column_header=False)
                    st.success("✅ Data pushed successfully!")
                except Exception as e:
                    st.error(f"❌ Failed to push: {e}")
else:
    st.info("Please upload one or more CSV files to begin.")

