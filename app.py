import pandas as pd
import pandas_datareader.data as web
import matplotlib.pyplot as plt
import datetime

# 1. SETUP
FRED_API_KEY = '6fb9a24dabb670baab332ab6a281da1b '
start = datetime.datetime.now() - datetime.timedelta(days=365*10)

# 2. FULL MAPPING (All available on FRED)
fred_indicators = {
    'USSLIND': 'Leading Index (PMI Proxy)',
    'USPHCI': 'Coincident Index (Services Proxy)',
    'IC4WSA': 'Jobless Claims',
    'MCUMFN': 'Capacity Utilization',
    'BAA10Y': 'Credit Spreads',
    'BAMLH0A0HYM2': 'High Yield Spreads',
    'UMCSENT': 'Consumer Sentiment',
    'T10Y2Y': 'Yield Curve',
    'DTWEXBGS': 'USD Index',
    'M2SL': 'Money Supply',
    'TRUCKD11': 'Truck Tonnage (Baltic Proxy)',
    'T10YIE': 'Inflation Breakevens',
    'PERMIT': 'Housing Permits'
}

# 3. FETCH DATA
print("Fetching JPM Framework indicators from FRED...")
df = web.DataReader(list(fred_indicators.keys()), 'fred', start, api_key=FRED_API_KEY)
df = df.resample('ME').last().ffill()
df.columns = [fred_indicators[col] for col in df.columns]

# 4. CALCULATE LEADING-LAGGING SPREAD (Appendix B, Page 19)
# JPM looks at whether the Leading Index is outpacing the Coincident (Lagging) one.
df['Lead-Lag Spread'] = df['Leading Index (PMI Proxy)'] - df['Coincident Index (Services Proxy)']

# 5. SCORING (Z-Score relative to 3-Year Trend)
z = (df - df.rolling(36).mean()) / df.rolling(36).std()

# 6. SIGNAL KEY (Assigning + / - based on JPM Appendix B)
def jpm_signal_key(val, name):
    # Inverting logic for Risk/Claims
    inverse = ['Claims', 'Spreads']
    if any(x in name for x in inverse):
        val = -val
        
    if val > 1.2: return "++ Expansion"
    elif val > 0: return "+ Recovery"
    elif val > -1.2: return "- Slowdown"
    else: return "-- Contraction"

latest = z.iloc[-1]
scorecard = pd.DataFrame({
    'Z-Score': latest,
    'Signal': [jpm_signal_key(v, n) for n, v in latest.items()]
}).sort_values('Z-Score', ascending=False)

print("\n--- JPM APPENDIX B: FRED-ONLY DASHBOARD ---")
print(scorecard)

# Summary Analysis
bullish_signals = scorecard[scorecard['Signal'].str.contains('\+')].shape[0]
print(f"\nNet Bullish Signals: {bullish_signals} / {len(scorecard)}")
