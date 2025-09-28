#!/usr/bin/env python3

import os
import json
import streamlit as st
from dotenv import load_dotenv

from components.token_screener import render_token_screener, render_flow_intelligence

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
    st.set_page_config(page_title="Token Screener Dashboard", layout="wide")
    
    # Handle authentication
    if not st.user.is_logged_in:
        st.title("Nansen.ai Token Screener API Dashboard")
        st.write("Please log in to access the dashboard.")
        if st.button("Log in"):
            st.login()
        st.stop()
    
    # User is logged in - show logout button and user info
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("Nansen.ai Token Screener API Dashboard")
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

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        screener_chains = st.multiselect(
            "Chains",
            options=["ethereum", "solana", "base"],
            default=["ethereum", "solana", "base"]
        )
    with col_b:
        date_from = st.date_input("From date")
    with col_c:
        date_to = st.date_input("To date")
    only_sm = st.checkbox("Only Smart Money", value=True)
    screener_page_size = st.slider("Screener records per page", 10, 200, 100, 10)
    run_screener = st.button("Run Screener")

    if run_screener:
        parameters = {
            "chains": screener_chains or ["ethereum", "solana", "base"],
            "watchlistFilter": [],
            "sectorsFilter": [],
            "smLabelFilter": [],
            "onlySmartMoney": bool(only_sm)
        }
        if date_from and date_to:
            parameters["date"] = {"from": str(date_from), "to": str(date_to)}
        pagination = {"page": 1, "recordsPerPage": int(screener_page_size)}
        # Mark trigger for downstream to persist df in session
        st.session_state["_trigger_run_screener"] = True
        render_token_screener(parameters, pagination)

    st.divider()
    st.subheader("Flow Intelligence")
    with st.form("flow_intel_form", clear_on_submit=False):
        c1, c2, c3, c4 = st.columns([1,2,1,1])
        with c1:
            fi_chain = st.selectbox("Chain", options=["ethereum", "solana", "base"], index=0)
        with c2:
            fi_token = st.text_input("Token address (hex)", value="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48")
        with c3:
            fi_timeframe = st.selectbox("Timeframe", options=["1d", "7d", "30d"], index=0)
        with c4:
            fi_rpp = st.number_input("Records/page", min_value=10, max_value=200, value=100, step=10)
        run_flow = st.form_submit_button("Run Flow Intelligence")

    if run_flow:
        pagination = {"page": 1, "recordsPerPage": int(fi_rpp)}
        render_flow_intelligence(fi_chain, fi_token.strip(), fi_timeframe, pagination)


if __name__ == "__main__":
    main()
