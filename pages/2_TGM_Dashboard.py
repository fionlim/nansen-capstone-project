import streamlit as st

from components.tgm_holders_horizontal_bar_chart import render_holder_flows_horizontal_bar_chart
from components.tgm_holders_donut_chart import render_holders_donut_chart
from components.tgm_pnl_leaderboard_bubble_chart import render_pnl_leaderboard_bubble_chart
from components.tgm_dextrades_combo_chart import render_dex_trades_hourly
from components.tgm_token_metrics import render_token_metrics
from components.sm_gauge import render_gauge_charts
from components.llamaswap_iframe import render_llamaswap_iframe
from components.tgm_dashboard_summary import render_dashboard_summary

st.set_page_config(page_title="TGM Dashboard", layout="wide")
st.title("Token Dashboard")

# Handle authentication
if not st.user.is_logged_in:
    st.title("Nansen.ai API Dashboard")
    st.write("Please log in to access the dashboard.")
    if st.button("Log in"):
        st.login()
    st.stop()

# --- Handle URL Query Parameters ---
query_params = st.query_params
url_token = query_params.get("token", "")
url_chain = query_params.get("chain", "")

# Initialize session
if 'token' not in st.session_state:
    st.session_state.token = ''
if 'chain' not in st.session_state:
    st.session_state.chain = 'ethereum'
if 'period' not in st.session_state:
    st.session_state.period = '24h'
if 'aggregate_by_entity' not in st.session_state:
    st.session_state.aggregate_by_entity = False

# --- Priority: URL params > Landing Page > Empty ---
# Set from URL query parameters if present
if url_token:
    if url_chain:
        # Validate chain is in available chains
        available_chains = ["ethereum", "solana", "arbitrum", "optimism", "base", "bnb", "polygon"]
        if url_chain.lower() in available_chains:
            st.session_state.chain = url_chain.lower()
        else:
            st.warning(f"Invalid chain '{url_chain}'. Using default: ethereum")
    # Only lowercase token if chain is not solana
    token_normalized = url_token.strip()
    if st.session_state.chain != "solana":
        token_normalized = token_normalized.lower()
    st.session_state.token = token_normalized
    st.info(f"📎 Loaded from URL: Token {st.session_state.token[:10]}... on {st.session_state.chain}")
elif st.session_state.get("selected_token", ""):
    # Fallback to landing page prefilled token
    prefilled_token = st.session_state.get("selected_token", "")
    # Only lowercase token if chain is not solana
    token_normalized = prefilled_token.strip()
    if st.session_state.chain != "solana":
        token_normalized = token_normalized.lower()
    st.session_state.token = token_normalized
    st.info(f"Auto-loaded token: {prefilled_token}")

# --- Inputs ---
with st.form(key='input_form'):
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    with c1:
        # Use session state token as default value (from URL or landing page)
        token = st.text_input(
            "Token address", 
            value=st.session_state.get("token", ""),
            placeholder="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
        )
        if not token:
            st.info("👆 Enter a token address above to see detailed metrics")
    with c2:
        available_chains = ["ethereum", "solana", "arbitrum", "optimism", "base", "bnb", "polygon"]
        chain = st.selectbox("Chain", available_chains, key="chain")
        # Only lowercase token if chain is not solana
        token_normalized = token.strip()
        if chain != "solana":
            token_normalized = token_normalized.lower()
        st.session_state.token = token_normalized
    with c3:
        period = st.selectbox("Period", ["1h", "24h", "7d", "30d"], key="period")
    with c4:
        st.markdown("<br>", unsafe_allow_html=True)
        submit = st.form_submit_button("🔄 Update Dashboard", width='stretch')

# Placeholder for summary at the top (filled after all components run)
summary_placeholder = st.empty()
with summary_placeholder.container():
    with st.expander("**AI Summary**", expanded=False):
        st.text("Preparing summary…")

# --- Top layout: Smart Money Gauges on left, Token metrics on right ---

left_col, right_col = st.columns(2, gap="large")
with left_col:
    render_gauge_charts(st.session_state.token, st.session_state.chain, st.session_state.period)

with right_col:
    render_token_metrics(st.session_state.token, st.session_state.chain, st.session_state.period)

# --- Bottom layout: Holder Distributions ---

st.subheader('Holder Distribution & Flows')
col1, col2 = st.columns([1, 4])
with col1:
    aggregate_by_entity = st.selectbox('Aggregate by Entity', [False, True], key='aggregate_by_entity')
render_holders_donut_chart(st.session_state.chain, st.session_state.token, st.session_state.aggregate_by_entity)
render_holder_flows_horizontal_bar_chart(st.session_state.chain, st.session_state.token, st.session_state.aggregate_by_entity)

st.subheader('Holder PnL Bubble Chart', help = "PnL for past one week with following conditions: holding amount ≥ 1000 and realised PnL ≥ 1000")
render_pnl_leaderboard_bubble_chart(st.session_state.chain, st.session_state.token)

st.subheader(body = 'DEX Trades Hourly Overview', help="Shows both buy and sell trades by Smart Money labelled wallets only.")
render_dex_trades_hourly(st.session_state.chain, st.session_state.token)

# --- Bottom layout: LlamaSwap Widget ---
st.subheader('Swap via LlamaSwap')
render_llamaswap_iframe(st.session_state.chain, st.session_state.token)

# Update summary in the placeholder after all components have stored their data
with summary_placeholder.container():
    with st.expander("**AI Summary**", expanded=False):
        render_dashboard_summary()