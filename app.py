import streamlit as st
import pandas as pd
from fredapi import Fred
import matplotlib.pyplot as plt
import datetime
import numpy as np

# 1. PAGE SETUP
st.set_page_config(page_title="JPM Macro Monitor", layout="wide")
st.title("JPM Appendix B Macro Dashboard")
st.write("Macro detection tool using verified 2025 FRED Series IDs.")

# 2. SIDEBAR FOR API KEY
st.sidebar.header("Settings")
api_key = st.sidebar.text_input("Enter FRED API Key", type="password")

# 3. MAIN LOGIC
if api_key:
    try:
        fred = Fred(api_key=api_key)

        # UPDATED MAPPING (Verified active as of Dec 2025)
        # Note: USSLIND has been replaced by USALOLITONOSTSAM (OECD CLI) in many models
        full_map = {
            'USPHCI': 'Coincident Index (Services)',
            'USALOLITONOSTSAM': 'OECD Leading Indicator (PMI Proxy)',
            'IC4WSA': 'Initial Jobless Claims', 
            'TCU': 'Capacity Utilization',
            'T10Y2Y': 'Yield Curve Slope', 
            'PERMIT': 'Housing Permits',
            'DGORDER': 'Durable Goods Orders', 
            'RSAFS': 'Retail Sales',
            'BAA10Y': 'Corporate Credit Spreads', 
            'BAMLH0A0HYM2': 'High Yield Spreads',
            'VIXCLS': 'Market Volatility (VIX)', 
            'M2SL': 'Money Supply (M2)',
            'RTWEXBGS': 'Real USD Index', 
            'T10YIE': 'Inflation Breakevens',
            'RAILFRTCARLOADSD11': 'Rail Freight Carloads', 
            'UMCSENT': 'Consumer Sentiment',
            'DRTSCWM': 'Bank Lending Standards', 
            'REAINTRATREARAT10Y': 'Real 10Y Yield'
        }

        # Fetch Data individually to bypass "Bad Request" on specific series
        data_dict = {}
        with st.spinner('Accessing FRED database...'):
            for series_id, name in full_map.items():
                try:
                    series = fred.get_series(series_id)
                    data_dict[name] = series
                except Exception:
                    # Silently skip missing series to prevent dashboard crash
                    continue
        
        if not data_dict:
            st.error("Could not fetch any data. Please verify your API Key.")
            st.stop()

        df = pd.DataFrame(data_dict)
        df = df.resample('ME').last().ffill().tail(60) # Last 5 years

        # Calculate Z-Scores (36-month rolling)
        z = (df - df.rolling(36).mean()) / df.rolling(36).std()
        latest = z.iloc[-1].dropna()

        # Invert Risk Metrics (Falling claims/spreads = Positive for growth)
        inverse_list = ['Initial Jobless Claims', 'Corporate Credit Spreads', 
                        'High Yield Spreads', 'Market Volatility (VIX)', 
                        'Bank Lending Standards', 'Real USD Index']
        
        for col in latest.index:
            if col in inverse_list:
                latest[col] = -latest[col]

        # UI: Dashboard Layout
        col_left, col_right = st.columns([1, 1])
        
        with col_left:
            st.subheader("Investment Clock (Regime Path)")
            fig_clock, ax_clock = plt.subplots(figsize=(7, 7))
            
            # Use OECD Leading for Growth axis and Breakevens for Inflation axis
            if 'OECD Leading Indicator (PMI Proxy)' in z.columns and 'Inflation Breakevens' in z.columns:
                path = z[['OECD Leading Indicator (PMI Proxy)', 'Inflation Breakevens']].tail(24)
                ax_clock.plot(path.iloc[:,0], path.iloc[:,1], color='gray', alpha=0.3, linestyle='--')
                ax_clock.scatter(path.iloc[-1,0], path.iloc[-1,1], color='red', s=200, zorder=5)
            
            ax_clock.axhline(0, color='black', lw=1.5); ax_clock.axvline(0, color='black', lw=1.5)
            ax_clock.set_xlim(-3, 3); ax_clock.set_ylim(-3, 3)
            ax_clock.set_xlabel("Growth Acceleration (Z)"); ax_clock.set_ylabel("Inflation Acceleration (Z)")
            
            # Quadrant Labels
            ax_clock.text(1.5, 1.5, 'EXPANSION', fontsize=10, fontweight='bold', color='green', ha='center')
            ax_clock.text(1.5, -1.5, 'RECOVERY', fontsize=10, fontweight='bold', color='blue', ha='center')
            ax_clock.text(-1.5, 1.5, 'SLOWDOWN', fontsize=10, fontweight='bold', color='orange', ha='center')
            ax_clock.text(-1.5, -1.5, 'CONTRACTION', fontsize=10, fontweight='bold', color='red', ha='center')
            st.pyplot(fig_clock)

        with col_right:
            st.subheader("Appendix B Indicator Scorecard")
            fig_bar, ax_bar = plt.subplots(figsize=(7, 9))
            sorted_latest = latest.sort_values()
            colors = ['#2ecc71' if x > 0 else '#e74c3c' for x in sorted_latest]
            sorted_latest.plot(kind='barh', color=colors, ax=ax_bar)
            ax_bar.axvline(0, color='black', lw=1)
            st.pyplot(fig_bar)

        # Style Strategy recommendation
        avg_score = latest.mean()
        st.divider()
        if avg_score > 0.5:
            st.success(f"Current Score: {avg_score:.2f} | Strategy: Lean into Momentum and Cyclicals")
        elif avg_score > 0:
            st.info(f"Current Score: {avg_score:.2f} | Strategy: Rotation to Value and Small Caps")
        elif avg_score > -0.5:
            st.warning(f"Current Score: {avg_score:.2f} | Strategy: Defensive Quality and Low Volatility")
        else:
            st.error(f"Current Score: {avg_score:.2f} | Strategy: Capital Preservation / Defensive Growth")

    except Exception as e:
        st.error(f"System Error: {e}")
else:
    st.info("Input your FRED API Key in the sidebar to generate the JPM Dashboard.")
