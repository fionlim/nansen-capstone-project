import streamlit as st
from dataframes import counterparties_to_dataframe, related_wallets_to_dataframe

@st.cache_data(ttl=300)
def fetch_counterparties(_client, wallet, chain_all, from_iso, to_iso):
    cp_payload = {
        "address": wallet,
        "chain": chain_all,
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

    items = _client.profiler_address_counterparties(payload=cp_payload, fetch_all=True)
    df = counterparties_to_dataframe(items)
    
    return df

@st.cache_data(ttl=300)
def fetch_related_wallets(_client, wallet, chain_tx):
    rw_payload = {
        "address": wallet,
        "chain": chain_tx,
        "pagination": {"page": 1, "per_page": 100}
    }

    items = _client.profiler_address_related_wallets(payload=rw_payload, fetch_all=True)
    df = counterparties_to_dataframe(items)
    
    return df

def render_portfolio_relations_metrics(client, wallet, chain_all, chain_tx, from_iso, to_iso):
    cp_df = fetch_counterparties(client, wallet, chain_all, from_iso, to_iso)
    rw_df = fetch_related_wallets(client, wallet, chain_tx)
    if cp_df.empty:
        st.warning("No counterparty data found.")
        return
    if rw_df.empty:
        st.warning("No related wallet data found.")

    num_cp = cp_df["counterparty_address"].nunique()
    num_rw = rw_df["address"].nunique()

    top_cp_share = 0
    if not cp_df.empty and "total_volume_usd" in cp_df.columns:
        total_vol = cp_df["total_volume_usd"].sum()
        top_cp_share = (cp_df["total_volume_usd"].max() / total_vol * 100) if total_vol > 0 else 0

    top_rw_share = 0
    if not rw_df.empty:
        # count interactions per wallet
        rw_counts = rw_df.groupby("address").size()
        top_rw_share = (rw_counts.max() / rw_counts.sum() * 100) if rw_counts.sum() > 0 else 0


    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Number of Unique Counterparties", value=num_cp)
    with col2:
        st.metric(label="Top Counterparty Share %", value=f"{top_cp_share:.2f}%")
    with col3:
        st.metric(label="Number of Unique Related Wallets", value=num_rw)
    with col4:
        st.metric(label="Top Related Wallet Share %", value=f"{top_rw_share:.2f}%")