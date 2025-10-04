from typing import Dict
import streamlit as st
import plotly.express as px 
from nansen_client import NansenClient
from dataframes import holders_to_dataframe
import pandas as pd
import plotly.graph_objects as go

def render_holder_flows_horizontal_bar_chart(payload: Dict):
    """
    Render a centered horizontal bar chart with inflow (green, right) and outflow (red, left) by holder_type.
    Fetches data using the same payload logic as render_holder_distribution.
    """
    client = NansenClient()
    items = client.tgm_holders(payload)
    df = holders_to_dataframe(items)

    if df.empty:
        st.warning("No holder distribution data returned for the selected filters.")
        return
    agg = df.groupby('holder_type').agg({
        'total_inflow': 'sum',
        'total_outflow': 'sum'
    }).reset_index()
    agg['total_outflow'] = -agg['total_outflow']
    print(agg['holder_type'].unique())
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=agg['holder_type'],
        x=agg['total_inflow'],
        name='Inflow',
        orientation='h',
        marker_color='green',
        hovertemplate='Inflow: %{x}<extra></extra>'
    ))
    fig.add_trace(go.Bar(
        y=agg['holder_type'],
        x=agg['total_outflow'],
        name='Outflow',
        orientation='h',
        marker_color='red',
        hovertemplate='Outflow: %{x}<extra></extra>'
    ))
    fig.update_layout(
        barmode='relative',
        title='Total Inflow vs Outflow by Holder Type',
        xaxis_title='Amount',
        yaxis_title='Holder Type',
        bargap=0.3,
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=True,
        xaxis=dict(zeroline=True, zerolinewidth=2, zerolinecolor='gray')
    )
    st.plotly_chart(fig, use_container_width=True)

