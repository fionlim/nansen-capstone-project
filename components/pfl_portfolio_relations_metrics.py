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
        "pagination": {"page": 1, "per_page": 100}
    }
    cp_data = client.profiler_address_counterparties(payload=cp_payload, fetch_all=True)
    rw_data = client.profiler_address_related_wallets(payload=rw_payload, fetch_all=True)
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