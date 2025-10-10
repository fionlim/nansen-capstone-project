import streamlit as st
from dataframes import counterparties_to_dataframe, related_wallets_to_dataframe

def render_portfolio_relations_metrics(client, wallet, chain_tx, from_iso, to_iso):
    cp_payload = {
        "address": wallet,
        "chain": chain_tx,
        "date": {
            "from": f"{from_iso}", 
            "to": f"{to_iso}"
        },
        "group_by": "wallet",
        "pagination": {
            "page": 1, 
            "per_page": 100
        },
    }
    rw_payload = {
        "address": wallet,
        "chain": chain_tx,
    }
    cp_data = client.profiler_address_counterparties(payload=cp_payload, fetch_all=False, n=1)
    rw_data = client.profiler_address_related_wallets(payload=rw_payload, fetch_all=False, n=1)
    if not cp_data:
        st.warning("No counterparty data found.")
        return
    if not rw_payload:
        st.warning("No related wallet data found.")
        return

    cp_df = counterparties_to_dataframe(cp_data)
    rw_df = related_wallets_to_dataframe(rw_data)
    if cp_df.empty:
        st.warning("No counterparty data found.")
        return
    if rw_df.empty:
        st.warning("No related wallet data found.")

    # TODO: Add logic for Top Counterparty Share %, Top Related Wallet Share %
    num_cp = cp_df["counterparty_address"].nunique()
    num_rw = rw_df["address"].nunique()

    # TODO: Add metric display for Top Counterparty Share %, Top Related Wallet Share %
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Number of Unique Counterparties", value=num_cp)

    with col3:
        st.metric(label="Number of Unique Related Wallets", value=num_rw)