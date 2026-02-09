import streamlit as st
import pandas as pd
import os
from datetime import date, timedelta
from io import BytesIO

# ===================== CONFIG =====================

HQ_PASSWORD = "benchmark@hq"

COMPANY_OPTIONS = [
    "Reliance Digital",
    "Croma",
    "Vijay Sales",
    "Bajaj Electronics",
    "Other"
]

YEARS = [2024, 2025, 2026]

EXPECTED_CLUSTERS = [
    "AP 1","AP 2","AP 3","AP 4","BAN 1","BAN 2","BAN 3","BAN 4",
    "BH+JH","Bihar+UP","CG","Chennai 1","Chennai 2","Chennai 3",
    "Gujarat 1","Gujarat 2","Gujarat 3","Haryana + HP",
    "HYD 1","HYD 2","HYD 3","HYD 4","Kerala",
    "Kolkata 1","Kolkata 2","Kolkata 3","MP",
    "Mumbai 1","Mumbai 2+ROM 2","Mumbai 3","Navi Mumbai",
    "NCR 1","NCR 2","NCR 3","NCR 4","North East",
    "Odisha 1","Odisha 2","Pune 1","Pune 2 + ROM 1",
    "Punjab + Jammu","Raj 1","Raj 2","ROK 1","ROK 2","ROK 3",
    "ROM 3","ROM 4+Pune 3","ROTG 1","ROTN 1","ROTN 2","ROWB",
    "UP 1","UP 2","UP 3","UP West+UK"
]

DATA_FILE = "cluster_inputs.csv"

# ===================== FUNCTIONS =====================

def get_mondays(year):
    d = date(year, 1, 1)
    d += timedelta(days=(7 - d.weekday()) % 7)
    mondays = []
    while d.year == year:
        mondays.append(d)
        d += timedelta(days=7)
    return mondays

def to_excel_download(df):
    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)
    return buffer

# ===================== APP =====================

st.set_page_config(layout="wide")
st.title("Weekly Cluster Benchmark – Reliance Digital")

# Small font CSS for pending clusters
st.markdown("""
<style>
.small-font {font-size:12px !important;}
</style>
""", unsafe_allow_html=True)

# ===================== LOAD DATA =====================

if os.path.exists(DATA_FILE):
    data = pd.read_csv(DATA_FILE, parse_dates=["Week_Start_Date"])
else:
    data = pd.DataFrame(columns=[
        "Year","Week_Start_Date","Cluster","Company","Stores","Area_mn_sqft",
        "Revenue_per_store","Margin_per_store","Net_additions",
        "LFL_growth","Bills_per_store","ABV"
    ])

# ===================== INPUT =====================

st.subheader("Submit / Edit Weekly Data")

year = st.selectbox("Year", YEARS)
week_date = st.selectbox(
    "Week Starting (Monday)",
    get_mondays(year),
    format_func=lambda x: x.strftime("%d-%b-%Y")
)

cluster = st.selectbox("Cluster", EXPECTED_CLUSTERS)
company = st.selectbox("Company", COMPANY_OPTIONS)

existing = data[
    (data["Year"] == year) &
    (data["Week_Start_Date"] == pd.to_datetime(week_date)) &
    (data["Cluster"] == cluster) &
    (data["Company"] == company)
]

existing_row = existing.iloc[0] if not existing.empty else None

if existing_row is not None:
    st.info("Editing existing submission")

with st.form("cluster_form"):
    col1, col2 = st.columns(2)

    with col1:
        stores = st.number_input("Total stores", value=int(existing_row["Stores"]) if existing_row is not None else 0)
        area = st.number_input("Retail area (mn sq. ft.)", value=float(existing_row["Area_mn_sqft"]) if existing_row is not None else 0.0)
        net_add = st.number_input("Net additions", value=int(existing_row["Net_additions"]) if existing_row is not None else 0)

    with col2:
        rev_store = st.number_input("Revenue per store (Cr)", value=float(existing_row["Revenue_per_store"]) if existing_row is not None else 0.0)
        margin_store = st.number_input("Margin per store (Cr)", value=float(existing_row["Margin_per_store"]) if existing_row is not None else 0.0)
        lfl = st.number_input("LFL growth %", value=float(existing_row["LFL_growth"]) if existing_row is not None else 0.0)
        bills = st.number_input("Bills per store", value=int(existing_row["Bills_per_store"]) if existing_row is not None else 0)
        abv = st.number_input("ABV", value=float(existing_row["ABV"]) if existing_row is not None else 0.0)

    submitted = st.form_submit_button("Submit / Update")

if submitted:
    new_row = {
        "Year": year,
        "Week_Start_Date": pd.to_datetime(week_date),
        "Cluster": cluster,
        "Company": company,
        "Stores": stores,
        "Area_mn_sqft": area,
        "Revenue_per_store": rev_store,
        "Margin_per_store": margin_store,
        "Net_additions": net_add,
        "LFL_growth": lfl,
        "Bills_per_store": bills,
        "ABV": abv
    }

    if existing_row is not None:
        data.loc[existing.index[0]] = new_row
        st.success("Updated successfully")
    else:
        data = pd.concat([data, pd.DataFrame([new_row])], ignore_index=True)
        st.success("Saved successfully")

    data.to_csv(DATA_FILE, index=False)

# ===================== USER HISTORY =====================

st.divider()
st.subheader("Your Submission History")
user_data = data[data["Cluster"] == cluster].sort_values("Week_Start_Date", ascending=False)
st.dataframe(user_data, use_container_width=True)

# ===================== HQ VIEW =====================

st.divider()
st.subheader("HQ View")

hq_access = st.text_input("HQ Password", type="password")

if hq_access == HQ_PASSWORD:

    tab1, tab2 = st.tabs(["📊 Dashboard", "🗂 Raw Data"])

    # ---------- Dashboard ----------
    with tab1:
        hq_year = st.selectbox("HQ Year", YEARS)
        hq_week = st.selectbox(
            "HQ Week",
            get_mondays(hq_year),
            format_func=lambda x: x.strftime("%d-%b-%Y")
        )

        filtered = data[
            (data["Year"] == hq_year) &
            (data["Week_Start_Date"] == pd.to_datetime(hq_week))
        ]

        submitted_clusters = set(filtered["Cluster"].unique())
        expected = set(EXPECTED_CLUSTERS)
        pending = sorted(list(expected - submitted_clusters))

        c1, c2, c3 = st.columns(3)
        c1.metric("Clusters Expected", len(expected))
        c2.metric("Clusters Submitted", len(submitted_clusters))
        c3.metric("Clusters Pending", len(pending))

        if pending:
            st.markdown('<div class="small-font">', unsafe_allow_html=True)
            st.table(pd.DataFrame({"Pending Clusters": pending}))
            st.markdown('</div>', unsafe_allow_html=True)

        # Download FULL data
        st.download_button(
            "Download Complete Database (Excel)",
            to_excel_download(data),
            file_name="Full_Cluster_Benchmark_Data.xlsx"
        )

    # ---------- Raw Data ----------
    with tab2:
        st.markdown("### Latest 20 Entries (No Filters)")
        latest20 = data.sort_values("Week_Start_Date", ascending=False).head(20)
        st.dataframe(latest20, use_container_width=True)
