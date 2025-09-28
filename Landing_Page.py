#!/usr/bin/env python3

import os
import json
import streamlit as st
from dotenv import load_dotenv


def main():
    st.set_page_config(page_title="Landing Page", layout="wide")
    
    # Handle authentication
    if not st.user.is_logged_in:
        st.title("Nansen.ai API Dashboard")
        st.write("Please log in to access the dashboards.")
        if st.button("Log in"):
            st.login()
        st.stop()

    st.sidebar.success("Check out our dashboards above!")

    # User is logged in - show logout button and user info
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("Nansen.ai Capstone Project")
    with col2:
        if st.button("Log out"):
            st.logout()

    st.markdown("""
        We leverage **Nansen’s API** to analyze blockchain data and uncover insights into wallet activity, 
        token movements, and emerging trends.  

        Built with **Python** and **Streamlit**, our platform combines powerful data processing 
        (**pandas**), interactive visualizations (**Plotly** and **Pydeck**), and machine learning 
        techniques (**scikit-learn**) to transform raw on-chain data into meaningful, easy-to-understand insights.  

        🚀 Explore our dashboards to dive deeper into the world of **Web3 analytics**.
    """)
    
    st.write(f"Hello, {st.user.name}!")




if __name__ == "__main__":
    main()
