def cpc_dashboard_app(mode):
    import streamlit as st
    import pandas as pd
    import numpy as np
    import gspread
    from gspread_dataframe import set_with_dataframe
    from google.oauth2.service_account import Credentials
    from datetime import datetime
    import json
    import tempfile

    # --- Google Sheets Setup ---
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    SHEET_ID = "1vaKOc9re-xBwVhJ3oOOGtjmGVembMsAUq93krQo0mpc"

    read_creds = Credentials.from_service_account_info(
        info=st.secrets["google_service_account"],
        scopes=SCOPES
    )
    read_client = gspread.authorize(read_creds)

    @st.cache_data(show_spinner=False)
    def load_data(worksheet_name):
        sheet = read_client.open_by_key(SHEET_ID).worksheet(worksheet_name)
        data = sheet.get_all_values()
        df = pd.DataFrame(data[1:], columns=data[0])
        return df

    @st.cache_data(show_spinner=False)
    def preprocess_launching(df):
        df = df.copy()
        df['Keyword'] = df['Keyword'].apply(lambda x: 'all key' if x.startswith('all key') else x)
        df = df[~df['Keyword'].str.startswith('all key')]
        df = df[~df['Keyword'].isna() & ~df['Keyword'].str.strip().eq('')]
        df['Start date'] = pd.to_datetime(df['Start date'], format='%d/%m/%Y', errors='coerce')
        df['CPC(USD)'] = df['CPC(USD)'].replace({r'\$': '', ',': '.'}, regex=True).replace('', '0').astype(float)
        df['Year'] = df['Start date'].dt.year
        df['Month'] = df['Start date'].dt.month
        df_grouped = df.groupby(['Year', 'Keyword', 'Match_Type'])['CPC(USD)'].mean().reset_index()
        df_pivot = df_grouped.pivot_table(index=['Year', 'Keyword'], columns='Match_Type', values='CPC(USD)', aggfunc='mean').reset_index()
        df_pivot.columns.name = None
        df_pivot = df_pivot[['Year', 'Keyword', 'auto', 'b,p', 'ex']]
        return df_pivot

    @st.cache_data(show_spinner=False)
    def preprocess_daily(df):
        df = df.copy()
        df['CPC'] = df['CPC'].replace({r'\$': '', ',': '.'}, regex=True).replace('', '0').astype(float)
        df = df[~df['Keyword'].str.contains('all key', case=False, na=False)]
        df_grouped = df.groupby(['Year', 'Keyword', 'Type'])['CPC'].mean().reset_index()
        df_pivot = df_grouped.pivot_table(index=['Year', 'Keyword'], columns='Type', values='CPC', aggfunc='mean').reset_index()
        df_pivot.columns.name = None
        df_pivot = df_pivot[['Year', 'Keyword', 'auto', 'b,p', 'ex']]
        return df_pivot

    # --- Add Title ---
    st.title("Aggregate CPC By Year")  # Đây là tiêu đề mới của bạn

    # Xử lý theo chế độ
    if mode == "CPC Launching":
        df_raw = load_data("LAUNCHING TH")
        df_result = preprocess_launching(df_raw)
        st.subheader("📊 CPC Launching Data")
    else:
        df_raw = load_data("HELIUM TH")
        df_result = preprocess_daily(df_raw)
        st.subheader("📈 CPC Daily Data")

    st.dataframe(df_result, use_container_width=True)

    # Export
    st.markdown("### 📤 Export Section")
    uploaded_file = st.file_uploader("Upload your Google Service Account JSON to export", type="json")

    if st.button("📤 Export to Google Sheet"):
        if not uploaded_file:
            st.warning("⚠️ Please upload a service account JSON file first.")
        else:
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name

                user_creds = Credentials.from_service_account_file(tmp_file_path, scopes=SCOPES)
                user_client = gspread.authorize(user_creds)

                if mode == "CPC Launching":
                    sheet = user_client.open_by_key(SHEET_ID).worksheet("CPC LAUNCHING TH")
                else:
                    sheet = user_client.open_by_key(SHEET_ID).worksheet("CPC HELIUM")

                set_with_dataframe(sheet, df_result, row=2, col=1)
                st.success("✅ Exported to Google Sheet successfully!")
            except Exception as e:
                st.error(f"❌ Failed to export: {e}")
