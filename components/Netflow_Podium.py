import json
import requests
from typing import Dict
import streamlit as st
from dataframes import net_flow_to_dataframe


def render_netflow_podium(payload: Dict):

    try:
        BASE_URL = st.secrets["NANSEN_BASE_URL"]
        headers = {"apiKey": st.secrets["apiKey"],
            "Content-Type": "application/json"}
        response = requests.post(f"{BASE_URL}/smart-money/netflow", headers=headers, data=json.dumps(payload))
        items = response.json().get("data", [])
        df = net_flow_to_dataframe(items)
        if df.empty:
            st.warning("No net flow data returned for the selected filters.")
            return

        df_positive = df[df["net_flow_24h_usd"] > 0]
        podium_df = (
            df_positive.sort_values("net_flow_24h_usd", ascending=False)
            .head(3)
        )

        max_height = podium_df["net_flow_24h_usd"].max() if not podium_df.empty else 1
        podium_df["bar_height"] = (podium_df["net_flow_24h_usd"] / max_height * 150).astype(int)
        
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
                        <div class="podium-label">{podium_df.iloc[1]['token_symbol']} ({podium_df.iloc[1]['chain']})</div>
                        <div class="podium-value">${round(podium_df.iloc[1]['net_flow_24h_usd']):,} USD</div>
                    </div>
                    <div class="podium-bar gold">
                        <div class="medal" style="top: {gold_medal_top}px;">🥇</div>
                        <div class="bar" style="height:{podium_df.iloc[0]['bar_height']}px; background:#FFD700;"></div>
                        <div class="podium-label">{podium_df.iloc[0]['token_symbol']} ({podium_df.iloc[0]['chain']})</div>
                        <div class="podium-value">${round(podium_df.iloc[0]['net_flow_24h_usd']):,} USD</div>
                    </div>
                    <div class="podium-bar bronze">
                        <div class="medal" style="top: {bronze_medal_top}px;">🥉</div>
                        <div class="bar" style="height:{podium_df.iloc[2]['bar_height']}px; background:#CD7F32;"></div>
                        <div class="podium-label">{podium_df.iloc[2]['token_symbol']} ({podium_df.iloc[2]['chain']})</div>
                        <div class="podium-value">${round(podium_df.iloc[2]['net_flow_24h_usd']):,} USD</div>
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
                        <div class="podium-label">{podium_df.iloc[1]['token_symbol']} ({podium_df.iloc[1]['chain']})</div>
                        <div class="podium-value">${round(podium_df.iloc[1]['net_flow_24h_usd']):,} USD</div>
                    </div>
                    <div class="podium-bar gold">
                        <div class="medal" style="top: {gold_medal_top}px;">🥇</div>
                        <div class="bar" style="height:{podium_df.iloc[0]['bar_height']}px; background:#FFD700;"></div>
                        <div class="podium-label">{podium_df.iloc[0]['token_symbol']} ({podium_df.iloc[0]['chain']})</div>
                        <div class="podium-value">${round(podium_df.iloc[0]['net_flow_24h_usd']):,} USD</div>
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
                        <div class="podium-label">{podium_df.iloc[0]['token_symbol']} ({podium_df.iloc[0]['chain']})</div>
                        <div class="podium-value">${round(podium_df.iloc[0]['net_flow_24h_usd']):,} USD</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
    except Exception as e:
        st.error(f"Unexpected error: {e}")