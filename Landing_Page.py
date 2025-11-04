#!/usr/bin/env python3
import json
import streamlit as st

from components.sm_netflow_scatterplot import render_netflow_scatterplot
from components.sm_trade_value_podium import render_dex_trades_podium
from components.sm_netflow_podium import render_netflow_podium


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

    st.header("What are Smart Money Buying?")
    col_1, col_2 = st.columns(2)
    with col_1:
        all_chains = ["ethereum", "solana", "base", 
            "arbitrum", "avalanche", "berachain", 
            "blast", "bnb", "goat", 
            "hyperevm", "iotaevm", "linea", 
            "mantle", "optimism", "polygon",
            "ronin", "sei", "scroll", 
            "sonic", "unichain", "zksync"]
        selected_chains = st.multiselect(
            "Select Chains",
            options=["all"] + all_chains,
            default=["all"]
        )
        smart_money_labels = [
            "Fund", "Smart Trader", "30D Smart Trader",
            "90D Smart Trader", "180D Smart Trader"
        ]
        exclude_smart_money_labels = st.multiselect(
            "Exclude Smart Money Labels",
            options=smart_money_labels,
            default=[]
        )
    with col_2:
        col_min, col_max = st.columns(2)
        with col_min:
            min_market_cap = st.number_input(
                "Min Token Market Cap (USD)",
                min_value=0, value=1_000_000, step=100_000, format="%d"
            )
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.button("Apply Filters")
        with col_max:
            max_market_cap = st.number_input(
                "Max Token Market Cap (USD)",
                min_value=min_market_cap, value=10_000_000_000, step=100_000, format="%d"
            )
    col3, col4 = st.columns(2)
    with col3:
        DEX_DEFAULT_PAYLOAD = {
            "chains": [
                "all"
            ],
            "filters": {},
            "pagination": {
                "page": 1,
                "per_page": 100
            },
            "order_by": [
                {
                    "field": "trade_value_usd",
                    "direction": "DESC"
                }
            ]
        }
        st.subheader("Top 3 Tokens by DEX Trading Value (24h)")
        value_payload = json.loads(json.dumps(DEX_DEFAULT_PAYLOAD))
        if "all" in selected_chains or set(selected_chains) == set(all_chains):
            value_payload["chains"] = ["all"]
        else:
            value_payload["chains"] = selected_chains
        value_payload["filters"]["token_bought_market_cap"] = {
            "min": min_market_cap,
            "max": max_market_cap
        }
        value_payload["filters"]["exclude_smart_money_labels"] = exclude_smart_money_labels
        if submitted:
            render_dex_trades_podium(value_payload)
        else:
            render_dex_trades_podium(DEX_DEFAULT_PAYLOAD)
    with col4:
        NETFLOW_DEFAULT_PAYLOAD = {
            "chains": [
                "all"
            ],
            "filters": {
                "include_stablecoins": False,
                "include_native_tokens": False
            },
            "pagination": {
                "page": 1,
                "per_page": 100
            },
            "order_by": [
                {
                    "field": "net_flow_24h_usd",
                    "direction": "DESC"
                }
            ]
        }
        st.subheader("Top 3 Tokens by Netflow (24h)")

        netflow_payload = json.loads(json.dumps(NETFLOW_DEFAULT_PAYLOAD))
        if "all" in selected_chains or set(selected_chains) == set(all_chains):
            netflow_payload["chains"] = ["all"]
        else:
            netflow_payload["chains"] = selected_chains
        netflow_payload["filters"]["market_cap_usd"] = {
            "min": min_market_cap,
            "max": max_market_cap 
        }
        netflow_payload["filters"]["exclude_smart_money_labels"] = exclude_smart_money_labels
        if submitted:
            render_netflow_podium(netflow_payload)
        else:
            render_netflow_podium(NETFLOW_DEFAULT_PAYLOAD)

    SCATTERPLOT_DEFAULT_PAYLOAD = {
        "chains": [
            "ethereum",
            "solana",
            "base"
        ],
        "filters": {
            "include_stablecoins": False,
            "include_native_tokens": False
        },
        "pagination": {
            "page": 1,
            "per_page": 100
        },
    }
    st.divider()
    st.subheader("Token Netflow Distribution (Netflow > $5,000)")
    render_netflow_scatterplot(SCATTERPLOT_DEFAULT_PAYLOAD)

if __name__ == "__main__":
    main()
