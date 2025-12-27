import streamlit as st
import pandas as pd
import pandas_datareader.data as web
import matplotlib.pyplot as plt
import datetime
import numpy as np

st.title("JPM Appendix B: Macro Regime Detector")

# Add a sidebar for the API Key
api_key = st.sidebar.text_input("Enter FRED API Key", type="password")

if api_key:
    # [PASTE THE REST OF THE CALCULATION CODE HERE]
    # Use st.pyplot(plt) instead of plt.show()
else:
    st.warning("Please enter your FRED API Key in the sidebar to begin.")
