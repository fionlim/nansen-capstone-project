# components/pfl_volatility_heat_strip.py
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from nansen_client import NansenClient

def render_volatility_heat_strip(client: NansenClient, address: str, chain_all: str, from_iso: str, to_iso: str, hide_spam: bool = True):
    st.subheader("Balance Volatility")
    st.text("Heatmap: red = higher 7-day std dev of USD balance; rows=tokens, cols=days.")

    try:
        payload = {
            "address": address,
            "chain": chain_all,
            "filters": {"hide_spam_tokens": hide_spam, "value_usd": {"min": 10}},
            "date": {"from": from_iso, "to": to_iso},
            "pagination": { "page": 1,"per_page": 100 }
        }
        rows = client.profiler_address_historical_balances(payload, fetch_all=True)
        df = pd.DataFrame(rows)
        if df.empty:
            st.info("Insufficient data to compute volatility.")
            return

        df = df.copy()
        df["value_usd"] = pd.to_numeric(df["value_usd"], errors="coerce").fillna(0.0)
        df["block_timestamp"] = pd.to_datetime(df["block_timestamp"], utc=True, errors="coerce")

        top_tokens = (
            df.groupby("token_symbol")["value_usd"]
            .sum().sort_values(ascending=False).head(5).index
        )
        vol_df = df[df["token_symbol"].isin(top_tokens)].copy()
        vol_df["day"] = vol_df["block_timestamp"].dt.floor("D")

        daily = vol_df.groupby(["day", "token_symbol"], as_index=False)["value_usd"].sum()

        start_day = pd.to_datetime(from_iso).floor("D")
        end_day = pd.to_datetime(to_iso).floor("D")
        all_days = pd.date_range(start_day, end_day, freq="D")

        wide = (
            daily.pivot(index="day", columns="token_symbol", values="value_usd")
            .reindex(all_days).astype(float).fillna(0.0)
        )
        wide.index.name = "day"
        wide = wide.loc[:, (wide != 0).any(axis=0)]
        if wide.shape[1] == 0:
            st.info("No non-zero balances for the top tokens in this window.")
            return

        vol_7d = wide.rolling(window=7, min_periods=2).std(ddof=0).fillna(0.0)
        heat = vol_7d.loc[all_days].T

        z = heat.values.astype(float)
        if heat.size == 0 or float(np.nanmax(z)) == 0.0:
            st.info("Rolling volatility is zero across the selected window.")
            return

        row_med = np.nanmedian(z, axis=1)
        row_max = np.nanmax(z, axis=1)
        med_mat = np.tile(row_med[:, None], (1, z.shape[1]))
        max_mat = np.tile(row_max[:, None], (1, z.shape[1]))
        customdata = np.dstack([med_mat, max_mat])

        x_dates = heat.columns.to_pydatetime()
        y_tokens = heat.index.astype(str).tolist()
        zmax = float(np.nanmax(z))

        fig = go.Figure(
            data=go.Heatmap(
                z=z, x=x_dates, y=y_tokens,
                customdata=customdata,
                coloraxis="coloraxis",
                hoverongaps=False,
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "%{x|%a, %b %d, %Y}<br>"
                    "7D rolling σ: <b>%{z:,.2f}</b> USD<br>"
                    "Token median σ: %{customdata[0]:,.2f} USD<br>"
                    "Token max σ: %{customdata[1]:,.2f} USD"
                    "<extra></extra>"
                ),
            )
        )
        fig.update_layout(
            coloraxis=dict(colorscale="RdYlGn_r", cmin=0, cmax=zmax),
            coloraxis_colorbar=dict(title="7D σ (USD)"),
            xaxis_title="Date",
            yaxis_title="Token",
            margin=dict(t=30, l=10, r=10, b=10),
        )
        st.plotly_chart(fig, width='stretch')

    except Exception as e:
        st.error(f"Failed to load Volatility Heat Strip: {e}")
