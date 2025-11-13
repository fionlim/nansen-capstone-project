import streamlit as st
from typing import Dict, List, Tuple
import pandas as pd
from datetime import datetime, timezone, timedelta
from nansen_client import NansenClient
from dataframes import pfl_transactions_to_dataframe, tgm_token_screener_to_dataframe, format_small_price

@st.cache_data(ttl=300)
def fetch_transactions(_client, wallet, from_iso, to_iso):
    transaction_payload = {
        "address": wallet,
        "chain": "ethereum",
        "date": {"from": from_iso,
                "to": to_iso},
        "hide_spam_token": True,
        "order_by": [{"field": "block_timestamp", "direction": "DESC"}],
        "pagination": {"page": 1, "per_page": 20},
    }

    transaction_items = _client.profiler_address_transactions(payload=transaction_payload)
    transaction_df = pfl_transactions_to_dataframe(transaction_items)

    return transaction_df

@st.cache_data(ttl=300)
def fetch_token_screener(_client, chain, from_iso, to_iso, token_address):
    token_payload = {
        "chains": [chain],
        "date": {"from": from_iso, "to":to_iso},
        "filters": {"token_address": token_address},
        "pagination": {"page": 1, "per_page": 1},
    }
    token_items = _client.tgm_token_screener(payload=token_payload)
    token_df = tgm_token_screener_to_dataframe(token_items)

    return token_df

@st.cache_data(ttl=300)
def fetch_current_balance(_client, chain, wallet, token_address):
    balance_payload = {
        "chain": chain,
        "address": wallet,
        "filters": {"token_address": token_address},
        "pagination": {"page": 1, "recordsPerPage": 1},
    }
    balance_items = _client.profiler_address_current_balance(balance_payload)
    balance_df = pd.DataFrame(balance_items)

    return balance_df


