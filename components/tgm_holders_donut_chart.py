import streamlit as st
import plotly.express as px
import requests
import pandas as pd

from nansen_client import NansenClient
from dataframes import holders_to_dataframe

@st.cache_data(ttl=300)
def fetch_holders(chain, token_address, aggregate_by_entity):
    client = NansenClient()

    payload = {
        "chain": chain,
        "token_address": token_address,
        "aggregate_by_entity": aggregate_by_entity,
        "label_type": "all_holders",
        "pagination": {
            "page": 1,
            "per_page": 10 
        },
        "filters": {
            "include_smart_money_labels": [
            "30D Smart Trader",
            "Fund",
            "90D Smart Trader",
            "180D Smart Trader", 
            "Smart Trader"
                ],
            "ownership_percentage": {
            "min": 0.001
            },
            "token_amount": {
            "min": 1000
            },
            "value_usd": {
            "min": 10000
            }
        },
        "order_by": [
            {
            "field": "ownership_percentage",
            "direction": "DESC"
            }
        ]
    }

    items = client.tgm_holders(payload, fetch_all=True)
    df = holders_to_dataframe(items)
    
    return df

@st.fragment
def render_holders_donut_chart(chain: str, token_address: str, aggregate_by_entity: bool):
    columns = [
        "address", "address_label", "token_amount", "total_outflow", "total_inflow",
        "balance_change_24h", "balance_change_7d", "balance_change_30d",
        "ownership_percentage", "value_usd", "holder_type"
    ]

    if not token_address or not chain:
        columns_df = pd.DataFrame(columns=columns)
        st.dataframe(columns_df)

        donut_cols = st.columns(3)
        labels = ['smart_money', 'exchange', 'whale', 'public_figure', 'others']
        values = [1, 1, 1, 1, 1]

        fig1 = px.pie(names=labels, values=values, hole=0.5,
                    title='Unique Addresses by Label')
        donut_cols[0].plotly_chart(fig1, width='stretch')

        fig2 = px.pie(names=labels, values=values, hole=0.5,
                    title='Aggregated Token Amount by Label')
        donut_cols[1].plotly_chart(fig2, width='stretch')

        fig3 = px.pie(names=labels, values=values, hole=0.5,
                    title='Aggregated Total Inflow by Label')
        donut_cols[2].plotly_chart(fig3, width='stretch')
    
    else:
        try:
            # holder_types = ['smart_money', 'exchange', 'whale', 'public_figure', 'all_holders']
            df = fetch_holders(chain, token_address, aggregate_by_entity)

            if df.empty:
                st.warning("No holder distribution data returned for the selected filters.")
            else:
                df_display = df.copy()

                num_cols = [
                    "token_amount", "total_outflow", "total_inflow",
                    "balance_change_24h", "balance_change_7d", "balance_change_30d",
                    "ownership_percentage", "value_usd"
                ]
                for col in num_cols:
                    df_display[col] = df_display[col].apply(lambda x: f"{x:,.2f}")

                with st.expander("All Holders' Metrics", expanded=False):
                    with st.container():
                        st.markdown(
                            f'<div style="overflow-y:auto;">',
                            unsafe_allow_html=True
                        )

                        header_cols = st.columns([2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1])
                        for i, col_name in enumerate(columns):
                            with header_cols[i]:
                                st.markdown(f"**{col_name.replace('_', ' ').title()}**", unsafe_allow_html=True)

                        for idx, row in df_display.iterrows():
                            row_cols = st.columns([2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1])
                            for i, col_name in enumerate(columns):
                                with row_cols[i]:
                                    if col_name == "address":
                                        if st.button(f"{row[col_name][:20]}... 🔍", key=f"{row[col_name]}_{idx}"):
                                            st.session_state["wallet"] = row["address"]
                                            st.session_state["label"] = row["address_label"]
                                            st.switch_page("pages/3_Profiler_Dashboard.py")
                                    else:
                                        st.write(row[col_name])
                        st.markdown("</div>", unsafe_allow_html=True)

                #st.dataframe(df) 
                st.subheader('Holder Distribution')
                donut_cols = st.columns(3)
        
                # 1. Distribution of number of unique addresses by label
                address_counts = df.groupby('holder_type')['address'].nunique().reset_index()
                fig1 = px.pie(address_counts, names='holder_type', values='address', hole=0.5,
                            title='Unique Addresses by Label')
                donut_cols[0].plotly_chart(fig1, width='stretch')

                # 2. Aggregated token_amount by label
                token_amounts = df.groupby('holder_type')['token_amount'].sum().reset_index()
                fig2 = px.pie(token_amounts, names='holder_type', values='token_amount', hole=0.5,
                            title='Aggregated Token Amount by Label')
                donut_cols[1].plotly_chart(fig2, width='stretch')

                # 3. Aggregated total_inflow by label
                inflows = df.groupby('holder_type')['total_inflow'].sum().reset_index()
                fig3 = px.pie(inflows, names='holder_type', values='total_inflow', hole=0.5,
                            title='Aggregated Total Inflow by Label')
                donut_cols[2].plotly_chart(fig3, width='stretch')
        except requests.exceptions.HTTPError as http_err:
            st.error(f"Failed to fetch holder distribution data: {http_err}")
        except Exception as e:
            st.error(f"Unexpected error: {e}")