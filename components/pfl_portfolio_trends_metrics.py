import streamlit as st
from dataframes import historical_balances_to_dataframe

def render_portfolio_trends_metrics(client, wallet, chain, from_iso, to_iso):
    """
    Render Top Token Concentration % and 30-Day Portfolio Growth % for a wallet.
    
    Args:
        client: NansenClient instance
        wallet: str, wallet address
        chain: str, chain for portfolio data
        from_iso: str, start datetime ISO string
        to_iso: str, end datetime ISO string
    """
    payload = {
        "address": wallet,
        "chain": chain,
        "date": {
            "from": from_iso,
            "to": to_iso
        },
        "pagination": {
            "page": 1,
            "per_page": 1000
        },
    }

    # Fetch historical balances from Nansen Profiler API
    data = client.profiler_address_historical_balances(payload=payload, fetch_all=True)
    if not data:
        st.warning("No portfolio data found for trend metrics.")
        return

    df = historical_balances_to_dataframe(data)
    if df.empty:
        st.warning("No portfolio data found for trend metrics.")
        return

    # --- Latest snapshot per token ---
    snapshot = df.sort_values("block_timestamp").groupby("token_symbol").last()
    total_value_usd = snapshot["value_usd"].sum()
    top_token_value = snapshot["value_usd"].max() if not snapshot.empty else 0
    top_token_concentration = (top_token_value / total_value_usd * 100) if total_value_usd > 0 else 0

    # --- 30-Day Portfolio Growth ---
    # Sum value across tokens for first and last day
    df_daily = df.groupby("block_timestamp")["value_usd"].sum().reset_index()
    if len(df_daily) >= 2:
        start_val = df_daily.iloc[0]["value_usd"]
        end_val = df_daily.iloc[-1]["value_usd"]
        portfolio_growth_30d = ((end_val - start_val) / start_val * 100) if start_val > 0 else 0
    else:
        portfolio_growth_30d = 0

    # Display metrics in two columns
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Top Token Concentration %", value=f"{top_token_concentration:.2f}%")
    with col2:
        st.metric(label="30D Portfolio Growth %", value=f"{portfolio_growth_30d:.2f}%")
