# components/pfl_token_share_stacked.py
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
from nansen_client import NansenClient

def render_token_share_stacked(client: NansenClient, address: str, chain_all: str, from_iso: str, to_iso: str, hide_spam: bool = True):
    st.subheader("Token Mix Over Time")
    st.text("100% stacked area (holdings > $10 only to remove dust); band thickness = daily portfolio share.")

    try:
        payload = {
            "address": address,
            "chain": chain_all,
            "filters": {"hide_spam_tokens": hide_spam, "value_usd": {"min": 10}},
            "date": {"from": from_iso, "to": to_iso},
        }
        rows = client.profiler_address_historical_balances_all(payload)
        df = pd.DataFrame(rows)

        if df.empty:
            st.info("No historical balances found for the selected date range.")
            return

        df["block_timestamp"] = pd.to_datetime(df["block_timestamp"], errors="coerce").dt.floor("D")
        g = (df.groupby(["block_timestamp", "token_symbol"], as_index=False)["value_usd"]
                .sum().rename(columns={"value_usd": "value_usd_token"}))
        g["value_usd_token"] = pd.to_numeric(g["value_usd_token"], errors="coerce").fillna(0.0)

        totals = g.groupby("block_timestamp", as_index=False)["value_usd_token"].sum() \
                  .rename(columns={"value_usd_token": "total_usd"})
        g = g.merge(totals, on="block_timestamp", how="left")
        g["pct_share"] = np.where(g["total_usd"] > 0, 100 * g["value_usd_token"] / g["total_usd"], 0.0)

        fig = px.area(
            g.sort_values("block_timestamp"),
            x="block_timestamp",
            y="pct_share",
            color="token_symbol",
            labels={"pct_share": "Portfolio %"},
        )
        fig.for_each_trace(lambda t: t.update(stackgroup="one"))
        fig.update_traces(
            hovertemplate="<b>%{fullData.name}</b> · %{y:.2f}%<extra></extra>",
            line=dict(width=0.7)
        )
        fig.update_layout(
            hovermode="x unified",
            xaxis_title="Date",
            yaxis_title="Percentage of Portfolio",
            legend_title_text="Token",
            margin=dict(t=30, l=10, r=10, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Failed to load Token Share Over Time: {e}")
