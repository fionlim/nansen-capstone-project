import streamlit as st
from dataframes import historical_balances_to_dataframe

@st.cache_data(ttl=300)
def fetch_historical_balances(_client, wallet, chain_all, from_iso, to_iso):
    payload = {
        "address": wallet,
        "chain": chain_all,
        "date": {
            "from": f"{from_iso}", 
            "to": f"{to_iso}"
        },
        "pagination": {
            "page": 1, 
            "per_page": 100
        },
    }

    items = _client.profiler_address_historical_balances(payload=payload, fetch_all=True)
    df = historical_balances_to_dataframe(items)
    
    return df

def render_portfolio_value_metrics(client, wallet, chain_all, from_iso, to_iso):
    df = fetch_historical_balances(client, wallet, chain_all, from_iso, to_iso)
    if df.empty:
        st.warning("No portfolio data found.")
        return

    # latest snapshot per token
    snapshot = df.sort_values("block_timestamp").groupby("token_symbol").last()
    portfolio_value = snapshot["value_usd"].sum()
    num_tokens = len(snapshot)

    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Total Portfolio Value (USD)", value=f"${portfolio_value:,.2f}")

    with col2:
        st.metric(label="Number of Tokens Held", value=num_tokens)