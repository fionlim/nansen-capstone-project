import json
import requests
from typing import Dict
import streamlit as st
from dataframes import net_flow_to_dataframe
import plotly.graph_objects as go
import numpy as np

def render_netflow_scatterplot(payload: Dict):

    try:
        BASE_URL = st.secrets['nansen']['base_url']
        headers = {"apiKey": st.secrets['nansen']['apiKey'],
            "Content-Type": "application/json"}
        response = requests.post(f"{BASE_URL}/smart-money/netflow", headers=headers, data=json.dumps(payload))
        items = response.json().get("data", [])
        df = net_flow_to_dataframe(items)
        if df.empty:
            st.warning("No net flow data returned for the selected filters.")
            return

        chains = df['chain'].unique()
        fig = go.Figure()
        positions = np.linspace(0, 1, len(chains))
        colors = ['rgba(0,100,200,0.5)', 'rgba(0,180,0,0.5)', 'rgba(255,140,0,0.5)']
        for i, chain in enumerate(chains):
            chain_df = df[df['chain'] == chain]

            chain_df = chain_df[chain_df['net_flow_24h_usd'].abs() > 5000]
            chain_df = chain_df.reindex(chain_df['net_flow_24h_usd'].abs().sort_values(ascending=False).index)
            n = len(chain_df)

            column_width = 0.3
            x_jitter = positions[i] + np.random.uniform(-column_width/2, column_width/2, size=n)


            fig.add_trace(go.Scatter(
                x=x_jitter,
                y=chain_df['net_flow_24h_usd'],
                mode='markers',
                marker=dict(size=18, color=colors[i]),
                name=chain,
                customdata=np.stack([
                    [chain]*n,
                    chain_df['net_flow_24h_usd'],
                    chain_df['token_symbol'] if 'token_symbol' in chain_df.columns else chain_df['token_address']
                ], axis=-1),
                hovertemplate=(
                    "Chain: %{customdata[0]}<br>" +
                    "Netflow: %{customdata[1]:,.0f} USD<br>" +
                    "Token: %{customdata[2]}<extra></extra>"
                )
            ))

        fig.update_layout(
            xaxis=dict(
                tickmode='array',
                tickvals=positions,
                ticktext=chains,
                type='linear',
            ),
            yaxis=dict(
                title='Netflow (USD, 24h)',
                zeroline=True,
                showline=True
            ),
            showlegend=False,
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Unexpected error: {e}")