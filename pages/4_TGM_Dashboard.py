#!/usr/bin/env python3

import os
import json
import streamlit as st
from dotenv import load_dotenv
import pandas as pd
import numpy as np
import plotly.express as px
from components.holders import render_holder_distribution, render_inflow_outflow_bar_chart
from components.pnl_leaderboard import render_holder_pnl_bubble_chart

DEFAULT_TOKEN_ADDRESS = "2zMMhcVQEXDtdE6vsFS7S7D5oUodfJHE8vd1gnBouauv"
DEFAULT_CHAIN = "solana"

HOLDERS_DEFAULT_PAYLOAD = {
    "chain": DEFAULT_CHAIN,
    "token_address": DEFAULT_TOKEN_ADDRESS,
    "aggregate_by_entity": True,
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
        "Fund",
        "Smart Trader"
            ],
        "ownership_percentage": {
        "min": 0.00
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

PnL_LEADERBOARD_DEFAULT_PAYLOAD = {
    "chain": DEFAULT_CHAIN,
    "token_address": DEFAULT_TOKEN_ADDRESS,
    "date": {
        "from": "2025-07-14",
        "to": "2025-07-15"
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
        "direction": "ASC"
    }
    ]
}



def main():
    st.set_page_config(page_title="Holder Dashboard", layout="wide")
    
    # Handle authentication
    if not st.user.is_logged_in:
        st.title("Nansen.ai Profiler API Dashboard")
        st.write("Please log in to access the dashboard.")
        if st.button("Log in"):
            st.login()
        st.stop()
    
    # User is logged in - show logout button and user info
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("Nansen.ai Holder API Dashboard")
    with col2:
        if st.button("Log out"):
            st.logout()
    
    st.write(f"Hello, {st.user.name}!")

    # Check API key after login
    # load_dotenv()
    # api_key = os.getenv("apiKey")
    # print("API KEY: {api_key}")
    # if not api_key:
    #     st.error("Missing API key. Add 'apiKey' to your .env file.")
    #     st.stop()

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
    # label_type = st.selectbox('Label Type', ['whale','public_figure','smart_money','all_holders','exchange'], index=[
    #     'whale','public_figure','smart_money','all_holders','exchange'
    # ].index(DEFAULT_PAYLOAD.get('label_type', 'all_holders')))

    # Update payload with widget values
    holders_payload = HOLDERS_DEFAULT_PAYLOAD.copy()
    holders_payload['chain'] = chain
    holders_payload['token_address'] = token_address
    holders_payload['aggregate_by_entity'] = aggregate_by_entity
    # payload['label_type'] = label_type 

    # render_holder_distribution(holders_payload)
    # render_inflow_outflow_bar_chart(holders_payload)
    render_holder_pnl_bubble_chart(PnL_LEADERBOARD_DEFAULT_PAYLOAD)

    

if __name__ == "__main__":
    main()
