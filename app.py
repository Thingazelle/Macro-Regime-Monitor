import streamlit as st
import pandas as pd
from fredapi import Fred
import matplotlib.pyplot as plt
import datetime
import numpy as np

# 1. PAGE SETUP
st.set_page_config(page_title="JPM Macro Monitor", layout="wide")
st.title("JPM Appendix B Macro Dashboard")
st.write("Detection tool based on the J.P. Morgan Framework for Style Investing (FRED Stable Version).")

# 2. SIDEBAR FOR API KEY
st.sidebar.header("Settings")
api_key = st.sidebar.text_input("Enter FRED API Key", type="password")

# 3. MAIN LOGIC
if api_key:
    try:
        # Initialize FRED API
        fred = Fred(api_key=api_key)

        # Updated Stable Mapping (Verified IDs)
        full_map = {
            'USSLIND': 'Leading Index (PMI)', 
            'USPHCI': 'Coincident (Services)',
            'IC4WSA': 'Jobless Claims', 
            'MCUMFN': 'Capacity Util',
            'T10Y2Y': 'Yield Curve', 
            'PERMIT': 'Housing Permits',
            'DGORDER': 'New Orders', 
            'RSAFS': 'Retail Sales',
            'BAA10Y': 'Credit Spreads', 
            'BAMLH0A0HYM2': 'HY Spreads',
            'VIXCLS': 'VIX', 
            'M2SL': 'Money Supply',
            'RTWEXBGS': 'Real USD Index', 
            'T10YIE': 'Breakevens',
            'FRGHTPNUS': 'Freight Index', 
            'UMCSENT': 'Cons Sentiment',
            'DRTSCWM': 'Lending Standards', 
            'REAINTRATREARAT10Y': 'Real Yields'
        }

        # Fetch Data individually to catch any specific series errors
        data_dict = {}
        for series_id, name in full_map.items():
            try:
                series = fred.get_series(series_id)
                data_dict[name] = series
            except Exception as inner_e:
                st.warning(f"Skipping {name} ({series_id}): {inner_e}")
        
        df = pd.DataFrame(data_dict)
        df = df.resample('ME').last().ffill().tail(120)

        # Calculate Z-Scores
        z = (df - df.rolling(36).mean()) / df.rolling(36).std()
        latest = z.iloc[-1].dropna()

        # Invert Risk Metrics
        inverse_list = ['Jobless Claims', 'Credit Spreads', 'HY Spreads', 'VIX', 'Lending Standards', 'Real USD Index']
        for col in latest.index:
            if col in inverse_list:
                latest[col] = -latest[col]

        # UI: Dashboard Layout
        col_left, col_right = st.columns([1, 1])
        
        with col_left:
            st.subheader("Investment Clock (Regime Path)")
            fig_clock, ax_clock = plt.subplots(figsize=(7, 7))
            path = z[['Leading Index (PMI)', 'Breakevens']].tail(24)
            ax_clock.plot(path.iloc[:,0], path.iloc[:,1], color='gray', alpha=0.3, linestyle='--')
            ax_clock.scatter(path.iloc[-1,0], path.iloc[-1,1], color='red', s=200, zorder=5)
            ax_clock.axhline(0, color='black', lw=1.5); ax_clock.axvline(0, color='black', lw=1.5)
            ax_clock.set_xlim(-3, 3); ax_clock.set_ylim(-3, 3)
            ax_clock.set_xlabel("Growth Z-Score"); ax_clock.set_ylabel("Inflation Z-Score")
            
            # Quadrant Labels
            ax_clock.text(1.5, 1.5, 'EXPANSION', fontsize=10, fontweight='bold', color='green', ha='center')
            ax_clock.text(1.5, -1.5, 'RECOVERY', fontsize=10, fontweight='bold', color='blue', ha='center')
            ax_clock.text(-1.5, 1.5, 'SLOWDOWN', fontsize=10, fontweight='bold', color='orange', ha='center')
            ax_clock.text(-1.5, -1.5, 'CONTRACTION', fontsize=10, fontweight='bold', color='red', ha='center')
            st.pyplot(fig_clock)

        with col_right:
            st.subheader("Indicator Detail Scorecard")
            fig_bar, ax_bar = plt.subplots(figsize=(7, 9))
            sorted_latest = latest.sort_values()
            colors = ['#2ecc71' if x > 0 else '#e74c3c' for x in sorted_latest]
            sorted_latest.plot(kind='barh', color=colors, ax=ax_bar)
            ax_bar.axvline(0, color='black', lw=1)
            st.pyplot(fig_bar)

        st.divider()
        avg_score = latest.mean()
        st.write(f"### Current Aggregate Regime Score: {avg_score:.2f}")

    except Exception as e:
        st.error(f"Critical Error: {e}")
else:
    st.info("Please enter your FRED API Key in the sidebar.")
