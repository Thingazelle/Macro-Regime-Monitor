import streamlit as st
import pandas as pd
import pandas_datareader.data as web
import matplotlib.pyplot as plt
import datetime
import numpy as np

st.set_page_config(page_title="JPM Macro Monitor", layout="wide")
st.title("Full JPM Appendix B Macro Dashboard")

api_key = st.sidebar.text_input("Enter FRED API Key", type="password")

if api_key:
    try:
        # Full Mapping (20+ Indicators)
        full_map = {
            'USSLIND': 'Leading Index (PMI)', 'USPHCI': 'Coincident (Services)',
            'IC4WSA': 'Jobless Claims', 'MCUMFN': 'Capacity Util',
            'T10Y2Y': 'Yield Curve', 'PERMIT': 'Housing Permits',
            'DGORDER': 'New Orders', 'RSAFS': 'Retail Sales',
            'BAA10Y': 'Credit Spreads', 'BAMLH0A0HYM2': 'HY Spreads',
            'VIXCLS': 'VIX', 'M2SL': 'Money Supply',
            'DTWEXBGS': 'USD Index', 'T10YIE': 'Breakevens',
            'RAILFRTCARLOADS': 'Rail Freight', 'UMCSENT': 'Cons Sentiment',
            'DRTSCWM': 'Lending Standards', 'REAINTRATREARAT10Y': 'Real Yields'
        }

        start = datetime.datetime.now() - datetime.timedelta(days=365*10)
        df = web.DataReader(list(full_map.keys()), 'fred', start, api_key=api_key)
        df = df.resample('ME').last().ffill()
        df.columns = [full_map[col] for col in df.columns]

        # Calculate Z-Scores
        z = (df - df.rolling(36).mean()) / df.rolling(36).std()
        latest = z.iloc[-1].dropna()

        # Invert Risk Metrics
        inverse_list = ['Jobless Claims', 'Credit Spreads', 'HY Spreads', 'VIX', 'Lending Standards', 'USD Index']
        for col in latest.index:
            if col in inverse_list:
                latest[col] = -latest[col]

        # UI: Big Summary
        score = latest.mean()
        st.subheader(f"Aggregate Regime Score: {score:.2f}")
        
        # Quadrant Visualization
        col_left, col_right = st.columns([1, 1])
        
        with col_left:
            st.write("Style Cycle (2-Year Path)")
            fig_clock, ax_clock = plt.subplots(figsize=(7, 7))
            path = z[['Leading Index (PMI)', 'Breakevens']].tail(24)
            ax_clock.plot(path.iloc[:,0], path.iloc[:,1], color='gray', alpha=0.3)
            ax_clock.scatter(path.iloc[-1,0], path.iloc[-1,1], color='red', s=150)
            ax_clock.axhline(0, color='black', lw=1); ax_clock.axvline(0, color='black', lw=1)
            ax_clock.set_xlabel("Growth (Z)"); ax_clock.set_ylabel("Inflation (Z)")
            st.pyplot(fig_clock)

        with col_right:
            st.write("Appendix B Indicator Scorecard")
            fig_bar, ax_bar = plt.subplots(figsize=(7, 9))
            # Color coding (Green for positive contribution to regime, Red for negative)
            colors = ['green' if x > 0 else 'red' for x in latest.sort_values()]
            latest.sort_values().plot(kind='barh', color=colors, ax=ax_bar)
            st.pyplot(fig_bar)

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("Please enter your FRED API Key in the sidebar.")
