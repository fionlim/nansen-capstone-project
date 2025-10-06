#!/usr/bin/env python3
import streamlit as st
import pandas as pd

from components.tgm_holders_horizontal_bar_chart import render_holder_flows_horizontal_bar_chart
from components.tgm_holders_donut_chart import render_holders_donut_chart
from components.tgm_pnl_leaderboard_bubble_chart import render_pnl_leaderboard_bubble_chart
from components.tgm_dextrades_combo_chart import render_dex_trades_hourly

st.set_page_config(page_title="TGM Dashboard", layout="wide")

# Handle authentication
if not st.user.is_logged_in:
    st.title("Nansen.ai API Dashboard")
    st.write("Please log in to access the dashboard.")
    if st.button("Log in"):
        st.login()
    st.stop()

st.set_page_config(page_title="TGM", layout="wide")
st.title("TGM Dashboard")

# --- Inputs ---
c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
with c1:
    token = st.text_input(
        "Token address", placeholder="2zMMhcVQEXDtdE6vsFS7S7D5oUodfJHE8vd1gnBouauv"
    )
    # token = token.strip().lower()
with c2:
    chain = st.selectbox(
        "Chain", ["solana","ethereum", "arbitrum", "optimism", "base", "bnb", "polygon"], index=0
    )
with c3:
    period = st.selectbox("Period", ["1h", "24h", "7d", "30d"], index=0)
with c4:
    st.markdown("<br>", unsafe_allow_html=True)
    refresh_data = st.button("🔄 Refresh Metrics", use_container_width=True)

# --- Main layout: Holder Distributions ---
if not token:
    st.info("👆 Enter a token address above to see detailed metrics")

# Input widgets for payload variables
st.subheader('Holder Distribution Query Settings')

aggregate_by_entity = st.selectbox('Aggregate by Entity', [False, True], index=0)

# Update payload with widget values

render_holders_donut_chart(chain, token, aggregate_by_entity)
render_holder_flows_horizontal_bar_chart(chain, token, aggregate_by_entity)
render_pnl_leaderboard_bubble_chart(chain, token)
render_dex_trades_hourly(chain, token)
