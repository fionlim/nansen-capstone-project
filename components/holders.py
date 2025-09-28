from typing import Dict
import streamlit as st
import plotly.express as px 
from nansen_client import NansenClient
from dataframes import holders_to_dataframe
import pandas as pd

def render_holder_distribution(payload: Dict):
    client = NansenClient()

    try:
        holder_types = ['exchange', 'whale']
        df = pd.DataFrame()
        for type in holder_types:
            payload['label_type'] = type
            items = client.tgm_holders(payload)
            holder_type_df = holders_to_dataframe(items)
            holder_type_df['holder_type'] = type
            if df.empty:
                df = holder_type_df
            else: 
                df = pd.concat([df, holder_type_df], ignore_index=True)
        if df.empty:
            st.warning("No holder distribution data returned for the selected filters.")
        else:
            st.dataframe(df) 
            st.subheader('Holder Distribution')
            donut_cols = st.columns(3)
    
            # 1. Distribution of number of unique addresses by label
            address_counts = df.groupby('holder_type')['address'].nunique().reset_index()
            fig1 = px.pie(address_counts, names='holder_type', values='address', hole=0.5,
                        title='Unique Addresses by Label')
            donut_cols[0].plotly_chart(fig1, use_container_width=True)

            # 2. Aggregated token_amount by label
            token_amounts = df.groupby('holder_type')['token_amount'].sum().reset_index()
            fig2 = px.pie(token_amounts, names='holder_type', values='token_amount', hole=0.5,
                        title='Aggregated Token Amount by Label')
            donut_cols[1].plotly_chart(fig2, use_container_width=True)

            # 3. Aggregated total_inflow by label
            inflows = df.groupby('holder_type')['total_inflow'].sum().reset_index()
            fig3 = px.pie(inflows, names='holder_type', values='total_inflow', hole=0.5,
                        title='Aggregated Total Inflow by Label')
            donut_cols[2].plotly_chart(fig3, use_container_width=True)

            render_inflow_outflow_bar_chart(df)
    except Exception as e:
        st.error(f"Unexpected error: {e}" )

def render_inflow_outflow_bar_chart(payload: Dict):
    """
    Render a centered horizontal bar chart with inflow (green, right) and outflow (red, left) by holder_type.
    Fetches data using the same payload logic as render_holder_distribution.
    """
    client = NansenClient()
    holder_types = ['exchange', 'whale']
    df = pd.DataFrame()
    for type in holder_types:
        payload['label_type'] = type
        items = client.tgm_holders(payload)
        holder_type_df = holders_to_dataframe(items)
        holder_type_df['holder_type'] = type
        if df.empty:
            df = holder_type_df
        else:
            df = pd.concat([df, holder_type_df], ignore_index=True)
    if df.empty:
        st.warning("No holder distribution data returned for the selected filters.")
        return
    import plotly.graph_objects as go
    agg = df.groupby('holder_type').agg({
        'total_inflow': 'sum',
        'total_outflow': 'sum'
    }).reset_index()
    agg['total_outflow'] = -agg['total_outflow']
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