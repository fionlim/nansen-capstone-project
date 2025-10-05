#!/usr/bin/env python3

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date, timedelta
from nansen_client import NansenClient

client = NansenClient()

#helper functions

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

# main

def main():
    st.set_page_config(page_title="Profiler Dashboard", layout="wide")
    
    # auth block
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

    # Sidebar
    st.sidebar.header("Portfolio Snapshot Settings")
    address = st.sidebar.text_input("Ethereum Address", "")
    range_option = st.sidebar.selectbox("Range", ["7D", "30D", "90D", "YTD"])
    

    end_date = date.today()
    if range_option == "7D":
        start_date = end_date - timedelta(days=7)
    elif range_option == "30D":
        start_date = end_date - timedelta(days=30)
    elif range_option == "90D":
        start_date = end_date - timedelta(days=90)
    else:
        start_date = date(end_date.year, 1, 1)


    if st.sidebar.button("Fetch Portfolio Snapshot"):
        with st.spinner("Fetching portfolio data..."):
            snapshot, portfolio_value, num_tokens, history = get_portfolio_snapshot(
                address, start_date.isoformat(), end_date.isoformat()
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
                "address": address,
                "chain": "ethereum",
                "date": {"from": f"{start_date}T00:00:00Z", "to": f"{end_date}T23:59:59Z"},
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
            payload_rw = {"address": address, "chain": "ethereum"}
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
                "address": address,
                "chain": "ethereum",
                "date": {"from": f"{start_date}T00:00:00Z", "to": f"{end_date}T23:59:59Z"},
            }
            data_pnl = client.get_pnl_summary(payload_pnl)

            realized_pnl = data_pnl.get("realized_pnl_usd", 0)
            win_rate = data_pnl.get("win_rate", 0)
            roi_percent = data_pnl.get("realized_pnl_percent", 0)

            col1, col2, col3 = st.columns(3)
            col1.metric(f"{range_option} Realized PnL", f"${realized_pnl:,.2f}")
            col2.metric(f"{range_option} Win Rate", f"{win_rate:.1f}%")
            col3.metric(f"{range_option} Avg ROI", f"{roi_percent:.2f}%")

if __name__ == "__main__":
    main()
