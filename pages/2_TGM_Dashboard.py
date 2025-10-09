import streamlit as st
from components.sm_gauge import render_gauge_charts
from components.tgm_token_metrics import render_token_metrics

st.set_page_config(page_title="TGM", layout="wide")
st.title("TGM Dashboard")

# --- Inputs ---
c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
with c1:
    token = st.text_input(
        "Token address", placeholder="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
    )
    token = token.strip().lower()
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
if not token:
    st.info("👆 Enter a token address above to see detailed metrics")

left_col, right_col = st.columns(2, gap="large")

with left_col:
    with st.container():
        gauge_data = render_gauge_charts(token, chain, period)
        # st.write(gauge_data)

        if not gauge_data:
            st.error("Failed to load Smart Money data.")

with right_col:
    with st.container():
        render_token_metrics(token, chain, period)