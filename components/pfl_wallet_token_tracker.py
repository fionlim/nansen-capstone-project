import streamlit as st
from typing import Dict
from nansen_client import NansenClient
from dataframes import pfl_transactions_to_dataframe


def render_wallet_token_tracker(payload: Dict):

    try:
        payload = {
            "address": "0x28c6c06298d514db089934071355e5743bf21d60",
            "chain": "ethereum",
            "date": {"from": "2025-08-01T00:00:00Z", "to": "2025-08-10T23:59:59Z"},
            "hide_spam_token": True,
            "order_by": [{"field": "block_timestamp", "direction": "DESC"}],
            "pagination": {"page": 1, "per_page": 20},
        }
        client = NansenClient()
        items = client.profiler_address_transactions(payload, fetch_all=False)
        df = pfl_transactions_to_dataframe(items)
        if df.empty:
            st.warning("No net flow data returned for the selected filters.")
            return
        
        df = df[df["method"] == "transfer(address,uint256)"].reset_index(drop=True)

        #for _, row in df.iterate 

    except Exception as e:
        st.error(f"Unexpected error: {e}")