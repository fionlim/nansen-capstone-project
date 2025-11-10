#!/usr/bin/env python3
import json
import streamlit as st
from streamlit_javascript import st_javascript

from components.sm_netflow_scatterplot import render_netflow_scatterplot
from components.sm_trade_value_podium import render_dex_trades_podium
from components.sm_netflow_podium import render_netflow_podium
from components.pfl_wallet_token_tracker import render_wallet_token_tracker


def main():
    st.set_page_config(page_title="Landing Page", layout="wide")
    
    # Handle authentication
    if not st.user.is_logged_in:
        st.title("Nansen.ai API Dashboard")
        st.write("Please log in to access the dashboards.")
        if st.button("Log in"):
            st.login()
        st.stop()

    st.sidebar.success("Check out our dashboards above!")

    # User is logged in - show logout button and user info
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("Nansen.ai Sample Project")
    with col2:
        if st.button("Log out"):
            st.logout()
    
    st.write(f"Hello, {st.user.name}!")

    st.header("What are Smart Money Buying?")

    # Initialize session
    if 'chains' not in st.session_state:
        st.session_state.chains = ['all']
    if 'excl_labels' not in st.session_state:
        st.session_state.excl_labels = []
    if 'min_mc' not in st.session_state:
        st.session_state.min_mc = 1_000_000
    if 'max_mc' not in st.session_state:
        st.session_state.max_mc = 10_000_000_000
    if 'starred_wallets' not in st.session_state:
        starred_wallets = st_javascript("JSON.parse(localStorage.getItem('starred_wallets') || '[]');")
        if not isinstance(starred_wallets, list):
            st.info("Loading starred wallets...")
            st.stop()
        st.session_state.starred_wallets = starred_wallets

    with st.form(key='input_form'):
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            all_chains = ["all", "ethereum", "solana", "base", 
                "arbitrum", "avalanche", "berachain", 
                "blast", "bnb", "goat", 
                "hyperevm", "iotaevm", "linea", 
                "mantle", "optimism", "polygon",
                "ronin", "sei", "scroll", 
                "sonic", "unichain", "zksync"]
            selected_chains = st.multiselect(
                "Select Chains",
                options=all_chains,
                default=st.session_state.chains,
                key="chains"
            )
            smart_money_labels = [
                "Fund", "Smart Trader", "30D Smart Trader",
                "90D Smart Trader", "180D Smart Trader"
            ]
            exclude_smart_money_labels = st.multiselect(
                "Exclude Smart Money Labels",
                options=smart_money_labels,
                default=st.session_state.excl_labels,
                key="excl_labels"
            )
        with c2:
            min_market_cap = st.number_input(
                "Min Token Market Cap (USD)",
                min_value=0, step=100_000, format="%d",
                value=st.session_state.min_mc,
                key="min_mc"
            )
            st.markdown("<br>", unsafe_allow_html=True)
            submit = st.form_submit_button("🔄 Update Dashboard")
        with c3:
            max_market_cap = st.number_input(
                "Max Token Market Cap (USD)",
                min_value=min_market_cap, step=100_000, format="%d",
                value=st.session_state.max_mc,
                key="max_mc"
            )

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Top 3 Tokens by DEX Trading Value (24h)")
        render_dex_trades_podium(st.session_state.chains, st.session_state.min_mc, st.session_state.max_mc, st.session_state.excl_labels)

    with col4:
        st.subheader("Top 3 Tokens by Netflow (24h)")
        render_netflow_podium(st.session_state.chains, st.session_state.min_mc, st.session_state.max_mc, st.session_state.excl_labels)

    st.divider()
    st.subheader("Token Netflow Distribution (Netflow > $5,000)")
    render_netflow_scatterplot()

    st.divider()
    st.subheader("Starred Wallet Token Purchases on Ethereum")
    render_wallet_token_tracker(st.session_state.starred_wallets)

if __name__ == "__main__":
    main()
