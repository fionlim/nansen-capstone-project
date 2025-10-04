from typing import Dict
import streamlit as st
import plotly.graph_objects as go
from nansen_client import NansenClient
from dataframes import dex_trades_to_dataframe
import pandas as pd

def render_dex_trades_hourly(payload: Dict):
    client = NansenClient()

    try:
        items = client.dex_trades(payload)
        df = dex_trades_to_dataframe(items)
        if df.empty:
            st.warning("No DEX trades data returned for the selected filters.")
        else:
            st.subheader('DEX Trades Hourly Overview')
            # Convert block_timestamp to datetime
            df['block_timestamp'] = pd.to_datetime(df['block_timestamp'])

            # Filter for transactions in the last 24 hours
            latest_time = df['block_timestamp'].max()
            last_24h = latest_time - pd.Timedelta(hours=24)
            print(last_24h, latest_time)
            df_24h = df[df['block_timestamp'] >= last_24h].copy()

            # Simplify block_timestamp to just date and hour
            df_24h['hour'] = df_24h['block_timestamp'].dt.hour

            # Aggregate: count transactions and sum traded_token_amount per hour
            hourly_agg = df_24h.groupby(['hour']).agg(
                transactions_count=('block_timestamp', 'count'),
                traded_token_amount=('traded_token_amount', 'sum')
            ).reset_index()

            # Combined line-bar chart
            fig = go.Figure()
            # Bar for traded token amount
            fig.add_trace(go.Bar(
                x=hourly_agg['hour'],
                y=hourly_agg['traded_token_amount'],
                name='Traded Token Amount',
                marker_color='rgba(55, 83, 109, 0.7)',
                yaxis='y2'
            ))
            # Line for transactions count
            fig.add_trace(go.Scatter(
                x=hourly_agg['hour'],
                y=hourly_agg['transactions_count'],
                name='Transactions Count',
                mode='lines+markers',
                marker_color='rgba(26, 118, 255, 1)',
                yaxis='y1'
            ))

            fig.update_layout(
                title='Hourly Transactions Count & Traded Token Amount (Last 24 Hours)',
                xaxis=dict(title='Hour of Day'),
                yaxis=dict(
                    title='Transactions Count',
                    side='left',
                    showgrid=False
                ),
                yaxis2=dict(
                    title='Traded Token Amount',
                    overlaying='y',
                    side='right',
                    showgrid=False
                ),
                legend=dict(x=0.01, y=0.99),
                bargap=0.2,
                template='plotly_white'
            )
            st.plotly_chart(fig, use_container_width=True)
            
    except Exception as e:
        st.error(f"Unexpected error: {e}" )