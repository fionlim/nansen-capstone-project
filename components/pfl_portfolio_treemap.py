# components/pfl_portfolio_treemap.py
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go  # noqa: F401
from nansen_client import NansenClient

def _fetch_balances_df(client: NansenClient, address: str, chain_all: str, hide_spam: bool) -> pd.DataFrame:
    payload = {
        "address": address,
        "chain": chain_all,
        "hide_spam_token": hide_spam,
        "order_by": [{"field": "value_usd", "direction": "DESC"}],
        "pagination": {"page": 1, "per_page": 100}
    }
    resp = client.profiler_address_current_balance(payload)
    return pd.DataFrame(resp)

@st.fragment
def _treemap_fragment(df: pd.DataFrame, *, fragment_key: str = "pfl_portfolio_treemap_fragment"):
    st.subheader("Top Holdings")
    st.text("Box size = USD value; hover for $ and % of portfolio.")

    # Stable radio inside the fragment, so only this fragment updates on toggle
    view_mode = st.radio(
        "Toggle view",
        ["Aggregate by token", "Token → Chain (drilldown)"],
        horizontal=True,
        key=f"{fragment_key}_view_mode"
    )

    if df.empty:
        st.info("No balances found for this wallet on the selected chain(s).")
        return

    df = df.copy()
    df["value_usd"] = pd.to_numeric(df["value_usd"], errors="coerce").fillna(0.0)

    token_totals = (
        df.groupby(["token_symbol", "token_name"], as_index=False)["value_usd"].sum()
    )
    grand_total = token_totals["value_usd"].sum()
    token_totals["portfolio_pct"] = np.where(
        grand_total > 0, 100 * token_totals["value_usd"] / grand_total, 0.0
    )

    pct_threshold = 1.0
    majors = token_totals[token_totals["portfolio_pct"] >= pct_threshold].copy()
    minors = token_totals[token_totals["portfolio_pct"] < pct_threshold].copy()
    others_value = minors["value_usd"].sum()

    if view_mode == "Aggregate by token":
        display_df = majors.sort_values("value_usd", ascending=False).copy()
        if others_value > 0:
            display_df = pd.concat([
                display_df,
                pd.DataFrame([{
                    "token_symbol": "Others",
                    "token_name": "Others",
                    "value_usd": others_value,
                    "portfolio_pct": 100 * others_value / grand_total if grand_total > 0 else 0.0
                }])
            ], ignore_index=True)

        fig = px.treemap(
            display_df,
            path=[px.Constant("Portfolio"), "token_symbol"],
            values="value_usd",
            custom_data=["portfolio_pct", "token_name", "value_usd"],
        )
        fig.update_traces(
            textinfo="label+text",
            texttemplate="<b>%{label}</b><br><sub>%{customdata[0]:.2f}%</sub>",
            marker=dict(line=dict(color="#e0e0e0", width=1)),
            hovertemplate="<b>%{customdata[1]}</b> (%{label})<br>"
                          "Value: $%{customdata[2]:,.2f}<br>"
                          "Portfolio: %{customdata[0]:.2f}%<extra></extra>",
        )
        fig.update_layout(margin=dict(t=30, l=10, r=10, b=10))
        st.plotly_chart(fig, width='stretch')
    else:
        majors_symbols = set(majors["token_symbol"])
        tree_df = df[df["token_symbol"].isin(majors_symbols)].copy()
        if others_value > 0:
            tree_df = pd.concat([
                tree_df,
                pd.DataFrame([{"token_symbol": "Others", "token_name": "Others", "chain": None, "value_usd": others_value}])
            ], ignore_index=True)

        fig2 = px.treemap(
            tree_df,
            path=[px.Constant("Portfolio"), "token_symbol", "chain"],
            values="value_usd",
            custom_data=["token_name", "value_usd"],
        )
        fig2.update_traces(
            textinfo="label+text",
            texttemplate="<b>%{label}</b><br><sub>%{percentRoot:.1%}</sub>",
            marker=dict(line=dict(color="#e0e0e0", width=1)),
            hovertemplate="<b>%{customdata[0]}</b> (%{label})<br>"
                          "Value: $%{customdata[1]:,.2f}<br>"
                          "Of token: %{percentParent:.1%}<br>"
                          "Of portfolio: %{percentRoot:.1%}<extra></extra>",
        )
        fig2.update_layout(margin=dict(t=30, l=10, r=10, b=10))
        st.plotly_chart(fig2, width='stretch')

def render_portfolio_treemap(
    client: NansenClient,
    address: str,
    chain_all: str,
    hide_spam: bool = True,
    *,
    fragment_key: str = "pfl_portfolio_treemap_fragment"
):
    """
    Fetch data once per run (cheap), then let only the fragment re-render when toggling the view.
    No Streamlit cache is used; this simply leverages partial reruns.
    """
    # If you want to avoid refetching even inside the fragment when only the radio changes,
    # we can keep a tiny in-session store keyed by (address, chain_all, hide_spam).
    store_key = f"balances::{address}::{chain_all}::{int(hide_spam)}"
    if "pfl_store" not in st.session_state:
        st.session_state["pfl_store"] = {}
    if store_key not in st.session_state["pfl_store"]:
        st.session_state["pfl_store"][store_key] = _fetch_balances_df(client, address, chain_all, hide_spam)

    df = st.session_state["pfl_store"][store_key]
    _treemap_fragment(df, fragment_key=fragment_key)