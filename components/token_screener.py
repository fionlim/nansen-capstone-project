from typing import Dict, List
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

from nansen_client import NansenClient
from dataframes import screener_to_dataframe, flow_to_dataframe


def _corr_table(df: pd.DataFrame):
    corr_df = df[["priceUsd", "liquidity", "volume", "netflow", "buyVolume", "sellVolume"]].copy()
    corr = corr_df.corr(numeric_only=True)
    st.dataframe(corr, use_container_width=True)


def _candles_chart(df_c: pd.DataFrame, title: str = "Token Candles"):
    if df_c.empty or not set(["time", "open", "high", "low", "close"]).issubset(df_c.columns):
        st.info("No candle data available for this token/timeframe.")
        return
    fig = go.Figure(data=[go.Candlestick(
        x=df_c["time"], open=df_c["open"], high=df_c["high"], low=df_c["low"], close=df_c["close"]
    )])
    fig.update_layout(title=title, xaxis_title="Time", yaxis_title="Price (USD)", height=450)
    st.plotly_chart(fig, use_container_width=True)


def render_token_screener(parameters: Dict, pagination: Dict):
    client = NansenClient()

    st.subheader("Token Screener: Smart Money Across Chains")

    payload = {"parameters": parameters, "pagination": pagination}
    try:
        df_s = None
        run_context = st.session_state.get("screener_df")
        # Fetch new data if parameters changed via user action outside rerun
        if st.session_state.get("_trigger_run_screener"):
            st.session_state.pop("_trigger_run_screener", None)
            screen_items = client.token_screener(payload)
            df_s = screener_to_dataframe(screen_items)
            st.session_state["screener_df"] = df_s
        elif run_context is not None:
            df_s = run_context
        else:
            # First-time render: fetch and store
            screen_items = client.token_screener(payload)
            df_s = screener_to_dataframe(screen_items)
            st.session_state["screener_df"] = df_s
        if df_s is None or df_s.empty:
            st.warning("No screener data available.")
            return

        st.markdown("**Significant Smart Money activity (by volume/netflow)**")
        sig = df_s.sort_values(["volume", "netflow"], ascending=[False, False]).head(30)
        st.dataframe(
            sig[["tokenSymbol", "chain", "tokenAddressHex", "volume", "netflow", "buyVolume", "sellVolume"]]
            .rename(columns={
                "tokenSymbol": "Token",
                "tokenAddressHex": "Address",
                "volume": "Volume (USD)",
                "netflow": "Netflow (USD)",
                "buyVolume": "Buy Vol (USD)",
                "sellVolume": "Sell Vol (USD)"
            }),
            use_container_width=True
        )
        vol_series = sig.set_index("tokenSymbol")["volume"]
        vol_series = vol_series.replace([np.inf, -np.inf], np.nan).dropna()
        if vol_series.empty:
            st.info("No finite volume values to chart.")
        else:
            st.bar_chart(vol_series)

        # Selection for price history / candlestick
        # st.markdown("### Price History")
        # col1, col2, col3 = st.columns([2, 2, 1])
        # with col1:
        #     symbols = sig["tokenSymbol"].dropna().unique().tolist()
        #     selected_symbol = st.selectbox("Select token", options=symbols)
        # with col2:
        #     filtered = sig[sig["tokenSymbol"] == selected_symbol]
        #     if filtered.empty:
        #         st.warning("Selected token not in current results.")
        #         return
        #     selected_row = filtered.iloc[0]
        #     selected_address = selected_row["tokenAddressHex"]
        #     selected_chain = selected_row["chain"]
        #     timeframe = st.selectbox("Timeframe", options=["1d", "7d", "30d"], index=0)
        # with col3:
        #     run_candles = st.button("Load Chart")

        # if run_candles:
        #     # Use Token God Mode flows for price history
        #     # Build date range from timeframe selection (approximate: last N days)
        #     try:
        #         import datetime as _dt
        #         days = 1 if timeframe == "1d" else 7 if timeframe == "7d" else 30
        #         date_to = _dt.date.today()
        #         date_from = date_to - _dt.timedelta(days=days)
        #         flows_payload = {
        #             "parameters": {
        #                 "chain": selected_chain,
        #                 "tokenAddress": selected_address,
        #                 "date": {"from": str(date_from), "to": str(date_to)},
        #                 "label": "smart_money"
        #             },
        #             "pagination": {"page": 1, "recordsPerPage": 500}
        #         }
        #         flows = client.token_flows(flows_payload)
        #         df_f = pd.DataFrame(flows)
        #         if not df_f.empty and "blockDate" in df_f.columns and "priceUsd" in df_f.columns:
        #             df_f = df_f.rename(columns={"blockDate": "time"})
        #             df_f["time"] = pd.to_datetime(df_f["time"], errors="coerce")
        #             # Render price line chart; if candles desired, we would need OHLC data
        #             st.line_chart(df_f.set_index("time")["priceUsd"], height=300)
        #         else:
        #             st.info("No price history available from flows for this selection.")
        #     except Exception as e:
        #         st.error(f"Failed to load price history: {e}")

        st.markdown("**Market metrics vs Smart Money movements**")
        _corr_table(df_s)
        st.caption("Correlation between price/liquidity/volume and SM netflow/buys/sells")

        st.markdown("**Strong fundamentals (holder/trading proxies)**")
        fundamentals = df_s.copy()
        if "fdvMcRatio" in fundamentals.columns:
            fundamentals = fundamentals.sort_values(["fdvMcRatio", "volume"], ascending=[True, False]).head(30)
        else:
            fundamentals = fundamentals.sort_values(["volume"], ascending=[False]).head(30)
        st.dataframe(
            fundamentals[[
                "tokenSymbol", "chain", "marketCap", "fdv", "fdvMcRatio", "volume", "buyVolume", "sellVolume"
            ]].rename(columns={
                "tokenSymbol": "Token",
                "marketCap": "Market Cap (USD)",
                "fdv": "FDV (USD)",
                "fdvMcRatio": "FDV/MC",
                "volume": "Volume (USD)",
                "buyVolume": "Buy Vol (USD)",
                "sellVolume": "Sell Vol (USD)"
            }),
            use_container_width=True
        )

        st.markdown("**Emerging tokens with fresh inflows**")
        emerging = df_s.copy()
        if "tokenAgeDaysNum" in emerging.columns:
            emerging = emerging[emerging["tokenAgeDaysNum"].fillna(1e9) <= 30]
        emerging = emerging.sort_values(["netflow", "volume"], ascending=[False, False]).head(30)
        st.dataframe(
            emerging[[
                "tokenSymbol", "chain", "tokenAddressHex", "tokenAgeDays", "netflow", "volume", "liquidity", "priceUsd"
            ]].rename(columns={
                "tokenSymbol": "Token",
                "tokenAddressHex": "Address",
                "tokenAgeDays": "Age (days)",
                "netflow": "Netflow (USD)",
                "volume": "Volume (USD)",
                "liquidity": "Liquidity (USD)",
                "priceUsd": "Price (USD)"
            }),
            use_container_width=True
        )
    except Exception as e:
        st.error(f"Unexpected error: {e}")


def render_flow_intelligence(chain: str, token_address: str, timeframe: str, pagination: Dict):
    client = NansenClient()

    st.subheader("Flow Intelligence")
    payload = {
        "parameters": {"chain": chain, "tokenAddress": token_address, "timeframe": timeframe},
        "pagination": pagination,
    }
    try:
        flow_items = client.flow_intelligence(payload)
        df_flow = flow_to_dataframe(flow_items)
        if df_flow.empty:
            st.warning("No flow intelligence data returned for the selected inputs.")
        else:
            st.dataframe(df_flow, use_container_width=True)
    except Exception as e:
        st.error(f"Unexpected error: {e}")
