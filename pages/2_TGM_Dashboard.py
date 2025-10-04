#!/usr/bin/env python3
from datetime import datetime as dt
import streamlit as st
import pandas as pd

from components.holder_flows_horizontal_bar_chart import render_holder_flows_horizontal_bar_chart
from components.holders_donut_chart import render_holders_donut_chart
from components.pnl_leaderboard_bubble_chart import render_pnl_leaderboard_bubble_chart
from components.dex_trades_hourly import render_dex_trades_hourly

DEFAULT_TOKEN_ADDRESS = "2zMMhcVQEXDtdE6vsFS7S7D5oUodfJHE8vd1gnBouauv"
DEFAULT_CHAIN = "solana"
DATE_FROM = (dt.today() - pd.Timedelta(days=7)).strftime('%Y-%m-%d')  # one week ago
DATE_TO = dt.today().strftime('%Y-%m-%d') # today

HOLDERS_DEFAULT_PAYLOAD = {
    "chain": DEFAULT_CHAIN,
    "token_address": DEFAULT_TOKEN_ADDRESS,
    "aggregate_by_entity": True,
    "label_type": "all_holders",
    "pagination": {
        "page": 1,
        "per_page": 100 
    },
    "filters": {
        "include_smart_money_labels": [
        "30D Smart Trader",
        "Fund",
        "90D Smart Trader",
        "180D Smart Trader", 
        "Fund",
        "Smart Trader"
            ],
        "ownership_percentage": {
        "min": 0.001
        },
        "token_amount": {
        "min": 10000
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

PnL_LEADERBOARD_DEFAULT_PAYLOAD = {
    "chain": DEFAULT_CHAIN,
    "token_address": DEFAULT_TOKEN_ADDRESS,
    "date": {
        "from": DATE_FROM,
        "to": DATE_TO
    },
    "pagination": {
    "page": 1,
    "per_page": 10
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

DEX_TRADES_DEFAULT_PAYLOAD = {
    "chain": DEFAULT_CHAIN,
    "token_address": DEFAULT_TOKEN_ADDRESS,
    "only_smart_money": False,
    "date": {
    "from": (dt.today() - pd.Timedelta(days=2)).strftime('%Y-%m-%d'),
    "to": DATE_TO
    },
    "pagination": {
    "page": 1,
    "per_page": 100
    },
    "filters": {
    "action": "BUY",
    "estimated_value_usd": {
        "min": 1000
    },
    "include_smart_money_labels": [
        "Whale",
        "Smart Trader"
    ],
    "token_amount": {
        "min": 100
    }
    },
    "order_by": [
    {
        "field": "block_timestamp",
        "direction": "ASC"
    }
    ]
}



def main():
    st.set_page_config(page_title="TGM Dashboard", layout="wide")
    
    # Handle authentication
    if not st.user.is_logged_in:
        st.title("Nansen.ai API Dashboard")
        st.write("Please log in to access the dashboard.")
        if st.button("Log in"):
            st.login()
        st.stop()
    
    # User is logged in - show logout button and user info
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("Nansen.ai TGM API Dashboard")
    with col2:
        if st.button("Log out"):
            st.logout()
    
    st.write(f"Hello, {st.user.name}!")

    # Input widgets for payload variables
    st.subheader('Holder Distribution Query Settings')
    chain = st.selectbox(
        'Chain',
        [
            'arbitrum','avalanche','base','berachain','blast','bnb','ethereum','goat','hyperevm','iotaevm','linea','mantle','optimism','polygon','ronin','sei','scroll','sonic','unichain','zksync','bitcoin','solana','ton','tron','starknet'
        ],
        index=[
            'arbitrum','avalanche','base','berachain','blast','bnb','ethereum','goat','hyperevm','iotaevm','linea','mantle','optimism','polygon','ronin','sei','scroll','sonic','unichain','zksync','bitcoin','solana','ton','tron','starknet'
        ].index(HOLDERS_DEFAULT_PAYLOAD.get('chain ', 'solana'))
    )
    token_address = st.text_input('Token Address', value=HOLDERS_DEFAULT_PAYLOAD.get('token_address', ''))
    aggregate_by_entity = st.selectbox('Aggregate by Entity', [True, False], index=0 if HOLDERS_DEFAULT_PAYLOAD.get('aggregate_by_entity', True) else 1)

    # Update payload with widget values
    holders_payload = HOLDERS_DEFAULT_PAYLOAD.copy()
    holders_payload['chain'] = chain
    holders_payload['token_address'] = token_address
    holders_payload['aggregate_by_entity'] = aggregate_by_entity
    # payload['label_type'] = label_type 

    render_holders_donut_chart(holders_payload)
    render_holder_flows_horizontal_bar_chart(holders_payload)
    render_pnl_leaderboard_bubble_chart(PnL_LEADERBOARD_DEFAULT_PAYLOAD)
    render_dex_trades_hourly(DEX_TRADES_DEFAULT_PAYLOAD)

    

if __name__ == "__main__":
    main()
