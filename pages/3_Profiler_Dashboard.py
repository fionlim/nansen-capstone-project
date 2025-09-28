#!/usr/bin/env python3

import os
import json
import streamlit as st
from dotenv import load_dotenv

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
    st.set_page_config(page_title="Profiler Dashboard", layout="wide")
    
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
        st.title("Nansen.ai Profiler API Dashboard")
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

if __name__ == "__main__":
    main()
