# components/pfl_roi_pnl_scatter.py
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
from nansen_client import NansenClient

@st.cache_data(ttl=300)
def fetch_profiler_address_pnl_summary(_client, address, chain_all, from_iso, to_iso):
    payload = {
        "address": address, 
        "chain": chain_all, 
        "date": {
            "from": from_iso, 
            "to": to_iso
        }
    }

    items = _client.profiler_address_pnl_summary(payload)
    df = pd.DataFrame(items.get("top5_tokens", []))

    return df

def render_roi_pnl_scatter(client: NansenClient, address: str, chain_all: str, from_iso: str, to_iso: str):
    st.subheader("ROI vs PnL by Token")
    st.text("X=ROI%; Y=PnL $; each dot=token; winners sit upper-right.")
    try:
        top5_df = fetch_profiler_address_pnl_summary(client, address, chain_all, from_iso, to_iso)
        if top5_df.empty or not {"realized_roi", "realized_pnl", "token_symbol"}.issubset(top5_df.columns):
            st.info("We are unable to compute profit & loss (PnL) data for this wallet on the currently selected chain(s).")
            return

        df_sc = top5_df.copy()
        df_sc["realized_roi_pct"] = df_sc["realized_roi"] * 100.0

        # De-overlap points with small polar jitter for identical coords
        groups = df_sc.groupby(
            [df_sc["realized_roi_pct"].round(2), df_sc["realized_pnl"].round(0)],
            dropna=False
        )
        jitter = np.zeros((len(df_sc), 2))
        xr = max(df_sc["realized_roi_pct"].max() - df_sc["realized_roi_pct"].min(), 1.0)
        yr = max(df_sc["realized_pnl"].max() - df_sc["realized_pnl"].min(), 1.0)
        r_x, r_y = xr * 0.005, yr * 0.01

        for _, idx in groups.groups.items():
            if len(idx) > 1:
                n = len(idx)
                angles = np.linspace(0, 2*np.pi, n, endpoint=False)
                for j, i in enumerate(idx):
                    jitter[i, 0] = r_x * np.cos(angles[j])
                    jitter[i, 1] = r_y * np.sin(angles[j])

        df_sc["x_jit"] = df_sc["realized_roi_pct"] + jitter[:, 0]
        df_sc["y_jit"] = df_sc["realized_pnl"] + jitter[:, 1]

        fig = px.scatter(
            df_sc, x="x_jit", y="y_jit", text="token_symbol",
            hover_data={"x_jit": False, "y_jit": False, "token_symbol": False},
        )
        fig.update_traces(
            customdata=np.stack([df_sc["token_symbol"], df_sc["realized_roi_pct"], df_sc["realized_pnl"]], axis=-1),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "ROI: %{customdata[1]:.2f}%<br>"
                "PnL: $%{customdata[2]:,.0f}"
                "<extra></extra>"
            ),
            marker=dict(size=14, line=dict(width=1, color="#333"), opacity=0.85),
            textposition="top center",
        )
        fig.add_hline(y=0, line_dash="dash")
        fig.add_vline(x=0, line_dash="dash")
        fig.update_layout(
            xaxis_title="ROI (%)",
            yaxis_title="PnL (USD)",
            margin=dict(t=30, l=10, r=10, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Failed to load ROI vs PNL: {e}")
