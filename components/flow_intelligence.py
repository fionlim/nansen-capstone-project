from typing import Dict
import streamlit as st
import plotly.express as px 
from nansen_client import NansenClient
from dataframes import flows_to_dataframe
import pandas as pd

def render_flow_intelligence(payload: Dict):
    client = NansenClient()

    try:
        items = client.flow_intelligence(payload)
        df = flows_to_dataframe(items)
        if df.empty:
            st.warning("No flow intelligence data returned for the selected filters.")
        else:
            st.dataframe(df) 
            st.subheader('Flow Intelligence Overview')
            fig = px.bar(df, x='tokenSymbol', y='netflow', color='chain',
                         title='Net Flow by Token and Chain', barmode='group')
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Unexpected error: {e}" )