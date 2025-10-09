import streamlit as st
from datetime import datetime, timedelta, timezone
from nansen_client import NansenClient
from dataframes import tgm_token_screener_to_dataframe


def format_delta_color(delta_value):
    if delta_value and delta_value.startswith("+"):
        return "normal"  # Green for positive
    elif delta_value and delta_value.startswith("-"):
        return "inverse"  # Red for negative
    else:
        return "normal"


def render_token_metrics(token_address: str, chain: str, period: str):

    st.subheader("Token Metrics")
    st.markdown("<br>", unsafe_allow_html=True)

    if token_address:
        with st.spinner("Fetching token metrics..."):
            try:
                period_mapping = {
                    "1h": timedelta(hours=1),
                    "24h": timedelta(hours=24),
                    "7d": timedelta(days=7),
                    "30d": timedelta(days=30),
                }

                if period not in period_mapping:
                    raise ValueError(f"Invalid period: {period}. Must be one of: 1h, 24h, 7d, 30d")

                # Calculate date range based on period
                now = datetime.now(timezone.utc)
                to_datetime = now.isoformat()
                from_datetime = (now - period_mapping[period]).isoformat()

                payload = {
                    "chains": [chain],
                    "date": {
                        "from": from_datetime,
                        "to": to_datetime,
                    },
                    "filters": {"token_address": token_address},
                }

                client = NansenClient()
                items = client.tgm_token_screener(payload)
                df = tgm_token_screener_to_dataframe(items)
                if not df.empty:
                    token_data = df.iloc[0]  # df should only have one row

                    # Show token symbol and age
                    col_info1, col_info2 = st.columns(2)
                    with col_info1:
                        st.metric("Token Symbol", token_data.get("token_symbol", "N/A"))
                    with col_info2:
                        st.metric(
                            "Token Age", token_data.get("token_age_days", "N/A")
                        )

                    # Row 1: Market Cap and FDV
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric(
                            label="Market Cap",
                            value=token_data.get("market_cap_usd_formatted", "N/A"),
                        )
                    with col2:
                        st.metric(
                            label="FDV",
                            value=token_data.get("fdv_usd_formatted", "N/A"),
                        )

                    # Row 2: Holders and Transfers
                    col3, col4 = st.columns(2)
                    with col3:
                        st.metric(
                            label="Holders",
                            value=token_data.get("holders_formatted", "N/A"),
                        )
                    with col4:
                        st.metric(
                            label="Transfers (24h)",
                            value=token_data.get("transfers_24h_formatted", "N/A"),
                        )

                    # Row 3: Price and Price Change
                    col5, col6 = st.columns(2)
                    with col5:
                        st.metric(
                            label="Price (USD)",
                            value=token_data.get("price_usd_formatted", "N/A"),
                        )
                    with col6:
                        st.metric(
                            label="Price Change (24h)",
                            value=token_data.get("price_change_24h_formatted", "N/A"),
                            delta=token_data.get("price_change_24h_delta", None),
                            delta_color=format_delta_color(token_data.get("price_change_24h_delta", "")),
                        )

                    # Row 4: Volume and Volume Change
                    col7, col8 = st.columns(2)
                    with col7:
                        st.metric(
                            label="Volume (24h)",
                            value=token_data.get("volume_24h_usd_formatted", "N/A"),
                        )
                    with col8:
                        st.metric(
                            label="Volume Change (24h)",
                            value=token_data.get("volume_change_24h_formatted", "N/A"),
                            delta=token_data.get("volume_change_24h_delta", None),
                            delta_color=format_delta_color(token_data.get("volume_change_24h_delta", "")),
                        )

                    # Row 5: Liquidity and Liquidity Change
                    col9, col10 = st.columns(2)
                    with col9:
                        st.metric(
                            label="Liquidity (USD)",
                            value=token_data.get("liquidity_usd_formatted", "N/A"),
                        )
                    with col10:
                        st.metric(
                            label="Liquidity Change (24h)",
                            value=token_data.get("liquidity_change_24h_formatted", "N/A"),
                            delta=token_data.get("liquidity_change_24h_delta", None),
                            delta_color=format_delta_color(token_data.get("liquidity_change_24h_delta", "")),
                        )
                else:
                    st.warning("No token metrics found for the specified token address and period.")
                with col_info1:
                    st.metric("Token Symbol", token_data.get("token_symbol", "N/A"))
                with col_info2:
                    st.metric(
                        "Token Age", token_data.get("token_age_days", "N/A")
                    )

                # Row 1: Market Cap and FDV
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(
                        label="Market Cap",
                        value=token_data.get("market_cap_usd_formatted", "N/A"),
                    )
                with col2:
                    st.metric(
                        label="FDV",
                        value=token_data.get("fdv_formatted", "N/A"),
                    )

                # Row 2: Volume metrics
                col3, col4 = st.columns(2)
                with col3:
                    st.metric(
                        label="Buy Volume",
                        value=token_data.get("buy_volume_formatted", "N/A"),
                    )
                with col4:
                    st.metric(
                        label="Sell Volume",
                        value=token_data.get("sell_volume_formatted", "N/A"),
                    )

                # Row 3: Price and Total Volume
                col5, col6 = st.columns(2)
                with col5:
                    st.metric(
                        label="Price",
                        value=token_data.get("price_usd_formatted", "N/A"),
                        delta=token_data.get("price_change_formatted", "N/A"),
                    )
                with col6:
                    st.metric(
                        label="Volume",
                        value=token_data.get("volume_formatted", "N/A"),
                    )

                # Row 4: Liquidity and Net Flow
                col7, col8 = st.columns(2)
                with col7:
                    st.metric(
                        label="Liquidity",
                        value=token_data.get("liquidity_formatted", "N/A"),
                    )
                with col8:
                    st.metric(
                        label="Netflow",
                        value=token_data.get("netflow_formatted", "N/A"),
                    )

                # Row 5: FDV/MC Ratio and Flow Ratios
                col9, col10, col11 = st.columns(3)
                with col9:
                    st.metric(
                        label="FDV/MC Ratio",
                        value=token_data.get("fdv_mc_ratio", "N/A"),
                    )
                with col10:
                    st.metric(
                        label="Inflow FDV Ratio",
                        value=token_data.get("inflow_fdv_ratio_formatted", "N/A"),
                    )
                with col11:
                    st.metric(
                        label="Outflow FDV Ratio",
                        value=token_data.get("outflow_fdv_ratio_formatted", "N/A"),
                    )

            except Exception as e:
                st.error(f"Error fetching token metrics: {str(e)}")

                # Show placeholder cards
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(label="Market Cap", value="-", delta=None)
                with col2:
                    st.metric(label="FDV", value="-", delta=None)

                col3, col4 = st.columns(2)
                with col3:
                    st.metric(label="Buy Volume", value="-", delta=None)
                with col4:
                    st.metric(label="Sell Volume", value="-", delta=None)

                col5, col6 = st.columns(2)
                with col5:
                    st.metric(label="Liquidity", value="-", delta=None)
                with col6:
                    st.metric(label="Netflow", value="-", delta=None)

                col7, col8, col9 = st.columns(3)
                with col7:
                    st.metric(label="FDV/MC Ratio", value="-", delta=None)
                with col8:
                    st.metric(label="Inflow FDV Ratio", value="-", delta=None)
                with col9:
                    st.metric(label="Outflow FDV Ratio", value="-", delta=None)

    else:

        # Show placeholder cards when no token is selected
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Market Cap", value="-", delta=None)
        with col2:
            st.metric(label="FDV", value="-", delta=None)

        col3, col4 = st.columns(2)
        with col3:
            st.metric(label="Buy Volume", value="-", delta=None)
        with col4:
            st.metric(label="Sell Volume", value="-", delta=None)

        col5, col6 = st.columns(2)
        with col5:
            st.metric(label="Liquidity", value="-", delta=None)
        with col6:
            st.metric(label="Netflow", value="-", delta=None)

        col7, col8, col9 = st.columns(3)
        with col7:
            st.metric(label="FDV/MC Ratio", value="-", delta=None)
        with col8:
            st.metric(label="Inflow FDV Ratio", value="-", delta=None)
        with col9:
            st.metric(label="Outflow FDV Ratio", value="-", delta=None)
