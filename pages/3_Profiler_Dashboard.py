#!/usr/bin/env python3

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date, datetime, timedelta, timezone
from nansen_client import NansenClient

# Chart components
from components.pfl_portfolio_treemap import render_portfolio_treemap
from components.pfl_token_share_stacked import render_token_share_stacked
from components.pfl_volatility_heat_strip import render_volatility_heat_strip
from components.pfl_counterparty_network import render_counterparty_network
from components.pfl_related_wallet_network import render_related_wallet_network
from components.pfl_token_pnl_waterfall import render_token_pnl_waterfall
from components.pfl_roi_pnl_scatter import render_roi_pnl_scatter
from components.pfl_transactions_log_hist import render_transactions_log_hist


# ----- start of nat's helper functions -----

def get_portfolio_snapshot(address: str, start_date: str, end_date: str):
    """Fetch portfolio balance history and latest snapshot for a wallet."""
    payload = {
        "address": address,
        "chain": "ethereum",
        "date": {"from": f"{start_date}T00:00:00Z", "to": f"{end_date}T23:59:59Z"},
        "pagination": {"page": 1, "per_page": 1000},
    }

    data = client.get_portfolio_history(payload)
    if not data:
        return None, None, None, None

    history = pd.DataFrame(data)
    history["block_timestamp"] = pd.to_datetime(history["block_timestamp"])

    # latest snapshot per token
    snapshot = history.sort_values("block_timestamp").groupby("token_symbol").last()
    portfolio_value = snapshot["value_usd"].sum()
    num_tokens = len(snapshot)

    return snapshot, portfolio_value, num_tokens, history


def plot_token_allocation(snapshot):
    """Pie chart of token allocation (>10% labeled)."""
    total = snapshot["value_usd"].sum()
    shares = snapshot["value_usd"] / total * 100
    labels = [tok if pct > 10 else "" for tok, pct in zip(snapshot.index, shares)]

    fig, ax = plt.subplots()
    ax.pie(snapshot["value_usd"], labels=labels, autopct=lambda p: f"{p:.1f}%" if p > 10 else "")
    ax.set_title("Token Allocation Snapshot")
    return fig


def plot_portfolio_trend(history, range_option):
    """Line chart of portfolio value over time."""
    portfolio_trend = history.groupby("block_timestamp")["value_usd"].sum().reset_index()
    start_val = portfolio_trend.iloc[0]["value_usd"]
    end_val = portfolio_trend.iloc[-1]["value_usd"]
    growth_pct = (end_val - start_val) / start_val * 100 if start_val > 0 else 0

    fig, ax = plt.subplots()
    ax.plot(portfolio_trend["block_timestamp"], portfolio_trend["value_usd"])
    ax.set_title(f"Portfolio Value Trend ({range_option}) — Growth: {growth_pct:.2f}%")
    ax.set_xlabel("Date")
    ax.set_ylabel("USD Value")
    plt.xticks(rotation=45, ha="right")
    return fig


    
    # auth block

# ----- end of nat's helper functions -----


