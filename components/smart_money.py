from typing import Dict
import streamlit as st

from nansen_client import NansenClient
from dataframes import inflows_to_dataframe, holdings_to_dataframe


def render_smart_money(payload: Dict, new_token_max_days: int):
    client = NansenClient()

    sub_inflows, sub_holdings = st.tabs(["Inflows", "Holdings"])

    with sub_inflows:
        try:
            items = client.smart_money_inflows(payload)
            df = inflows_to_dataframe(items)
            if df.empty:
                st.warning("No inflows data returned for the selected filters.")
            else:
                st.subheader("Most commonly traded tokens by Smart Money (last day)")
                top_traded = df.sort_values("volume24hUSD", ascending=False).head(20)
                st.dataframe(
                    top_traded[[
                        "symbol", "chain", "tokenAddress", "volume24hUSD", "nofTraders", "sectors", "marketCap"
                    ]].rename(columns={
                        "symbol": "Token",
                        "chain": "Chain",
                        "tokenAddress": "Address",
                        "volume24hUSD": "24h Volume (USD)",
                        "nofTraders": "#SM Traders",
                        "sectors": "Sectors",
                        "marketCap": "Market Cap (USD)"
                    }),
                    use_container_width=True
                )
                st.bar_chart(top_traded.set_index("symbol")["volume24hUSD"])

                st.subheader("New tokens significantly adopted by Smart Money")
                new_tokens = df[df["tokenAgeDaysNum"].fillna(1e9) <= new_token_max_days]
                new_tokens = new_tokens.sort_values("volume24hUSD", ascending=False).head(20)
                st.dataframe(
                    new_tokens[[
                        "symbol", "chain", "tokenAddress", "tokenAgeDays", "volume24hUSD", "nofTraders", "sectors", "marketCap"
                    ]].rename(columns={
                        "symbol": "Token",
                        "chain": "Chain",
                        "tokenAddress": "Address",
                        "tokenAgeDays": "Age (days)",
                        "volume24hUSD": "24h Volume (USD)",
                        "nofTraders": "#SM Traders",
                        "sectors": "Sectors",
                        "marketCap": "Market Cap (USD)"
                    }),
                    use_container_width=True
                )
        except Exception as e:
            st.error(f"Unexpected error: {e}")

    with sub_holdings:
        try:
            items_h = client.smart_money_holdings(payload)
            df_h = holdings_to_dataframe(items_h)
            if df_h.empty:
                st.warning("No holdings data returned for the selected filters.")
            else:
                st.subheader("What tokens are Smart Money holding?")
                top_held = df_h.sort_values("balanceUsd", ascending=False).head(50)
                st.dataframe(
                    top_held[[
                        "symbol", "chain", "tokenAddress", "balanceUsd", "balancePctChange24H",
                        "nofHolders", "shareOfHoldings", "sectors", "marketCap"
                    ]].rename(columns={
                        "symbol": "Token",
                        "chain": "Chain",
                        "tokenAddress": "Address",
                        "balanceUsd": "Balance (USD)",
                        "balancePctChange24H": "Balance Change 24h (%)",
                        "nofHolders": "#SM Holders",
                        "shareOfHoldings": "Share of Holdings",
                        "sectors": "Sectors",
                        "marketCap": "Market Cap (USD)"
                    }),
                    use_container_width=True
                )
                st.bar_chart(top_held.set_index("symbol")["balanceUsd"])
        except Exception as e:
            st.error(f"Unexpected error: {e}")
