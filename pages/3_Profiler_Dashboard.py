#!/usr/bin/env python3

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date, datetime, timedelta, timezone
from nansen_client import NansenClient
from streamlit_javascript import st_javascript
import streamlit.components.v1 as components

# Chart components
from components.pfl_portfolio_value_metrics import render_portfolio_value_metrics
from components.pfl_portfolio_treemap import render_portfolio_treemap
from components.pfl_token_share_stacked import render_token_share_stacked
from components.pfl_volatility_heat_strip import render_volatility_heat_strip
from components.pfl_portfolio_relations_metrics import render_portfolio_relations_metrics
from components.pfl_counterparty_network import render_counterparty_network
from components.pfl_related_wallet_network import render_related_wallet_network
from components.pfl_portfolio_pnl_metrics import render_portfolio_pnl_metrics
from components.pfl_token_pnl_waterfall import render_token_pnl_waterfall
from components.pfl_roi_pnl_scatter import render_roi_pnl_scatter
from components.pfl_transactions_log_hist import render_transactions_log_hist
from components.pfl_portfolio_trends_metrics import render_portfolio_trends_metrics


CHAINS = ["all","ethereum","arbitrum","avalanche","base", "berachain", "blast", "bnb","goat", "hyperevm", "iotaevm", "linea", "mantle", "optimism","polygon","ronin", "sei", "scroll", "sonic", "unichain", "zksync", "solana", "bitcoin", "starknet", "ton", "tron"]
TX_CHAINS = ["ethereum","arbitrum","avalanche","base", "berachain", "blast", "bnb","goat", "hyperevm", "iotaevm", "linea", "mantle", "optimism","polygon","ronin", "sei", "scroll", "sonic", "unichain", "zksync", "solana", "bitcoin", "starknet", "ton", "tron"]

def iso_from_date(d, end_of_day=False):
    if isinstance(d, datetime):
        dt = d
    else:
        dt = datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
    if end_of_day:
        dt = dt.replace(hour=23, minute=59, second=59)
    return dt.isoformat().replace("+00:00", "Z")

def main():
    st.set_page_config(page_title="Profiler Dashboard", layout="wide")

    # Auth 
    if not st.user.is_logged_in:
        st.title("Nansen.ai Profiler API Dashboard")
        st.write("Please log in to access the dashboard.")
        if st.button("Log in"):
            st.login()
        st.stop()

    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("Nansen.ai Profiler API Dashboard")
    with col2:
        if st.button("Log out"):
            st.logout()
    st.write(f"Hello, {st.user.name}!")

    # --------------------------
    # Top-of-page filters
    # --------------------------
    default_wallet = "0xb284f19ffa703daadf6745d3c655f309d17370a5"
    stored_wallet = st_javascript("localStorage.getItem('current_wallet') || ''")
    if not stored_wallet:
        wallet_value = default_wallet
    else:
        wallet_value = stored_wallet
    wallet = st.text_input("Wallet address", value=wallet_value, placeholder="0x...")

    st_javascript(f"localStorage.setItem('current_wallet', '{wallet}');")

    starred_wallets = st_javascript("JSON.parse(localStorage.getItem('starred_wallets') || '[]');")
    if not isinstance(starred_wallets, list):
        st.info("Loading starred wallets...")
        st.stop()
    is_starred = wallet in starred_wallets

    if not is_starred:
        if st.button("Star Wallet"):
            components.html(f"""
                <script>
                const wallet = "{wallet}";
                let wallets = JSON.parse(localStorage.getItem("starred_wallets")) || [];
                wallets.push(wallet);
                localStorage.setItem("starred_wallets", JSON.stringify(wallets));
                alert("Wallet added to your starred list!");
                window.parent.location.reload();
                </script>
            """, height=0)
    else:
        if st.button("Unstar Wallet"):
            components.html(f"""
            <script>
            const wallet = "{wallet}";
            let wallets = JSON.parse(localStorage.getItem("starred_wallets")) || [];
            wallets = wallets.filter(w => w !== wallet);
            localStorage.setItem("starred_wallets", JSON.stringify(wallets));
            alert("Wallet removed from starred list!");
            window.parent.location.reload();
            </script>
            """, height=0)

    colA, colB = st.columns(2)
    with colA:
        chain_all = st.selectbox("Portfolio/PNL Chains", CHAINS, index=0)
    with colB:
        chain_tx = st.selectbox("Transactions/Related Wallets Chain", TX_CHAINS, index=0)

    # Hardcode timeframe to the **last 30 days** (UTC)
    now_date = datetime.now(timezone.utc).date()
    date_from = now_date - timedelta(days=29)
    date_to = now_date
    from_iso = iso_from_date(date_from, end_of_day=False)
    to_iso = iso_from_date(date_to, end_of_day=True)

    # --------------------------
    # Persist "loaded" state to survive reruns from widgets
    # --------------------------
    if "profiler_loaded" not in st.session_state:
        st.session_state.profiler_loaded = False

    load_col, reset_col = st.columns([1, 1])
    with load_col:
        if st.button("Load Profiler"):
            st.session_state.profiler_loaded = True
    with reset_col:
        if st.button("Reset"):
            st.session_state.profiler_loaded = False
            st.rerun()

    if not st.session_state.profiler_loaded:
        st.info("Set filters and click **Load Profiler**.")
        st.stop()

    # From here on, the page remains rendered even if any widget triggers a rerun
    client = NansenClient()

    # ------------- Section 1 -------------
    st.header("Section 1: Identity & Portfolio Snapshot")
    render_portfolio_value_metrics(client, wallet, chain_all, from_iso, to_iso)
    render_portfolio_treemap(client, wallet, chain_all)

    # ------------- Section 2 -------------
    st.header("Section 2: Portfolio Trends & Stability (30 Days)")
    render_portfolio_trends_metrics(client, wallet, chain_all, from_iso, to_iso)

    c1, c2 = st.columns(2)
    with c1:
        render_token_share_stacked(client, wallet, chain_all, from_iso, to_iso)
    with c2:
        render_volatility_heat_strip(client, wallet, chain_all, from_iso, to_iso)

    # ------------- Section 3 -------------
    st.header("Section 3: Interactions & Influence")
    render_portfolio_relations_metrics(client, wallet, chain_all, chain_tx, from_iso, to_iso)
    d1, d2 = st.columns(2)
    with d1:
        render_counterparty_network(client, wallet, chain_all, from_iso, to_iso)
    with d2:
        render_related_wallet_network(client, wallet, chain_tx)

    # ------------- Section 4 -------------
    st.header("Section 4: Tactical Trading Behaviour (30 Days)")
    render_portfolio_pnl_metrics(client, wallet, chain_all, from_iso, to_iso)
    e1, e2 = st.columns(2)
    with e1:
        render_token_pnl_waterfall(client, wallet, chain_all, from_iso, to_iso)
    with e2:
        render_roi_pnl_scatter(client, wallet, chain_all, from_iso, to_iso)

    st.subheader("Trade Sizes (Last 100 transactions)")
    render_transactions_log_hist(client, wallet, chain_tx, from_iso, to_iso)

    st.caption("Data source: Nansen Profiler APIs • All timestamps in UTC")

if __name__ == "__main__":
    main()