# ----- start of celine's block -----

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
    wallet = st.text_input("Wallet address", value=default_wallet, placeholder="0x...")

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
    render_portfolio_treemap(client, wallet, chain_all)

    # ------------- Section 2 -------------
    st.header("Section 2: Portfolio Trends & Stability (30 Days)")
    c1, c2 = st.columns(2)
    with c1:
        render_token_share_stacked(client, wallet, chain_all, from_iso, to_iso)
    with c2:
        render_volatility_heat_strip(client, wallet, chain_all, from_iso, to_iso)

    # ------------- Section 3 -------------
    st.header("Section 3: Interactions & Influence")
    d1, d2 = st.columns(2)
    with d1:
        render_counterparty_network(client, wallet, chain_all, from_iso, to_iso)
    with d2:
        render_related_wallet_network(client, wallet, chain_tx)

    # ------------- Section 4 -------------
    st.header("Section 4: Tactical Trading Behaviour (30 Days)")
    e1, e2 = st.columns(2)
    with e1:
        render_token_pnl_waterfall(client, wallet, chain_all, from_iso, to_iso)
    with e2:
        render_roi_pnl_scatter(client, wallet, chain_all, from_iso, to_iso)

    st.subheader("Trade Sizes (Last 100 transactions)")
    render_transactions_log_hist(client, wallet, chain_tx, from_iso, to_iso)

    st.caption("Data source: Nansen Profiler APIs • All timestamps in UTC")

    # ----- end of celine's block -----


    # ----- start of nat's block -----

    # range_option = st.sidebar.selectbox("Range", ["7D", "30D", "90D", "YTD"])
    # end_date = date.today()
    # if range_option == "7D":
    #     start_date = end_date - timedelta(days=7)
    # elif range_option == "30D":
    #     start_date = end_date - timedelta(days=30)
    # elif range_option == "90D":
    #     start_date = end_date - timedelta(days=90)
    # else:
    #     start_date = date(end_date.year, 1, 1)


    if st.sidebar.button("Fetch Portfolio Snapshot"):
        with st.spinner("Fetching portfolio data..."):
            snapshot, portfolio_value, num_tokens, _ = get_portfolio_snapshot(
                wallet, from_iso, to_iso
            )

            if snapshot is None:
                st.warning("No portfolio data found.")
                st.stop()

            # ---- Portfolio summary
            st.subheader("Portfolio Snapshot")
            col1, col2 = st.columns(2)
            col1.metric("Portfolio Value", f"${portfolio_value:,.2f}")
            col2.metric("Number of Tokens Held", num_tokens)

            st.pyplot(plot_token_allocation(snapshot))
            #st.pyplot(plot_portfolio_trend(history, range_option))

            # ---- Counterparties
            st.subheader("Counterparties")
            payload_cp = {
                "address": wallet,
                "chain": "ethereum",
                "date": {"from": f"{from_iso}", "to": f"{to_iso}"},
                "group_by": "wallet",
                "pagination": {"page": 1, "per_page": 50},
            }
            data_cp = client.get_counterparties(payload_cp)
            df_cp = pd.DataFrame(data_cp)
            if not df_cp.empty:
                st.table(
                    df_cp.sort_values("total_volume_usd", ascending=False).head(5)[
                        ["counterparty_address", "total_volume_usd"]
                    ]
                )
            else:
                st.info("No counterparty data found.")

            # ---- Related Wallets
            st.subheader("Related Wallets")
            payload_rw = {"address": wallet, "chain": "ethereum"}
            data_rw = client.get_related_wallets(payload_rw)
            df_rw = pd.DataFrame(data_rw)
            if not df_rw.empty:
                st.table(
                    df_rw.groupby("address")
                    .size()
                    .sort_values(ascending=False)
                    .head(5)
                    .reset_index(name="interaction_count")
                )
            else:
                st.info("No related wallets found.")

            # ---- Trading Behaviour
            st.subheader("Trading Behaviour (PnL Summary)")
            payload_pnl = {
                "address": wallet,
                "chain": "ethereum",
                "date": {"from": f"{from_iso}", "to": f"{to_iso}"},
            }
            data_pnl = client.get_pnl_summary(payload_pnl)

            realized_pnl = data_pnl.get("realized_pnl_usd", 0)
            win_rate = data_pnl.get("win_rate", 0)
            roi_percent = data_pnl.get("realized_pnl_percent", 0)

            col1, col2, col3 = st.columns(3)
            col1.metric(f"Realized PnL", f"${realized_pnl:,.2f}")
            col2.metric(f"Win Rate", f"{win_rate:.1f}%")
            col3.metric(f"Avg ROI", f"{roi_percent:.2f}%")

    # ----- end of nat's block -----

if __name__ == "__main__":
    main()