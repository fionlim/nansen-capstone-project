from typing import Dict
import streamlit as st
import plotly.express as px 
from nansen_client import NansenClient
from dataframes import holders_to_dataframe
import pandas as pd
import plotly.graph_objects as go

def render_holders_donut_chart(payload: Dict):
    client = NansenClient()

    try:
        # holder_types = ['smart_money', 'exchange', 'whale', 'public_figure', 'all_holders']
        items = client.tgm_holders(payload)
        df = holders_to_dataframe(items)

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

    except Exception as e:
        st.error(f"Unexpected error: {e}" )