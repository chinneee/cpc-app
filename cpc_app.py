def cpc_dashboard_app(mode):
    import streamlit as st
    import pandas as pd
    import numpy as np
    import gspread
    from gspread_dataframe import set_with_dataframe
    from google.oauth2.service_account import Credentials
    from datetime import datetime
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
    def load_data(sheet_name):
        sheet = read_client.open_by_key(SHEET_ID).worksheet(sheet_name)
        data = sheet.get_all_values()
        return pd.DataFrame(data[1:], columns=data[0])

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
        return df_pivot[['Year', 'Keyword', 'auto', 'b,p', 'ex']]

    @st.cache_data(show_spinner=False)
    def preprocess_daily(df):
        df = df.copy()
        df['CPC'] = df['CPC'].replace({r'\$': '', ',': '.'}, regex=True).replace('', '0').astype(float)
        df = df[~df['Keyword'].str.contains('all key', case=False, na=False)]
        df = df[~df['Keyword'].isna() & ~df['Keyword'].str.strip().eq('')]
        df_grouped = df.groupby(['Year', 'Keyword', 'Type'])['CPC'].mean().reset_index()
        df_pivot = df_grouped.pivot_table(index=['Year', 'Keyword'], columns='Type', values='CPC', aggfunc='mean').reset_index()
        df_pivot.columns.name = None
        return df_pivot[['Year', 'Keyword', 'auto', 'b,p', 'ex']]

    def estimate_cpc_launching_2025(df_launch, df_daily):
        df_launch = df_launch.copy()
        df_daily = df_daily.copy()

        for df in [df_launch, df_daily]:
            df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
            df.dropna(subset=['Year'], inplace=True)
            df['Year'] = df['Year'].astype(int)

        # Tính CPC trung bình theo Match Type và Year
        def get_avg_cpc(df, label):
            df_avg = df.groupby('Year')[['auto', 'b,p', 'ex']].mean().reset_index()
            df_avg = df_avg[df_avg['Year'].isin([2024, 2025])]
            df_avg = df_avg.melt(id_vars='Year', var_name='Match Type', value_name=f'Avg CPC {label}')
            return df_avg

        avg_launch = get_avg_cpc(df_launch, 'Lau')
        avg_daily = get_avg_cpc(df_daily, 'Dail')

        df_merge = pd.merge(avg_launch, avg_daily, on=['Year', 'Match Type'])
        pivot_df = df_merge.pivot(index='Match Type', columns='Year')
        pivot_df.columns = ['_'.join([col[0], str(col[1])]) for col in pivot_df.columns]
        pivot_df.reset_index(inplace=True)

        # Tính các tỷ lệ
        pivot_df['CPC_Daily_Ratio_25_vs_24'] = pivot_df['Avg CPC Dail_2025'] / pivot_df['Avg CPC Dail_2024']
        pivot_df['CPC_Launching_Ratio_25_vs_24'] = pivot_df['Avg CPC Lau_2025'] / pivot_df['Avg CPC Lau_2024']
        pivot_df['Launch_vs_Daily_2025'] = pivot_df['Avg CPC Lau_2025'] / pivot_df['Avg CPC Dail_2025']
        st.subheader("📌 Pivot CPC Summary")
        st.dataframe(pivot_df, use_container_width=True)

        # 🔄 Tạo bảng 2024 từ dữ liệu 2024 + 2023, ưu tiên 2024
        def get_most_recent_rows(df, label):
            df_24 = df[df['Year'].isin([2023, 2024])].copy()
            df_24.sort_values(by='Year', ascending=False, inplace=True)
            return df_24.drop_duplicates('Keyword', keep='first')

        df_2024_launch = get_most_recent_rows(df_launch, 'Lau')
        df_2024_daily = get_most_recent_rows(df_daily, 'Dail')

        # 👉 Tạo bảng 2025 launching
        df_2025_launch = df_2024_launch.copy()
        for mt in ['auto', 'b,p', 'ex']:
            df_2025_launch[mt] = df_2025_launch[mt] * pivot_df.loc[pivot_df['Match Type'] == mt, 'CPC_Launching_Ratio_25_vs_24'].values[0]
        df_2025_launch['Year'] = 2025

        # 👉 Tạo bảng 2025 daily
        df_2025_daily = df_2024_daily.copy()
        for mt in ['auto', 'b,p', 'ex']:
            df_2025_daily[mt] = df_2025_daily[mt] * pivot_df.loc[pivot_df['Match Type'] == mt, 'CPC_Daily_Ratio_25_vs_24'].values[0]
            df_2025_daily[mt] = df_2025_daily[mt] * pivot_df.loc[pivot_df['Match Type'] == mt, 'Launch_vs_Daily_2025'].values[0]
        df_2025_daily['Year'] = 2025

        # Kết hợp bảng 2025
        df_2025 = pd.concat([df_2025_launch, df_2025_daily], ignore_index=True)
        df_2025 = df_2025.dropna(subset=['Keyword'])
        df_2025['Year'] = pd.to_numeric(df_2025['Year'], errors='coerce')
        df_2025 = df_2025.groupby(['Keyword', 'Year'], as_index=False).mean(numeric_only=True)

        # Check duplicates
        duplicates = df_2025[df_2025.duplicated(subset=['Keyword', 'Year'], keep=False)]
        if not duplicates.empty:
            st.warning("🔁 Duplicated data detected:")
            st.dataframe(duplicates)
        else:
            st.success("✅ No duplicated data found.")

        st.subheader("📊 Estimated CPC Launching 2025")
        st.dataframe(df_2025, use_container_width=True)


        # Export
        uploaded_file = st.file_uploader("Upload Google Service JSON để export bảng 2025", type="json", key="est_export")
        if st.button("📤 Export Estimated CPC 2025"):
            if uploaded_file:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name
                user_creds = Credentials.from_service_account_file(tmp_file_path, scopes=SCOPES)
                user_client = gspread.authorize(user_creds)
                sheet = user_client.open_by_key(SHEET_ID).worksheet("EST CPC LAUNCHING")
                set_with_dataframe(sheet, df_2025, row=2)
                st.success("✅ Exported to Google Sheet successfully!")
            else:
                st.warning("⚠️ Please upload a service account JSON file.")

    # Giao diện chính
    st.title("Aggregate CPC By Year")

    # Menu phụ
    if mode in ["CPC Launching", "CPC Daily"]:
        df_raw = load_data("LAUNCHING TH" if mode == "CPC Launching" else "HELIUM TH")
        df_result = preprocess_launching(df_raw) if mode == "CPC Launching" else preprocess_daily(df_raw)
        st.subheader(f"📊 {mode} Data")
        st.dataframe(df_result, use_container_width=True)

        # Export gốc
        st.markdown("### 📤 Export Section")
        uploaded_file = st.file_uploader("Upload your Google Service Account JSON to export", type="json")
        if st.button("📤 Export to Google Sheet"):
            if not uploaded_file:
                st.warning("⚠️ Please upload a service account JSON file first.")
            else:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name
                user_creds = Credentials.from_service_account_file(tmp_file_path, scopes=SCOPES)
                user_client = gspread.authorize(user_creds)
                sheet_name = "CPC LAUNCHING TH" if mode == "CPC Launching" else "CPC HELIUM"
                sheet = user_client.open_by_key(SHEET_ID).worksheet(sheet_name)
                set_with_dataframe(sheet, df_result, row=2)
                st.success("✅ Exported to Google Sheet successfully!")

    # Tính toán dự báo
    if mode == "CPC Launching":
        st.markdown("---")
        if st.checkbox("📐 Estimate CPC Launching 2025"):
            df_launching = preprocess_launching(load_data("LAUNCHING TH"))
            df_daily = preprocess_daily(load_data("HELIUM TH"))
            estimate_cpc_launching_2025(df_launching, df_daily)
