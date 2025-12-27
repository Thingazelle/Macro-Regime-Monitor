import streamlit as st
import pandas as pd
from fredapi import Fred
import plotly.graph_objects as go
import plotly.express as px
import datetime
import numpy as np

# Page configuration
st.set_page_config(page_title="JPM Macro Terminal", layout="wide", initial_sidebar_state="collapsed")

# Professional Terminal Styling
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 5px; border: 1px solid #3e4251; }
    [data-testid="stHeader"] { background: rgba(0,0,0,0); }
    section[data-testid="stSidebar"] { display: none; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; background-color: #1e2130; border-radius: 5px; color: white; }
    </style>
    """, unsafe_allow_html=True)

# Authentication Handler
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("JPM Macro Terminal")
        st.subheader("Authentication Required")
        key_input = st.text_input("Enter FRED API Key", type="password")
        if st.button("Access Terminal"):
            if key_input:
                st.session_state.api_key = key_input
                st.session_state.authenticated = True
                st.rerun()
    st.stop()

# Macro Indicator Logic
try:
    fred = Fred(api_key=st.session_state.api_key)
    
    # Exhaustive Appendix B Mapping
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
    def fetch_all_data(api_key):
        data_dict = {}
        for series_id, name in full_map.items():
            try:
                data_dict[name] = fred.get_series(series_id)
            except:
                continue
        return pd.DataFrame(data_dict).resample('ME').last().ffill()

    raw_df = fetch_all_data(st.session_state.api_key)
    # Calculation for Z-Scores based on 36-month rolling window
    z_df = (raw_df - raw_df.rolling(36).mean()) / raw_df.rolling(36).std()
    latest_z = z_df.iloc[-1].dropna()

    # Inversion Logic for Risk Indicators
    inv = ['Jobless Claims', 'Credit Spreads', 'HY Spreads', 'VIX', 'Lending Standards', 'Real USD Index']
    scorecard_z = latest_z.copy()
    for col in scorecard_z.index:
        if col in inv: scorecard_z[col] = -scorecard_z[col]

    # Dashboard Interface
    st.title("Institutional Macro Terminal")
    t1, t2, t3 = st.tabs(["Regime Detection", "Historical Data", "Release Schedule"])

    with t1:
        col_left, col_right = st.columns([1, 1])
        with col_left:
            st.write("### Investment Clock")
            # Limit path to 12 months for clarity
            path = z_df[['Leading Index', 'Breakevens']].tail(12).reset_index()
            
            fig = go.Figure()
            # Quadrant Lines
            fig.add_shape(type="line", x0=-3, y0=0, x1=3, y1=0, line=dict(color="#3e4251", width=2))
            fig.add_shape(type="line", x0=0, y0=-3, x1=0, y1=3, line=dict(color="#3e4251", width=2))
            
            # Trail path
            fig.add_trace(go.Scatter(
                x=path['Leading Index'], y=path['Breakevens'],
                mode='lines+markers',
                line=dict(color='rgba(255,255,255,0.2)', width=2),
                marker=dict(size=6, color='rgba(255,255,255,0.4)'),
                name='12 Month Path'
            ))
            
            # Current location highlighted
            fig.add_trace(go.Scatter(
                x=[path['Leading Index'].iloc[-1]], 
                y=[path['Breakevens'].iloc[-1]],
                mode='markers+text',
                marker=dict(size=18, color='#ffcc00', line=dict(width=2, color='white')),
                text=["CURRENT POSITION"],
                textposition="top right",
                name='Current'
            ))

            fig.update_layout(
                template="plotly_dark", height=550, margin=dict(l=20, r=20, t=20, b=20),
                xaxis=dict(title="Growth Acceleration (Z)", range=[-3, 3], showgrid=False),
                yaxis=dict(title="Inflation Acceleration (Z)", range=[-3, 3], showgrid=False),
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_right:
            st.write("### Indicator Scorecard")
            score_data = scorecard_z.sort_values().reset_index()
            score_data.columns = ['Indicator', 'Z-Score']
            fig_bar = px.bar(score_data, x='Z-Score', y='Indicator', orientation='h',
                             color='Z-Score', color_continuous_scale='RdYlGn', 
                             template="plotly_dark")
            fig_bar.update_layout(height=550, coloraxis_showscale=False, margin=dict(t=20))
            st.plotly_chart(fig_bar, use_container_width=True)

    with t2:
        st.write("### Historical Time Series")
        selection = st.selectbox("Select Macro Variable", options=list(full_map.values()))
        fig_line = px.line(raw_df, y=selection, template="plotly_dark")
        fig_line.update_traces(line_color='#00d1ff', line_width=2)
        st.plotly_chart(fig_line, use_container_width=True)

    with t3:
        st.write("### Data Release Calendar")
        calendar = {
            "Metric": ["Employment / Claims", "Consumer Prices", "Retail Activity", "Monetary Policy", "Manufacturing"],
            "Typical Release": ["Every Thursday", "Monthly (Mid)", "Monthly (Mid)", "Every 6 Weeks", "Monthly (Start)"],
            "Source": ["Dept of Labor", "BLS", "Census Bureau", "Federal Reserve", "ISM / OECD"]
        }
        st.table(pd.DataFrame(calendar))

    if st.button("Reset Terminal Session"):
        st.session_state.authenticated = False
        st.rerun()

except Exception as e:
    st.error(f"Error encountered: {e}")
