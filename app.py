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

# 3. DASHBOARD LOGIC
api_key = st.session_state.api_key

try:
    fred = Fred(api_key=api_key)
    
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

    data_dict = {}
    with st.spinner('Accessing Global Macro Stream...'):
        for series_id, name in full_map.items():
            try:
                data_dict[name] = fred.get_series(series_id)
            except: continue
    
    df = pd.DataFrame(data_dict).resample('ME').last().ffill().tail(60)
    z = (df - df.rolling(36).mean()) / df.rolling(36).std()
    latest = z.iloc[-1].dropna()

    inv = ['Jobless Claims', 'Credit Spreads', 'HY Spreads', 'VIX', 'Lending Standards', 'Real USD Index']
    for col in latest.index:
        if col in inv: latest[col] = -latest[col]

    # HEADER
    st.title("🏛️ Institutional Macro Dashboard")
    st.caption(f"Status: Synchronized | Refreshed: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    st.divider()

    # METRICS
    avg_score = latest.mean()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Regime Score", f"{avg_score:.2f}")
    m2.metric("Growth Z", f"{latest.get('Leading Index', 0):.2f}")
    m3.metric("Inflation Z", f"{latest.get('Breakevens', 0):.2f}")
    m4.metric("Risk Sentiment", "Risk-On" if latest.get('VIX', 0) > 0 else "Risk-Off")

    # CHARTS
    c1, c2 = st.columns([1, 1])

    with c1:
        st.write("### Investment Clock Path")
        path_df = z[['Leading Index', 'Breakevens']].tail(24).reset_index()
        # FIXED: Corrected scatter plot syntax
        fig_clock = px.scatter(
            path_df, 
            x='Leading Index', 
            y='Breakevens',
            text=path_df['index'].dt.strftime('%b %y'),
            template="plotly_dark"
        )
        fig_clock.add_shape(type="line", x0=-3, y0=0, x1=3, y1=0, line=dict(color="gray", dash="dash"))
        fig_clock.add_shape(type="line", x0=0, y0=-3, x1=0, y1=3, line=dict(color="gray", dash="dash"))
        fig_clock.update_traces(mode='lines+markers+text', marker=dict(size=12, color='gold'), textposition='top center')
        fig_clock.update_layout(xaxis_title="Growth (Z)", yaxis_title="Inflation (Z)", height=600)
        st.plotly_chart(fig_clock, use_container_width=True)

    with c2:
        st.write("### Indicator Scorecard")
        score_df = latest.sort_values().reset_index()
        score_df.columns = ['Indicator', 'Score']
        fig_bar = px.bar(
            score_df, 
            x='Score', 
            y='Indicator', 
            orientation='h',
            color='Score', 
            color_continuous_scale='RdYlGn',
            template="plotly_dark"
        )
        fig_bar.update_layout(showlegend=False, height=600, coloraxis_showscale=False)
        st.plotly_chart(fig_bar, use_container_width=True)

    # STYLE RECOMMENDATION TABLE
    st.write("### Style Allocation Guidance")
    style_data = {
        "Regime": ["Expansion", "Recovery", "Slowdown", "Contraction"],
        "Top Styles": ["Momentum, Cyclicals", "Value, Small Caps", "Quality, Low Vol", "Defensive Growth, Cash"],
        "Asset Allocation": ["Overweight Equities", "Overweight Value", "Overweight Defensive", "Overweight Bonds/Gold"]
    }
    st.table(pd.DataFrame(style_data))

    if st.button("Reset Terminal"):
        st.session_state.authenticated = False
        st.rerun()

except Exception as e:
    st.error(f"Terminal Fault: {e}")
    if st.button("Return to Gateway"):
        st.session_state.authenticated = False
        st.rerun()
