# components/pfl_token_pnl_waterfall.py
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from nansen_client import NansenClient

@st.cache_data(ttl=300)
def fetch_profiler_address_pnl_summary(_client, address, chain_all, from_iso, to_iso):
    payload = {
        "address": address,
        "chain": chain_all,
        "date": {"from": from_iso, "to": to_iso},
    }
    items = _client.profiler_address_pnl_summary(payload)
    df = pd.DataFrame(items.get("top5_tokens", []))

    return df

def render_token_pnl_waterfall(client: NansenClient, address: str, chain_all: str, from_iso: str, to_iso: str):
    st.subheader("PnL Drivers")
    st.text("Each bar = token’s realized PnL; up=gains, down=losses (last 30 days).")
    try:
        top5_df = fetch_profiler_address_pnl_summary(client, address, chain_all, from_iso, to_iso)
        if top5_df.empty or not {"token_symbol", "realized_pnl"}.issubset(top5_df.columns):
            st.info("We are unable to compute profit & loss (PnL) data for this wallet on the currently selected chain(s).")
            return

        vals = top5_df.sort_values("realized_pnl", ascending=False).copy()
        vals["realized_pnl"] = pd.to_numeric(vals["realized_pnl"], errors="coerce").fillna(0.0)
        if "realized_roi" in vals.columns:
            vals["roi_pct"] = pd.to_numeric(vals["realized_roi"], errors="coerce") * 100.0
        else:
            vals["roi_pct"] = np.nan

        total_pnl = vals["realized_pnl"].sum()
        abs_total = vals["realized_pnl"].abs().sum()

        vals["share_total"] = np.where(total_pnl != 0, vals["realized_pnl"] / total_pnl, 0.0)
        vals["share_abs"]   = np.where(abs_total != 0, vals["realized_pnl"].abs() / abs_total, 0.0)

        customdata = np.stack([
            vals["realized_pnl"].values,
            vals["share_total"].values,
            vals["roi_pct"].values,
            vals["share_abs"].values,
        ], axis=-1)

        fig = go.Figure(go.Waterfall(
            orientation="v",
            measure=["relative"] * len(vals),
            x=vals["token_symbol"],
            y=vals["realized_pnl"],
            customdata=customdata,
            text=vals["realized_pnl"].map(lambda v: f"{v:,.0f}"),
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Realized PnL: $%{customdata[0]:,.0f}<br>"
                "Share of total PnL: %{customdata[1]:.1%}<br>"
                "Share of absolute PnL: %{customdata[3]:.1%}<br>"
                "ROI: %{customdata[2]:.1f}%"
                "<extra></extra>"
            ),
        ))
        fig.update_layout(
            title="Token Contributions to PnL (Last 30 Days)",
            yaxis_title="PnL (USD)",
            margin=dict(t=30, l=10, r=10, b=10),
            hoverlabel=dict(bgcolor="white", font_size=12)
        )
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Failed to load Waterfall: {e}")
