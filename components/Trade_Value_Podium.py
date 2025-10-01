import json
import requests
import streamlit as st
from dataframes import dex_trades_to_dataframe
from typing import Dict

def render_dex_trades_podium(payload: Dict):
    try:
        BASE_URL = st.secrets["nansen"]["base_url"]
        headers = {"apiKey": st.secrets["nansen"]["apiKey"],
            "Content-Type": "application/json"}
        response = requests.post(f"{BASE_URL}/smart-money/dex-trades", headers=headers, data=json.dumps(payload))
        items = response.json().get("data", [])
        df = dex_trades_to_dataframe(items)
        if df.empty:
            st.warning("No DEX trades data returned for the selected filters.")
            return
        excluded_stablecoins = {"USDT", "USDC", "DAI", 
                                "DUSD", "TUSD", "BUSD", 
                                "FRAX", "USDP", "GUSD"}
        excluded_native_tokens = {"ARB", "AVAX", "ETH", 
                                  "BERA", "BLAST", "BNB", 
                                  "GOAT", "HYPER", "IOTA",
                                  "MNT", "MATIC", "RON", 
                                  "SEI", "SONIC", "UNI", 
                                  "SOL", "BASE", "WETH", 
                                  "WBTC", "WSOL", "WEETH"}
        df = df[~df["token_bought_symbol"].isin(excluded_stablecoins)]        
        df = df[~df["token_bought_symbol"].isin(excluded_native_tokens)]
        podium_df = (
            df.groupby("token_bought_symbol")
            .agg({"trade_value_usd": "sum"})
            .reset_index()
            .sort_values("trade_value_usd", ascending=False)
            .head(3)
        )
        
        max_height = podium_df["trade_value_usd"].max()
        podium_df["bar_height"] = (podium_df["trade_value_usd"] / max_height * 150).astype(int)

        gold_height = podium_df.iloc[0]['bar_height']
        gold_medal_top = -20 if gold_height >= 20 else -45

        silver_height = podium_df.iloc[1]['bar_height']
        silver_medal_top = -20 if silver_height >= 20 else -45

        bronze_height = podium_df.iloc[2]['bar_height']
        bronze_medal_top = -20 if bronze_height >= 20 else -45

        st.markdown(
            """
            <style>
                .podium-container {
                    display: flex;
                    justify-content: center;
                    align-items: flex-end;
                    height: 220px;
                    margin-bottom: 20px;
                }
                .podium-bar {
                    flex: 1;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    margin: 0 20px;
                    position: relative;
                }
                .podium-bar .medal {
                    position: absolute;
                    top: -20px;
                    left: 50%;
                    transform: translateX(-50%);
                    font-size: 40px;
                }
                .bar {
                    width: 60px;
                    border-radius: 10px 10px 0 0;
                    margin-bottom: 10px;
                }
                .podium-label, .podium-value {
                    text-align: center;
                    width: 100%;
                }
                .podium-value {
                    font-weight: bold;
                }
            </style>
            """, unsafe_allow_html=True
        )


        if podium_df.empty:
            st.warning("No tokens available for podium display.")
            return
        
        elif len(podium_df) == 3:
            st.markdown(
                f"""
                <div class="podium-container">
                    <div class="podium-bar silver">
                        <div class="medal" style="top: {silver_medal_top}px;">🥈</div>
                        <div class="bar" style="height:{podium_df.iloc[1]['bar_height']}px; background:#C0C0C0;"></div>
                        <div class="podium-label">{podium_df.iloc[1]['token_bought_symbol']}</div>
                        <div class="podium-value">${round(podium_df.iloc[1]['trade_value_usd']):,} USD</div>
                    </div>
                    <div class="podium-bar gold">
                        <div class="medal" style="top: {gold_medal_top}px;">🥇</div>
                        <div class="bar" style="height:{podium_df.iloc[0]['bar_height']}px; background:#FFD700;"></div>
                        <div class="podium-label">{podium_df.iloc[0]['token_bought_symbol']}</div>
                        <div class="podium-value">${round(podium_df.iloc[0]['trade_value_usd']):,} USD</div>
                    </div>
                    <div class="podium-bar bronze">
                        <div class="medal" style="top: {bronze_medal_top}px;">🥉</div>
                        <div class="bar" style="height:{podium_df.iloc[2]['bar_height']}px; background:#CD7F32;"></div>
                        <div class="podium-label">{podium_df.iloc[2]['token_bought_symbol']}</div>
                        <div class="podium-value">${round(podium_df.iloc[2]['trade_value_usd']):,} USD</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        elif len(podium_df) == 2:
            st.markdown(
                f"""
                <div class="podium-container">
                    <div class="podium-bar silver">
                        <div class="medal" style="top: {silver_medal_top}px;">🥈</div>
                        <div class="bar" style="height:{podium_df.iloc[1]['bar_height']}px; background:#C0C0C0;"></div>
                        <div class="podium-label">{podium_df.iloc[1]['token_bought_symbol']}</div>
                        <div class="podium-value">${round(podium_df.iloc[1]['trade_value_usd']):,} USD</div>
                    </div>
                    <div class="podium-bar gold">
                        <div class="medal" style="top: {gold_medal_top}px;">🥇</div>
                        <div class="bar" style="height:{podium_df.iloc[0]['bar_height']}px; background:#FFD700;"></div>
                        <div class="podium-label">{podium_df.iloc[0]['token_bought_symbol']}</div>
                        <div class="podium-value">${round(podium_df.iloc[0]['trade_value_usd']):,} USD</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        else:
            st.markdown(
                f"""
                <div class="podium-container">
                    <div class="podium-bar gold">
                        <div class="medal" style="top: {gold_medal_top}px;">🥇</div>
                        <div class="bar" style="height:{podium_df.iloc[0]['bar_height']}px; background:#FFD700;"></div>
                        <div class="podium-label">{podium_df.iloc[0]['token_bought_symbol']}</div>
                        <div class="podium-value">${round(podium_df.iloc[0]['trade_value_usd']):,} USD</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
    except Exception as e:
        st.error(f"Unexpected error: {e}")