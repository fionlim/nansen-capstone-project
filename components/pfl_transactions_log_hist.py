# components/pfl_transactions_log_hist.py
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from nansen_client import NansenClient

@st.cache_data(ttl=300)
def fetch_profiler_address_transactions(_client, address, chain_tx, from_iso, to_iso):
    payload = {
        "address": address,
        "chain": chain_tx,
        "date": {"from": from_iso, "to": to_iso},
        "order_by": [{"field": "block_timestamp", "direction": "DESC"}],
        "pagination": {"page": 1, "per_page": 20},
    }

    items = _client.profiler_address_transactions(payload, n=5)
    df = pd.DataFrame(items)

    return df

def render_transactions_log_hist(client: NansenClient, address: str, chain_tx: str, from_iso: str, to_iso: str):
    st.text("Log-scaled USD/transaction with mean & median lines; shows small-vs-whale mix.")

    try:
        df = fetch_profiler_address_transactions(client, address, chain_tx, from_iso, to_iso)
        if df.empty or "volume_usd" not in df.columns:
            st.info("No transactions found to plot.")
            return

        df["volume_usd"] = pd.to_numeric(df["volume_usd"], errors="coerce")
        x = df["volume_usd"].replace(0, np.nan).dropna()
        x = x[x > 0]
        if x.empty:
            st.info("No non-zero transaction volumes available.")
            return

        mean_v = float(x.mean())
        median_v = float(x.median())
        m1, m2 = st.columns(2)
        m1.metric("Mean", f"${mean_v:,.0f}")
        m2.metric("Median", f"${median_v:,.0f}")

        df_hist = pd.DataFrame({"volume_usd": x})
        df_hist["log10_volume"] = np.log10(df_hist["volume_usd"])

        nb = min(30, max(10, int(np.sqrt(len(df_hist)))))

        fig = px.histogram(df_hist, x="log10_volume", nbins=nb, histnorm="probability density")
        lo = float(np.floor(df_hist["log10_volume"].min()))
        hi = float(np.ceil(df_hist["log10_volume"].max()))
        tick_vals = list(np.arange(lo, hi + 1))
        tick_text = [f"10^{k}" if abs(k) > 2 else f"{10**k:g}" for k in tick_vals]

        fig.update_xaxes(tickmode="array", tickvals=tick_vals, ticktext=tick_text, type="linear")
        fig.update_layout(xaxis_title="Transaction Value (USD, log scale)", yaxis_title="Density",
                          margin=dict(t=30, l=10, r=10, b=10))
        fig.add_vline(x=np.log10(mean_v), line_dash="dash", annotation_text=f"Mean: {mean_v:,.0f}")
        fig.add_vline(x=np.log10(median_v), line_dash="solid", annotation_text=f"Median: {median_v:,.0f}")

        z = df_hist["log10_volume"].values
        n = len(z)
        if n >= 2:
            std = np.std(z)
            iqr = np.subtract(*np.percentile(z, [75, 25]))
            sigma = std if (iqr <= 0 or std <= 0) else min(std, iqr / 1.34)
            h = 0.9 * sigma * (n ** (-1 / 5)) if sigma > 0 else 0.1
            h = max(h, 1e-3)

            grid = np.linspace(z.min() - 0.25, z.max() + 0.25, 256)
            diff = (grid[:, None] - z[None, :]) / h
            kde_vals = (np.exp(-0.5 * diff ** 2).sum(axis=1) / (n * h * np.sqrt(2 * np.pi)))
            fig.add_trace(go.Scatter(x=grid, y=kde_vals, mode="lines", name="KDE", hoverinfo="skip"))

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Failed to load Transaction Size Distribution: {e}")
