import streamlit as st
from typing import Dict
import plotly.graph_objects as go
from nansen_client import NansenClient
from dataframes import net_flow_to_dataframe

@st.fragment
def render_netflow_podium(chains: list, min_mc: int, max_mc: int, excl_labels: list):

    try:
        client = NansenClient()

        if "all" in chains:
            chains = ["all"]
        payload = {
            "chains": chains,
            "filters": {
                "include_stablecoins": False,
                "include_native_tokens": False,
                "market_cap_usd": {
                    "min": min_mc,
                    "max": max_mc
                },
                "exclude_smart_money_labels": excl_labels,
            },
            "pagination": {"page": 1, "per_page": 100},
            "order_by": [{"field": "net_flow_24h_usd", "direction": "DESC"}],
        }

        items = client.smart_money_netflow(payload=payload)
        df = net_flow_to_dataframe(items)
        if df.empty:
            st.warning("No net flow data returned for the selected filters.")
            return

        df_positive = df[df["net_flow_24h_usd"] > 0]
        podium_df = (
            df_positive.sort_values("net_flow_24h_usd", ascending=False)
            .head(3)
        )

        podium_df = podium_df.reset_index(drop=True)
        if len(podium_df) >= 3:
            podium_df = podium_df.iloc[[1, 0, 2]].reset_index(drop=True)
        elif len(podium_df) == 2:
            podium_df = podium_df.iloc[[1, 0]].reset_index(drop=True)

        podium_df["label"] = podium_df.apply(
            lambda r: f"<b>{r['token_symbol']}</b> ({r['chain']}) <br><b>${r['net_flow_24h_usd']:,.0f}</b>", axis=1
        )

        colors = ["#C0C0C0", "#FFD700", "#CD7F32"][:len(podium_df)]
        medals = ["🥈", "🥇", "🥉"][:len(podium_df)]
        if len(podium_df) == 1:
            colors = ["#FFD700"]
            medals = ["🥇"]

        fig = go.Figure(
            go.Bar(
                x=podium_df["label"],
                y=podium_df["net_flow_24h_usd"],
                marker_color=colors,
                hovertemplate="<b>%{x}</b><br><extra></extra>",
                customdata=podium_df["token_address"],
            )
        )

        for i, medal in enumerate(medals):
            fig.add_annotation(
                x=podium_df["label"].iloc[i],
                y=podium_df["net_flow_24h_usd"].iloc[i] + podium_df["net_flow_24h_usd"].max() * 0.1,
                text=medal,
                showarrow=False,
                font=dict(size=40),
            )

        fig.update_layout(
            template="plotly_dark",
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            height=420,
            margin=dict(t=20, b=0),
            showlegend=False,
        )

        st.plotly_chart(fig, use_container_width=True)

        cols = st.columns(len(podium_df))
        for i, col in enumerate(cols):
            token_symbol = podium_df.iloc[i]["token_symbol"]
            token_address = podium_df.iloc[i]["token_address"]
            net_flow_value = podium_df.iloc[i]["net_flow_24h_usd"]
            chain = podium_df.iloc[i]["chain"]

            with col:
                if st.button(f"**{token_symbol}** ({chain})\n**${net_flow_value:,.0f}**",
                             key=f"netflow_{token_address}",
                             use_container_width=True):
                    st.session_state["token"] = token_address
                    st.session_state["chain"] = chain
                    st.switch_page("pages/2_TGM_Dashboard.py")

    except Exception as e:
        st.error(f"Unexpected error: {e}")