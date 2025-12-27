import streamlit as st
import pandas as pd
from fredapi import Fred
import plotly.graph_objects as go
import plotly.express as px
import datetime
import numpy as np

# 1. PAGE SETUP & CLASSY THEME
st.set_page_config(page_title="JPM Macro Terminal", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS for a professional dark "Terminal" look
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3e4251; }
    [data-testid="stHeader"] { background: rgba(0,0,0,0); }
    /* Hide sidebar if API key is present */
    section[data-testid="stSidebar"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

# 2. LOGIN / API KEY HANDLER
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🏛️ JPM Macro Terminal")
        st.subheader("Secure Access Gateway")
        key_input = st.text_input("Enter FRED API Key to Initialize", type="password")
        if st.button("Initialize Terminal"):
            if key_input:
                st.session_state.api_key = key_input
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Invalid Key")
    st.stop()

# 3. DASHBOARD LOGIC (AUTHENTICATED)
api_key = st.session_state.api_key

try:
    fred = Fred(api_key=api_key)
    
    # Mapping for indicators
    full_map = {
        'USALOLITONOSTSAM': 'Leading Index', 'USPHCI': 'Coincident Index',
        'IC4WSA': 'Jobless Claims', 'MCUMFN': 'Capacity Util',
        'T10Y2Y': 'Yield Curve', 'PERMIT': 'Housing Permits',
        'DGORDER': 'New Orders', 'RSAFS': 'Retail Sales',
        'BAA10Y': 'Credit Spreads', 'BAMLH0A0HYM2': 'HY Spreads',
        'VIXCLS': 'VIX', 'M2SL': 'Money Supply',
        'RTWEXBGS': 'Real USD Index', 'T10YIE': 'Breakevens',
        'RAILFRTCARLOADSD11': 'Rail Freight', 'UMCSENT': 'Cons Sentiment',
        'DRTSCWM': 'Lending Standards', 'REAINTRATREARAT10Y': 'Real Yields'
    }

    # Data Fetching
    data_dict = {}
    for series_id, name in full_map.items():
        try:
            data_dict[name] = fred.get_series(series_id)
        except: continue
    
    df = pd.DataFrame(data_dict).resample('ME').last().ffill().tail(60)
    z = (df - df.rolling(36).mean()) / df.rolling(36).std()
    latest = z.iloc[-1].dropna()

    # Invert Risk Metrics
    inv = ['Jobless Claims', 'Credit Spreads', 'HY Spreads', 'VIX', 'Lending Standards', 'Real USD Index']
    for col in latest.index:
        if col in inv: latest[col] = -latest[col]

    # DASHBOARD HEADER
    st.title("🏛️ Institutional Macro Dashboard")
    st.caption(f"Status: Synchronized | Refreshed: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    st.divider()

    # TOP ROW: KEY METRICS
    m1, m2, m3, m4 = st.columns(4)
    avg_score = latest.mean()
    m1.metric("Regime Score", f"{avg_score:.2f}", delta_color="normal")
    m2.metric("Growth Z", f"{latest.get('Leading Index', 0):.2f}")
    m3.metric("Inflation Z", f"{latest.get('Breakevens', 0):.2f}")
    m4.metric("Risk Sentiment", "Risk-On" if latest.get('VIX', 0) > 0 else "Risk-Off")

    # SECOND ROW: INTERACTIVE CHARTS
    c1, c2 = st.columns([1, 1])

    with c1:
        st.write("### Investment Clock Path")
        path_df = z[['Leading Index', 'Breakevens']].tail(24).reset_index()
        fig_clock = px.scatter(path_df, x='Leading Index',
