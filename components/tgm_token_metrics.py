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
    # Add CSS to make metrics more compact and ensure numbers fit
    st.markdown("""
        <style>
        div[data-testid="stMetricValue"] {
            font-size: 0.9em !important;
            word-break: break-word !important;
            overflow-wrap: break-word !important;
        }
        div[data-testid="stMetricLabel"] {
            font-size: 0.85em !important;
        }
        [data-testid="stMetricContainer"] {
            min-width: 0 !important;
        }
        </style>
    """, unsafe_allow_html=True)
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
