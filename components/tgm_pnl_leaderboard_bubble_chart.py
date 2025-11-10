from datetime import datetime as dt
import streamlit as st
import plotly.express as px 
import pandas as pd
import plotly.graph_objects as go

from nansen_client import NansenClient
from dataframes import pnl_leaderboard_to_dataframe, pnl_summary_to_dataframe

@st.cache_data(ttl=300)
def fetch_token_leaderboard(chain, token_address, DATE_FROM, DATE_TO):
    client = NansenClient()

    payload = {
        "chain": chain,
        "token_address": token_address,
        "date": {
            "from": DATE_FROM,
            "to": DATE_TO
        },
        "pagination": {
            "page": 1,
            "per_page": 100
        },
        "filters": {
            "holding_usd": {
                "min": 1000
            },
            "pnl_usd_realised": {
                "min": 1000
            }
        },
        "order_by": [
            {
                "field": "pnl_usd_realised",
                "direction": "DESC"
            }
        ]
    }

    items = client.tgm_pnl_leaderboard(payload)
    df = pnl_leaderboard_to_dataframe(items)
    
    return df

@st.cache_data(ttl=300)
def fetch_pfl_leaderboard(chain, leaderboard_df, DATE_FROM, DATE_TO):
    client = NansenClient()

    payload = [
        {"chain": chain,
        "address": trader_address,
        "date": {
            "from": DATE_FROM,
            "to": DATE_TO
        },
        } for trader_address in leaderboard_df['trader_address'].tolist()]

    items = client.pfl_address_pnl_summary(payload)
    df = pnl_summary_to_dataframe(items)
    
    return df

@st.fragment
def render_pnl_leaderboard_bubble_chart(chain: str, token_address: str):
    if not token_address or not chain:

        df_empty = pd.DataFrame({
            'pnl_usd_realised': [1, 1e6],
            'pnl_usd_unrealised': [1, 1e6],
        })

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df_empty['pnl_usd_realised'],
            y=df_empty['pnl_usd_unrealised'],
            mode='markers',
            marker=dict(size=0, opacity=0)
        ))

        tickvals = [1, 1e1, 1e3, 1e6]
        ticktext = ['0', '10k', '100k', '1M']

        fig.update_layout(
            xaxis_title='PnL Realized (USD)',
            yaxis_title='PnL Unrealized (USD)',
            xaxis=dict(type='log', tickvals=tickvals, ticktext=ticktext),
            yaxis=dict(type='log', tickvals=tickvals, ticktext=ticktext),
            template='plotly_white'
        )

        st.plotly_chart(fig, width='stretch')

    else:
        DATE_FROM = (dt.today() - pd.Timedelta(days=7)).strftime('%Y-%m-%d')  # one week ago
        DATE_TO = dt.today().strftime('%Y-%m-%d') # today
        try:
            leaderboard_df = fetch_token_leaderboard(chain, token_address, DATE_FROM, DATE_TO)  # Limit to top 100 for performance
            summary_df = fetch_pfl_leaderboard(chain, leaderboard_df, DATE_FROM, DATE_TO)

            df = pd.merge(leaderboard_df, summary_df, left_on='trader_address', right_on='address', how='left', suffixes=('', '_summary'))
            if df.empty:
                st.warning("No PnL data returned for the selected filters.")
            else:
                col1, col2, col3 = st.columns([3, 2, 1])
                df_display = df.dropna(subset=['pnl_usd_realised', 'pnl_usd_unrealised', 'trader_address_label'])
                
                with col1:
                    st.write('Holder PnL Bubble Chart (Log Scale)')

                with col2:
                    selected_label = st.selectbox(
                        "Select wallet", 
                        df_display['trader_address_label'].fillna("Unknown").unique(),
                        index=0,
                        label_visibility="hidden"
                    )
                    
                with col3:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("Go to Profile", width='stretch'):
                        wallet_row = df_display[df_display['trader_address_label'] == selected_label].iloc[0]
                        st.session_state["wallet"] = wallet_row['trader_address']
                        st.session_state["label"] = wallet_row['trader_address_label']
                        st.switch_page("pages/3_Profiler_Dashboard.py")

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
                )
                fig.update_layout(
                    xaxis_title='PnL Realized(USD)',
                    yaxis_title='PnL Unrealized (USD)',
                    legend_title='Holder Type',
                    template='plotly_white'
                )
                st.plotly_chart(fig, width='stretch')

        except Exception as e:
            st.error(f"Unexpected error: {e}" )