import copy
from datetime import datetime, timedelta, timezone
from nansen_client import NansenClient
from dataframes import tgm_dex_trades_to_dataframe
import streamlit as st
import plotly.graph_objects as go


def render_gauge_charts(token_address: str, chain: str, period: str):
    """
    1st gauge: % of transactions by smart money
    2nd gauge: % of unique addresses out of the smart money transactions
    """
    if not token_address or not chain or not period:
        total_trades = 0
        smart_trades = 0
        unique_smart_addresses = 0
        gauge_1_value = 0
        gauge_2_value = 0

    else:
        period_mapping = {
            "1h": timedelta(hours=1),
            "24h": timedelta(hours=24),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30),
        }

        if period not in period_mapping:
            valid_periods = ", ".join(period_mapping.keys())
            raise ValueError(f"Invalid period: {period}. Must be one of: {valid_periods}")

        # Calculate date range based on period
        now = datetime.now(timezone.utc)
        to_datetime = now.isoformat()
        from_datetime = (now - period_mapping[period]).isoformat()

        # Data Fetching
        client = NansenClient()

        payload = {
            "chain": chain,
            "token_address": token_address,
            "date": {"from": from_datetime, "to": to_datetime},
            "pagination": {"page": 1, "per_page": 1000},  # max for tgm/dex-trades endpoint
            "order_by": [{"field": "block_timestamp", "direction": "ASC"}],
        }

        # set only_smart_money flag to True for 2nd payload
        new_payload = copy.deepcopy(payload)
        new_payload["only_smart_money"] = True
        
        # Fetch data from Nansen API
        all_dex_trades = client.tgm_dex_trades(payload, fetch_all=True)
        smart_money_trades = client.tgm_dex_trades(new_payload, fetch_all=True)

        # Convert results to dataframes in dataframes.py
        df_all = tgm_dex_trades_to_dataframe(all_dex_trades)
        df_smart = tgm_dex_trades_to_dataframe(smart_money_trades)

        # Calculate gauge metrics
        total_trades = len(df_all)
        smart_trades = len(df_smart)
        unique_smart_addresses = df_smart["trader_address"].nunique()

        # 1st gauge: % of transactions by smart money
        gauge_1_value = (smart_trades / total_trades * 100) if total_trades > 0 else 0

        # 2nd gauge: % of unique addresses out of smart money transactions
        gauge_2_value = (
            (unique_smart_addresses / smart_trades * 100) if smart_trades > 0 else 0
        )

    # helper function to determine gauge bar color based on value
    def get_bar_color(val):
        if val < 25:
            return "#dc2626"  # red
        elif val < 50:
            return "#f59e0b"  # orange
        elif val < 75:
            return "#eab308"  # yellow
        else:
            return "#10b981"  # green

    # First speedometer: Smart Money Transaction Percentage
    st.subheader("% of Smart Money Transactions")
    fig1 = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=gauge_1_value,
            number={"suffix": "%", "font": {"size": 18}, "valueformat": ".2f"},
            gauge={
                "axis": {"visible": False, "range": [0, 100]},
                "bar": {"color": get_bar_color(gauge_1_value)}
            },
        )
    )
    fig1.update_layout(height=250, margin=dict(l=10, r=10, t=30, b=20))
    st.plotly_chart(fig1, use_container_width=True,key="gauge1")
    st.caption(
        f"📊 {smart_trades:,} of {total_trades:,} dex trades done in the last ({period}) were done by smart money"
    )

    # Second speedometer: Unique Address Concentration
    st.subheader("% of Unique Smart Money Wallets")
    fig2 = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=gauge_2_value,
            number={"suffix": "%", "font": {"size": 18}, "valueformat": ".2f"},
            gauge={
                "axis": {"visible": False, "range": [0, 100]},
                "bar": {"color": get_bar_color(gauge_2_value)}
            },
        )
    )
    fig2.update_layout(height=250, margin=dict(l=10, r=10, t=30, b=20))
    st.plotly_chart(fig2, use_container_width=True,key="gauge2")
    st.caption(
        f"🏛️ {unique_smart_addresses:,} unique addresses in {smart_trades:,} smart money dex trades"
    )

    return {
        "smart_money_percentage": round(gauge_1_value, 2),
        "total_transactions": total_trades,
        "smart_money_transactions": smart_trades,
        "unique_smart_addresses": unique_smart_addresses,
        "period": period,
        "token_address": token_address,
        "chain": chain,
    }