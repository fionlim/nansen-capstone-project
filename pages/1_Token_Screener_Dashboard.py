import streamlit as st
from datetime import datetime, timedelta
from components.smart_money_gauge import render_gauge_charts

st.set_page_config(page_title="TGM", layout="wide")
st.title("TGM Dashboard")

# --- Inputs ---
c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
with c1:
    token = st.text_input(
        "Token address", placeholder="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
    )
with c2:
    chain = st.selectbox(
        "Chain", ["ethereum", "arbitrum", "optimism", "base", "bnb", "polygon"], index=0
    )
with c3:
    period = st.selectbox("Period", ["1h", "24h", "7d", "30d"], index=0)
with c4:
    st.markdown("<br>", unsafe_allow_html=True)
    refresh_data = st.button("🔄 Refresh Metrics", use_container_width=True)


# --- Main layout: Smart Money Gauges on left, Token metrics on right ---
left_col, right_col = st.columns(2, gap="large")

with left_col:
    with st.container():
        if token:
            gauge_data = render_gauge_charts(token, chain, period)
            st.write(gauge_data) # FOR DEBUGGING, remove before commit

            if not gauge_data:
                st.error("Failed to load Smart Money data.")
        else:
            st.info("👆 Enter a token address above to see Smart Money activity")

with right_col:
    with st.container():
        st.subheader("Token Metrics")