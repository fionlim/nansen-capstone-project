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

@st.cache_data(ttl=300)
def fetch_trades(chain, token_address, from_datetime, to_datetime):
    client = NansenClient()

    payload = {
        "chains": [chain],
        "date": {
            "from": from_datetime,
            "to": to_datetime,
        },
        "filters": {"token_address": token_address},
    }

    items = client.tgm_token_screener(payload)
    df = tgm_token_screener_to_dataframe(items)
    
    return df

@st.fragment
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
                to_datetime = now.strftime("%Y-%m-%dT%H:%M:%SZ")
                from_datetime = (now - period_mapping[period]).strftime("%Y-%m-%dT%H:%M:%SZ")

                df = fetch_trades(chain, token_address, from_datetime, to_datetime)

                if not df.empty:
                    token_data = df.iloc[0]  # df should only have one row
                    
                    # Fetch raw data for summary (before formatting)
                    client = NansenClient()
                    payload = {
                        "chains": [chain],
                        "date": {
                            "from": from_datetime,
                            "to": to_datetime,
                        },
                        "filters": {"token_address": token_address},
                    }
                    raw_items = client.tgm_token_screener(payload)
                    
                    # Store summarized data for AI summary - extract raw numeric values
                    if raw_items and len(raw_items) > 0:
                        raw_item = raw_items[0]
                        st.session_state.tgm_token_metrics_summary = {
                            "token_symbol": raw_item.get("token_symbol", "N/A"),
                            "token_age_days": float(raw_item.get("token_age_days", 0)) if raw_item.get("token_age_days") is not None else None,
                            "price_usd": float(raw_item.get("price_usd", 0)) if raw_item.get("price_usd") is not None else None,
                            "price_change": float(raw_item.get("price_change", 0)) if raw_item.get("price_change") is not None else None,
                            "market_cap_usd": float(raw_item.get("market_cap_usd", 0)) if raw_item.get("market_cap_usd") is not None else None,
                            "volume": float(raw_item.get("volume", 0)) if raw_item.get("volume") is not None else None,
                            "liquidity": float(raw_item.get("liquidity", 0)) if raw_item.get("liquidity") is not None else None,
                            "fdv": float(raw_item.get("fdv", 0)) if raw_item.get("fdv") is not None else None,
                            "buy_volume": float(raw_item.get("buy_volume", 0)) if raw_item.get("buy_volume") is not None else None,
                            "sell_volume": float(raw_item.get("sell_volume", 0)) if raw_item.get("sell_volume") is not None else None,
                            "netflow": float(raw_item.get("netflow", 0)) if raw_item.get("netflow") is not None else None,
                            "fdv_mc_ratio": float(raw_item.get("fdv_mc_ratio", 0)) if raw_item.get("fdv_mc_ratio") is not None else None,
                            "inflow_fdv_ratio": float(raw_item.get("inflow_fdv_ratio", 0)) if raw_item.get("inflow_fdv_ratio") is not None else None,
                            "outflow_fdv_ratio": float(raw_item.get("outflow_fdv_ratio", 0)) if raw_item.get("outflow_fdv_ratio") is not None else None,
                        }

                    # Show token symbol and age
                    col_info1, col_info2 = st.columns(2)

                    with col_info1:
                        st.metric("Token Symbol", token_data.get("token_symbol", "N/A"))
                    with col_info2:
                        st.metric(
                            "Token Age", token_data.get("token_age_days", "N/A")
                        )

                    # Row 1: Price and MC
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric(
                            label="Price",
                            value=token_data.get("price_usd", "N/A"),
                            delta=token_data.get("price_change", "N/A"),
                        )
                    with col2:
                        st.metric(
                            label="Market Cap",
                            value=token_data.get("market_cap_usd", "N/A"),
                        )

                    # Row 2: Volume, Liq and FDV
                    col3, col4, col5 = st.columns(3)
                    with col3:
                        st.metric(
                            label="Volume",
                            value=token_data.get("volume", "N/A"),
                        )
                    with col4:
                        st.metric(
                            label="Liquidity",
                            value=token_data.get("liquidity", "N/A"),
                        )
                    with col5:
                        st.metric(
                            label="FDV",
                            value=token_data.get("fdv", "N/A"),
                        )

                    # Row 3: Buy Volume, Netflow, Sell volume
                    col6, col7, col8 = st.columns(3)
                    with col6:
                        st.metric(
                            label="Buy Volume",
                            value=token_data.get("buy_volume", "N/A"),
                        )
                    with col7:
                        st.metric(
                            label="Netflow",
                            value=token_data.get("netflow", "N/A"),
                        )
                    with col8:
                        st.metric(
                            label="Sell Volume",
                            value=token_data.get("sell_volume", "N/A"),
                        )

                    # Row 4: FDV/MC Ratio and Flow Ratios
                    col9, col10, col11 = st.columns(3)
                    with col9:
                        st.metric(
                            label="FDV/MC Ratio",
                            value=token_data.get("fdv_mc_ratio", "N/A"),
                        )
                    with col10:
                        st.metric(
                            label="Inflow FDV Ratio",
                            value=token_data.get("inflow_fdv_ratio", "N/A"),
                        )
                    with col11:
                        st.metric(
                            label="Outflow FDV Ratio",
                            value=token_data.get("outflow_fdv_ratio", "N/A"),
                        )

                else:
                    st.warning("No token metrics found for the specified token address and period.")

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
