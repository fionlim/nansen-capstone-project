#!/usr/bin/env python3

import os
import json
import streamlit as st
from dotenv import load_dotenv

from components.smart_money import render_smart_money

DEFAULT_PAYLOAD = {
        "parameters": {
            "smFilter": [
                "180D Smart Trader",
                "Fund",
                "Smart Trader"
            ],
            "chains": [
                "ethereum",
                "solana"
            ],
            "includeStablecoin": True,
            "includeNativeTokens": True,
            "excludeSmFilter": []
        },
        "pagination": {
            "page": 1,
            "recordsPerPage": 100
        }
    }


def main():
    st.set_page_config(page_title="Smart Money Dashboard", layout="wide")
    
    # Handle authentication
    if not st.user.is_logged_in:
        st.title("Nansen.ai Smart Money API Dashboard")
        st.write("Please log in to access the dashboard.")
        if st.button("Log in"):
            st.login()
        st.stop()
    
    # User is logged in - show logout button and user info
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("Nansen.ai Smart Money API Dashboard")
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

    include_stable = st.checkbox("Include Stablecoins", value=True)
    include_native = st.checkbox("Include Native Tokens", value=True)
    page_size = st.slider("Records per page", 10, 200, 100, 10)
    new_token_max_days = st.number_input(
        "Max token age (days) to consider 'new'",
        min_value=1, max_value=3650, value=30, step=1
    )
    selected_chains = st.multiselect(
        "Chains",
        options=["ethereum", "solana"],
        default=["ethereum", "solana"]
    )
    selected_filters = st.multiselect(
        "Smart Money Filters",
        options=["180D Smart Trader", "Fund", "Smart Trader"],
        default=["180D Smart Trader", "Fund", "Smart Trader"]
    )
    submitted = st.button("Run Query")

    payload = json.loads(json.dumps(DEFAULT_PAYLOAD))
    payload["parameters"]["includeStablecoin"] = include_stable
    payload["parameters"]["includeNativeTokens"] = include_native
    payload["parameters"]["chains"] = selected_chains
    payload["parameters"]["smFilter"] = selected_filters
    payload["pagination"]["recordsPerPage"] = page_size

    if submitted:
        render_smart_money(payload, new_token_max_days)

if __name__ == "__main__":
    main()