@st.fragment
def render_wallet_token_tracker(wallets: List): 
    try:
        if not wallets:
            st.warning("No starred wallets.")
            return

        with st.spinner("Fetching starred wallet token purchases..."):
            client = NansenClient()
            starred_wallets = wallets

            eth_swap_in_methods = ["swapExactTokensForTokens", "swapTokensForExactTokens",
                                "swapExactETHForTokens", "swapETHForExactTokens",
                                "swapExactTokensForTokensSupportingFeeOnTransferTokens",
                                "swapExactETHForTokensSupportingFeeOnTransferTokens",
                                ]
            eth_swap_out_methods = ["swapTokensForExactETH", "swapExactTokensForETH",                                
                                    "swapExactTokensForETHSupportingFeeOnTransferTokens"
            ]

            to_time = datetime.now(timezone.utc)
            from_time = to_time - timedelta(hours=48)
            from_iso = from_time.isoformat().replace("+00:00", "Z")
            to_iso = to_time.isoformat().replace("+00:00", "Z")
            token_tx_map: Dict[Tuple[str, str], Dict[Tuple[str, str], List[Dict]]] = {}

            for wallet in starred_wallets:
                transaction_df = fetch_transactions(client, wallet, from_iso, to_iso)
                if transaction_df.empty:
                    st.warning("No net flow data returned for the selected filters.")
                    return
            
                transaction_df["method"] = transaction_df["method"].apply(
                    lambda m: m.split("(")[0]
                )
                swap_in_df = transaction_df[transaction_df["method"].isin(eth_swap_in_methods)].copy()
                swap_out_df = transaction_df[transaction_df["method"].isin(eth_swap_out_methods)].copy()

                for _, row in swap_in_df.iterrows():
                    tokens_received = row.get("tokens_received", [])
                    for token in tokens_received:
                        token_address = token.get("token_address")
                        token_chain = token.get("chain")
                        if not token_address or not token_chain:
                            continue
                        token_key = (token_address, token_chain)
                        wallet_label = token.get("to_address_label", "")
                        wallet_key = (wallet, wallet_label)
                        token_tx_map.setdefault(token_key, {}).setdefault(wallet_key, []).append({
                            "token_symbol": token.get("token_symbol", ""),
                            "token_amount": token.get("token_amount"),
                            "block_timestamp": row["block_timestamp"],
                            "transaction_hash": row["transaction_hash"],
                            "transaction_type": "receive"
                        })

                for _, row in swap_out_df.iterrows():
                    tokens_sent = row.get("tokens_sent", [])
                    for token in tokens_sent:
                        token_address = token.get("token_address")
                        token_chain = token.get("chain")
                        if not token_address or not token_chain:
                            continue
                        token_key = (token_address, token_chain)
                        wallet_label = token.get("from_address_label", "")
                        wallet_key = (wallet, wallet_label)
                        token_tx_map.setdefault(token_key, {}).setdefault(wallet_key, []).append({
                            "token_symbol": token.get("token_symbol", ""),
                            "token_amount": token.get("token_amount"),
                            "block_timestamp": row["block_timestamp"],
                            "transaction_hash": row["transaction_hash"],
                            "transaction_type": "sent"
                        })
            
            if not token_tx_map:
                st.warning("No relevant transactions found for the starred wallets in the last 24 hours.")
                return

            token_cards = []
            token_symbols_map = {}
            wallet_labels_map = {}

            for (token_address, chain), wallet_map in token_tx_map.items():
                token_df = fetch_token_screener(client, chain, from_iso, to_iso, token_address)

                # WARN: For now, check if token_symbol is empty to detect shitcoin that Nansen does not have data on 
                if token_df.empty or token_df.iloc[0].get("token_symbol") == '':
                    st.warning("No net flow data returned for the selected filters.")
                    return
                
                token_row = token_df.iloc[0]
                token_symbol = token_row.get("token_symbol", "Unknown")
                token_price_str = token_row.get("price_usd", "0").replace("$", "").replace(",", "")
                token_price = float(token_price_str) if token_price_str else 0.0
                market_cap = token_row.get("market_cap_usd", "N/A")
                volume_24h = token_row.get("volume", "N/A")

                token_symbols_map[token_symbol] = (token_address, chain)

                wallet_sections = ""
                for (wallet, wallet_label), tx_list in wallet_map.items():
                    wallet_display = f"{wallet[:20]}..."

                    if wallet_label not in wallet_labels_map:
                        wallet_labels_map[wallet_label] = wallet 

                    balance_df = fetch_current_balance(client, chain, wallet, token_address)
                    
                    token_balance_value = balance_df["value_usd"].iloc[0] if not balance_df.empty else 0

                    tx_count_received = sum(1 for tx in tx_list if tx["transaction_type"] == "receive")
                    tx_count_sent = sum(1 for tx in tx_list if tx["transaction_type"] == "sent")

                    latest_tx = max(tx_list, key=lambda x: x["block_timestamp"])
                    latest_tx_amount = latest_tx["token_amount"]
                    latest_tx_value_usd = latest_tx_amount * token_price

                    total_received = sum(tx["token_amount"] for tx in tx_list if tx["transaction_type"] == "receive")
                    total_sent = sum(abs(tx["token_amount"]) for tx in tx_list if tx["transaction_type"] == "sent")
                    netflow = (total_received - total_sent) * token_price

                    latest_tx_time = max(tx["block_timestamp"] for tx in tx_list if tx["block_timestamp"] is not None)
                    if latest_tx_time.tzinfo is None:
                        latest_tx_time = latest_tx_time.replace(tzinfo=timezone.utc)
                    age_mins = int((datetime.now(timezone.utc) - latest_tx_time).total_seconds() / 60)
                    if age_mins < 60:
                        age_display = f"{age_mins} mins ago"
                    else:
                        age_hours = round(age_mins / 60, 1)
                        age_display = f"{age_hours} hrs ago"


                    wallet_sections += f"""
                    <div style="font-size:0.9rem; color:#CCC; margin-top:6px;">
                        <b>{wallet_display}</b> ({wallet_label})<br>
                        💰 ${token_balance_value:,.2f} | 
                        🔄 {tx_count_received} in / {tx_count_sent} out | 
                        💸 Latest Tx: ${latest_tx_value_usd:,.2f} | 
                        📊 Netflow: ${netflow:,.2f} | 
                        ⏱️ {age_display}
                    </div>
                    """

                token_card_html = f"""
                    <div style="
                        flex: 1 1 calc(50% - 12px);
                        background-color:#1E1E1E;
                        border-radius:16px;
                        padding:20px;
                        margin:6px;
                        box-shadow:0px 2px 6px rgba(0,0,0,0.2);
                        ">
                        <h3 style="margin:0 0 6px 0;">{token_symbol} ({chain})</h3>
                        <div style="font-size:0.95rem; color:#EEE;">
                            💲 <b>Price:</b> {format_small_price(token_price)} &nbsp; 
                            🏦 <b>Market Cap:</b> {market_cap} &nbsp; 
                            📈 <b>Vol (24h):</b> {volume_24h}
                        </div>
                        <hr style="border:0.5px solid #444; margin:10px 0;">
                        {wallet_sections}
                    </div>
                """
                token_cards.append(token_card_html)

            col1, col2, col3, col4 = st.columns([2, 1, 2, 1])
            with col1:
                selected_token = st.selectbox("Select a token", list(token_symbols_map.keys()), index=0, label_visibility="hidden", key="tracker_token")
            
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Get Metrics", use_container_width=True, key="tracker_token_button"):
                    token_address, chain = token_symbols_map[selected_token]
                    st.session_state["token"] = token_address
                    st.session_state["chain"] = chain
                    st.switch_page("pages/2_TGM_Dashboard.py")

            with col3:
                selected_wallet_label = st.selectbox("Select a wallet", list(wallet_labels_map.keys()), index=0, label_visibility="hidden", key="tracker_wallet")
            
            with col4:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Go to Profiler", use_container_width=True, key="tracker_wallet_button"):
                    wallet = wallet_labels_map[selected_wallet_label]
                    st.session_state["wallet"] = wallet
                    st.session_state["label"] = selected_wallet_label
                    st.switch_page("pages/3_Profiler_Dashboard.py")

            st.markdown(
                f"""
                    <div style="display:flex; flex-wrap:wrap; justify-content:space-between;">
                        {''.join(token_cards)}
                    </div>
                """,
                unsafe_allow_html=True,
            )
        
    except Exception as e:
        st.error(f"Unexpected error: {e}")