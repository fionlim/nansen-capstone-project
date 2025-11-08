import streamlit as st
from datetime import datetime, timedelta, timezone
from nansen_client import NansenClient
from streamlit_javascript import st_javascript
import time
import streamlit.components.v1 as components

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

st.set_page_config(page_title="Profiler Dashboard", layout="wide")
st.title("Nansen.ai Profiler API Dashboard")

# Handle authentication
if not st.user.is_logged_in:
    st.title("Nansen.ai Profiler API Dashboard")
    st.write("Please log in to access the dashboard.")
    if st.button("Log in"):
        st.login()
    st.stop()

# Initialize session
if 'wallet' not in st.session_state:
    st.session_state.wallet = '0xb284f19ffa703daadf6745d3c655f309d17370a5'
if 'label' not in st.session_state:
    st.session_state.label = ''
if 'port_pnl_chains' not in st.session_state:
    st.session_state.port_pnl_chains = 'all'
if 'tx_related_chains' not in st.session_state:
    st.session_state.tx_related_chains = 'ethereum'
if 'starred_wallets' not in st.session_state:
    st.session_state.starred_wallets = []
if 'form_submitted' not in st.session_state:
    st.session_state.form_submitted = False

# Load starred wallets from localStorage
starred_wallets = st_javascript("JSON.parse(localStorage.getItem('starred_wallets') || '[]');")

if not isinstance(starred_wallets, list):
    st.info("Loading starred wallets...")
    st.stop()

st.session_state.starred_wallets = starred_wallets

# Update is_starred state
st.session_state.is_starred = st.session_state.wallet in st.session_state.starred_wallets

# --- Inputs ---
with st.form(key='input_form'):
    c1, c2, c3, c4 = st.columns([2, 1.5, 1, 1])
    with c1:
        wallet = st.text_input(
            "Wallet address", 
            value=st.session_state.wallet,
            placeholder="0x..."
        )
        if not wallet:
            st.info("👆 Enter a wallet address above to see detailed metrics")
        st.session_state.wallet = wallet.strip()
    with c2:
        label = st.text_input(
            "Wallet label",
            value=st.session_state.get("label", ""),
            placeholder="Optional label"
        )
        st.session_state.label = label.strip()
    with c3:
        st.selectbox("Portfolio/PNL Chains", CHAINS, index=CHAINS.index(st.session_state.port_pnl_chains) if st.session_state.port_pnl_chains in CHAINS else 0, key="port_pnl_chains")
    with c4:
        st.selectbox("TX/Related Chain", TX_CHAINS, index=TX_CHAINS.index(st.session_state.tx_related_chains) if st.session_state.tx_related_chains in TX_CHAINS else 0, key="tx_related_chains")
    

    submitted = st.form_submit_button("🔄 Update Dashboard", use_container_width=True)
    if submitted:
        st.session_state.form_submitted = True

# Star/Unstar button (outside form to avoid form submission)
if st.session_state.wallet:
    star_col, _ = st.columns([1, 5])
    with star_col:
        if st.session_state.is_starred:
            if st.button("⭐ Unstar Wallet"):
                st.session_state.is_starred = False
                components.html(f"""
                <script>
                    const wallet = "{st.session_state.wallet}";
                    let wallets = JSON.parse(localStorage.getItem("starred_wallets")) || [];
                    wallets = wallets.filter(w => w !== wallet);
                    localStorage.setItem("starred_wallets", JSON.stringify(wallets));
                </script>
                """, height=0)
                time.sleep(0.1)
                st.rerun()
        else:
            if st.button("☆ Star Wallet"):
                st.session_state.is_starred = True
                components.html(f"""
                <script>
                    const wallet = "{st.session_state.wallet}";
                    let wallets = JSON.parse(localStorage.getItem("starred_wallets")) || [];
                    wallets.push(wallet);
                    localStorage.setItem("starred_wallets", JSON.stringify(wallets));
                </script>
                """, height=0)
                time.sleep(0.1)
                st.rerun()

# Only render charts if form has been submitted
if not st.session_state.form_submitted:
    st.stop()

# Hardcode timeframe to the **last 30 days** (UTC)
now_date = datetime.now(timezone.utc).date()
date_from = now_date - timedelta(days=29)
date_to = now_date
from_iso = iso_from_date(date_from, end_of_day=False)
to_iso = iso_from_date(date_to, end_of_day=True)

client = NansenClient()

# ------------- Section 1 -------------
st.header("Section 1: Identity & Portfolio Snapshot")
render_portfolio_value_metrics(client, st.session_state.wallet, st.session_state.port_pnl_chains, from_iso, to_iso)
render_portfolio_treemap(client, st.session_state.wallet, st.session_state.port_pnl_chains)

# ------------- Section 2 -------------
st.header("Section 2: Portfolio Trends & Stability (30 Days)")
render_portfolio_trends_metrics(client, st.session_state.wallet, st.session_state.port_pnl_chains, from_iso, to_iso)

c1, c2 = st.columns(2)
with c1:
    render_token_share_stacked(client, st.session_state.wallet, st.session_state.port_pnl_chains, from_iso, to_iso)
with c2:
    render_volatility_heat_strip(client, st.session_state.wallet, st.session_state.port_pnl_chains, from_iso, to_iso)

# ------------- Section 3 -------------
st.header("Section 3: Interactions & Influence")
render_portfolio_relations_metrics(client, st.session_state.wallet, st.session_state.port_pnl_chains, st.session_state.tx_related_chains, from_iso, to_iso)
d1, d2 = st.columns(2)
with d1:
    render_counterparty_network(client, st.session_state.wallet, st.session_state.port_pnl_chains, from_iso, to_iso)
with d2:
    render_related_wallet_network(client, st.session_state.wallet, st.session_state.tx_related_chains)

# ------------- Section 4 -------------
st.header("Section 4: Tactical Trading Behaviour (30 Days)")
render_portfolio_pnl_metrics(client, st.session_state.wallet, st.session_state.port_pnl_chains, from_iso, to_iso)
e1, e2 = st.columns(2)
with e1:
    render_token_pnl_waterfall(client, st.session_state.wallet, st.session_state.port_pnl_chains, from_iso, to_iso)
with e2:
    render_roi_pnl_scatter(client, st.session_state.wallet, st.session_state.port_pnl_chains, from_iso, to_iso)

st.subheader("Trade Sizes (Last 100 transactions)")
render_transactions_log_hist(client, st.session_state.wallet, st.session_state.tx_related_chains, from_iso, to_iso)

st.caption("Data source: Nansen Profiler APIs • All timestamps in UTC")
