from typing import Dict
import streamlit as st
import plotly.express as px 
from nansen_client import NansenClient
from dataframes import pnl_leaderboard_to_dataframe, pnl_summary_to_dataframe
import pandas as pd
import plotly.graph_objects as go

def render_pnl_leaderboard_bubble_chart(payload: Dict):
    client = NansenClient()
    try:
        leaderboard_items = client.tgm_pnl_leaderboard(payload)
        leaderboard_df = pnl_leaderboard_to_dataframe(leaderboard_items).head(100)  # Limit to top 100 for performance

        summary_payload = [{"chain": payload["chain"],
                           "address": trader_address,
                           "date": payload["date"]} for trader_address in leaderboard_df['trader_address'].tolist()]
        
        summary_items = client.pfl_address_pnl_summary(summary_payload)
        summary_df = pnl_summary_to_dataframe(summary_items)
        df = pd.merge(leaderboard_df, summary_df, left_on='trader_address', right_on='address', how='left', suffixes=('', '_summary'))
        if df.empty:
            st.warning("No PnL data returned for the selected filters.")
        else:
            st.subheader('Holder PnL Bubble Chart')
            # Create bubble chart
            fig = px.scatter(
                df, 
                x='pnl_usd_realised', 
                y='pnl_usd_unrealised', 
                size='holding_usd', 
                # color='holder_type',
                hover_name='trader_address_label',
                hover_data={'win_rate': True},
                log_x=True,
                log_y=True,
                size_max=60,
                title='Holder PnL Bubble Chart (Log Scale)'
            )
            fig.update_layout(
                xaxis_title='PnL Realized(USD)',
                yaxis_title='PnL Unrealized (USD)',
                legend_title='Holder Type',
                template='plotly_white'
            )
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Unexpected error: {e}" )