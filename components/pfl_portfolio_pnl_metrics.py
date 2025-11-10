import streamlit as st
from dataframes import single_pnl_summary_to_dataframe

@st.cache_data(ttl=300)
def fetch_profiler_address_pnl_summary(_client, wallet, chain_all, from_iso, to_iso):
    payload = {
        "address": wallet,
        "chain": chain_all,
        "date": {
            "from": f"{from_iso}", 
            "to": f"{to_iso}"
        },
    }

    items = _client.profiler_address_pnl_summary(payload=payload)
    df = single_pnl_summary_to_dataframe(items)
    
    return df

def render_portfolio_pnl_metrics(client, wallet, chain_all, from_iso, to_iso):


    df = fetch_profiler_address_pnl_summary(client, wallet, chain_all, from_iso, to_iso)
    if df.empty:
        st.warning("No pnl data found.")
        return

    realized_pnl = df.at[0, "realized_pnl_usd"]
    win_rate = df.at[0, "win_rate"]
    roi_percent = df.at[0, "realized_pnl_percent"]
    

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Realized PnL", value=f"${realized_pnl:,.2f}")
    with col2:
        st.metric(label="Win Rate", value=f"{win_rate:.1f}%")
    with col3:
        st.metric(label="Avg ROI", value=f"{roi_percent:.2f}%")