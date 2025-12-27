import streamlit as st
import pandas as pd
from fredapi import Fred
import plotly.graph_objects as go
import plotly.express as px
import datetime
import numpy as np

# 1. PAGE SETUP & THEME
st.set_page_config(page_title="JPM Macro Terminal", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3e4251; }
    [data-testid="stHeader"] { background: rgba(0,0,0,0); }
    section[data-testid="stSidebar"] { display: none; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #1e2130; border-radius: 5px; color: white; }
    </style>
    """, unsafe_allow_html=True)

# 2. AUTHENTICATION
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("JPM Macro Terminal")
        st.subheader("Secure Access Gateway")
        key_input = st.text_input("Enter FRED API Key", type="password")
        if st.button("Initialize Terminal"):
            if key_input:
                st.session_state.api_key = key_input
                st.session_state.authenticated = True
                st.rerun()
    st.stop()

# 3. TERMINAL LOGIC
try:
    fred = Fred(api_key=st.session_state.api_key)
    
    full_map = {
        'USALOLITONOSTSAM': 'Leading Index', 'USPHCI': 'Coincident Index',
        'IC4WSA': 'Jobless Claims', 'TCU': 'Capacity Util',
        'T10Y2Y': 'Yield Curve', 'PERMIT': 'Housing Permits',
        'DGORDER': 'New Orders', 'RSAFS': 'Retail Sales',
        'BAA10Y': 'Credit Spreads', 'BAMLH0A0HYM2': 'HY Spreads',
        'VIXCLS': 'VIX', 'M2SL': 'Money Supply',
        'RTWEXBGS': 'Real USD Index', 'T10YIE': 'Breakevens',
        'RAILFRTCARLOADSD11': 'Rail Freight', 'UMCSENT': 'Cons Sentiment',
        'DRTSCWM': 'Lending Standards', 'REAINTRATREARAT10Y': 'Real Yields'
    }

    @st.cache_data(ttl=3600)
    def fetch_data(api_key):
        data_dict = {}
        for series_id, name in full_map.items():
            try:
                data_dict[name] = fred.get_series(series_id)
            except:
                continue
        return pd.DataFrame(data_dict).resample('ME').last().ffill()

    raw_df = fetch_data(st.session_state.api_key)
    df = raw_df.tail(120)
    z = (df - df.rolling(36).mean()) / df.rolling(36).std()
    latest_z = z.iloc[-1].dropna()

    inv = ['Jobless Claims', 'Credit Spreads', 'HY Spreads', 'VIX', 'Lending Standards', 'Real USD Index']
    adjusted_z = latest_z.copy()
    for col in adjusted_z.index:
        if col in inv: adjusted_z[col] = -adjusted_z[col]

    # UI LAYOUT
    st.title("Institutional Macro Dashboard")
    tab1, tab2, tab3 = st.tabs(["Regime Detection", "Historical Explorer", "Release Calendar"])

    with tab1:
        c1, c2 = st.columns([1, 1])
        with c1:
            st.write("### Investment Clock Path")
            path_df = z[['Leading Index', 'Breakevens']].tail(12).reset_index()
            
            fig_clock = go.Figure()
            # Quadrant Rectangles
            fig_clock.add_vrect(x0=0, x1=3, y0=0, y1=3, fillcolor="green", opacity=0.05, layer="below", line_width=0)
            fig_clock.add_vrect(x0=-3, x1=0, y0=-3, y1=0, fillcolor="red", opacity=0.05, layer="below", line_width=0)
            
            # Historical Path
            fig_clock.add_trace(go.Scatter(
                x=path_df['Leading Index'], y=path_df['Breakevens'],
                mode='lines+markers', line=dict(color='rgba(255, 255, 255, 0.2)', width=2),
                marker=dict(size=8, color='rgba(255, 255, 255, 0.5)'),
                name='Path'
            ))
            
            # Current Point
            fig_clock.add_trace(go.Scatter(
                x=[path_df['Leading Index'].iloc[-1]], y=[path_df['Breakevens'].iloc[-1]],
                mode='markers+text', marker=dict(size=20, color='gold', line=dict(width=2, color='white')),
                text=["CURRENT"], textposition="top right", name='Current Status'
            ))

            fig_clock.update_layout(
                template="plotly_dark", height=600,
                xaxis=dict(title="Growth (Z-Score)", range=[-3, 3], zeroline=True, zerolinewidth=2),
                yaxis=dict(title="Inflation (Z-Score)", range=[-3, 3], zeroline=True, zerolinewidth=2),
                showlegend=False
            )
            st.plotly_chart(fig_clock, use_container_width=True)

        with c2:
            st.write("### Indicator Scorecard")
            score_df = adjusted_z.sort_values().reset_index()
            score_df.columns = ['Indicator', 'Score']
            fig_bar = px.bar(score_df, x='Score', y='Indicator', orientation='h',
                             color='Score', color_continuous_scale='RdYlGn', template="plotly_dark")
            fig_bar.update_layout(height=600, coloraxis_showscale=False)
            st.plotly_chart(fig_bar, use_container_width=True)

    with tab2:
        st.write("### Historical Data Explorer")
        selected_indicator = st.selectbox("Select Indicator", options=list(full_map.values()))
        fig_hist = px.line(raw_df, y=selected_indicator, template="plotly_dark")
        fig_hist.update_traces(line_color='#00d1ff')
        st.plotly_chart(fig_hist, use_container_width=True)

    with tab3:
        st.write("### Macro Release Calendar (Typical Monthly Schedule)")
        calendar_data = {
            "Indicator": ["Jobless Claims", "VIX", "Yield Curve", "Retail Sales", "Housing Permits", "Industrial Production", "CPI / Breakevens", "PMI / Leading Index"],
            "Frequency": ["Weekly (Thursday)", "Real-time", "Daily", "Monthly (Mid-month)", "Monthly (Mid-month)", "Monthly (Mid-month)", "Monthly (Mid-month)", "Monthly (Start-month)"],
            "Reporting Agency": ["Dept of Labor", "CBOE", "Treasury", "Census Bureau", "Census Bureau", "Federal Reserve", "BLS", "OECD / Conference Board"]
        }
        st.table(pd.DataFrame(calendar_data))

    if st.button("Reset Terminal"):
        st.session_state.authenticated = False
        st.rerun()

except Exception as e:
    st.error(f"Terminal Fault: {e}")
