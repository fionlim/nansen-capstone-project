import streamlit as st
from typing import Dict
from nansen_client import NansenClient
from dataframes import net_flow_to_dataframe
import plotly.graph_objects as go
import numpy as np

def render_netflow_scatterplot(payload: Dict):
    col5, col6 = st.columns(2)
    with col5:
        st.write("Time period: Past 24 hours")

    try:
        client = NansenClient()
        items = client.smart_money_netflow(payload, fetch_all=False)
        df = net_flow_to_dataframe(items)
        if df.empty:
            st.warning("No net flow data returned for the selected filters.")
            return
        
        df = df[df["net_flow_24h_usd"].abs() > 5000]
        df = df.sort_values(by="net_flow_24h_usd", key=lambda x: x.abs(), ascending=False).reset_index(drop=True)

        with col6:
            col7, col8 = st.columns([2, 1])
            with col7:
                selected_token = st.selectbox("Select a token", df['token_symbol'].unique(), index=0, label_visibility="hidden")
            with col8:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Get Metrics", use_container_width=True):
                    st.session_state["selected_token"] = df.loc[df["token_symbol"] == selected_token, "token_address"].iloc[0]
                    st.session_state["chain"] = df.loc[df["token_symbol"] == selected_token, "chain"].iloc[0]
                    st.switch_page("pages/2_TGM_Dashboard.py")

        chains = df['chain'].unique()
        fig = go.Figure()
        positions = np.linspace(0, 1, len(chains))
        colors = ['rgba(0,100,200,0.5)', 'rgba(0,180,0,0.5)', 'rgba(255,140,0,0.5)']
        for i, chain in enumerate(chains):
            chain_df = df[df['chain'] == chain]
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
            height=500,
            margin=dict(t=40)
        )

        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Unexpected error: {e}")