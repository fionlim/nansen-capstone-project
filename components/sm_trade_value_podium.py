import streamlit as st
from typing import Dict
import plotly.graph_objects as go
from nansen_client import NansenClient
from dataframes import dex_trades_to_dataframe

def render_dex_trades_podium(payload: Dict):
    try:
        client = NansenClient()
        items = client.smart_money_dex_trades(payload=payload, fetch_all=False)
        df = dex_trades_to_dataframe(items)
        if df.empty:
            st.warning("No DEX trades data returned for the selected filters.")
            return
        excluded_stablecoins = {"USDT", "USDC", "DAI", 
                                "DUSD", "TUSD", "BUSD", 
                                "USDP", "GUSD"}
        excluded_native_tokens = {"ARB", "AVAX", "ETH", 
                                  "BERA", "BLAST", "BNB", 
                                  "HYPE", "IOTA",
                                  "MNT", "MATIC", "RON", 
                                  "SEI", "SONIC", "UNI", 
                                  "SOL", "BASE", "WETH", 
                                  "WBTC", "WSOL", "WEETH"}
        df = df[~df["token_bought_symbol"].isin(excluded_stablecoins)]        
        df = df[~df["token_bought_symbol"].isin(excluded_native_tokens)]

        podium_df = (
            df.groupby(["token_bought_symbol", "token_bought_address"])
            .agg({"trade_value_usd": "sum", "chain": lambda x: ", ".join(sorted(set(x)))})
            .reset_index()
            .sort_values("trade_value_usd", ascending=False)
            .head(3)
        )
        
        podium_df = podium_df.reset_index(drop=True)
        if len(podium_df) >= 3:
            podium_df = podium_df.iloc[[1, 0, 2]].reset_index(drop=True)
        elif len(podium_df) == 2:
            podium_df = podium_df.iloc[[1, 0]].reset_index(drop=True)

        podium_df["label"] = podium_df.apply(
            lambda r: f"<b>{r['token_bought_symbol']}</b> ({r['chain']}) <br> <b>${r['trade_value_usd']:,.0f}</b>", axis=1
        )

        colors = ["#C0C0C0", "#FFD700", "#CD7F32"][:len(podium_df)]
        medals = ["🥈", "🥇", "🥉"][:len(podium_df)]
        if len(podium_df) == 1:
            colors = ["#FFD700"]
            medals = ["🥇"]

        fig = go.Figure(
            go.Bar(
                x=podium_df["label"],
                y=podium_df["trade_value_usd"],
                marker_color=colors,
                hovertemplate="<b>%{x}</b><br><extra></extra>",
                customdata=podium_df["token_bought_address"],
            )
        )

        for i, medal in enumerate(medals):
            fig.add_annotation(
                x=podium_df["label"].iloc[i],
                y=podium_df["trade_value_usd"].iloc[i] + podium_df["trade_value_usd"].max()*0.1,
                text=medal,
                showarrow=False,
                font=dict(size=40),
        )

        fig.update_layout(
            template="plotly_dark",
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            height=420,
            margin=dict(t=20, b=0),
            showlegend=False,
        )

        st.plotly_chart(fig, use_container_width=True)    
  
        cols = st.columns(len(podium_df))
        for i, col in enumerate(cols):
            token_symbol = podium_df.iloc[i]["token_bought_symbol"]
            token_address = podium_df.iloc[i]["token_bought_address"]
            trade_value = podium_df.iloc[i]["trade_value_usd"]
            chain = podium_df.iloc[i]["chain"]
            with col:
                if st.button(f"{token_symbol}({chain})\n${trade_value:,.0f}", 
                             key=token_address, use_container_width=True):
                    st.session_state["selected_token"] = token_address
                    st.session_state["chain"] = chain
                    st.switch_page("pages/2_TGM_Dashboard.py")

        '''
        max_height = podium_df["trade_value_usd"].max()
        podium_df["bar_height"] = (podium_df["trade_value_usd"] / max_height * 150).astype(int)

        gold_height = podium_df.iloc[0]['bar_height']
        gold_medal_top = -20 if gold_height >= 20 else -45

        if len(podium_df) > 1:
            silver_height = podium_df.iloc[1]['bar_height']
            silver_medal_top = -20 if silver_height >= 20 else -45

        if len(podium_df) > 2:
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
                        <div class="podium-label">{podium_df.iloc[1]['token_bought_symbol']} ({podium_df.iloc[1]['chain']})</div>
                        <div class="podium-value">${round(podium_df.iloc[1]['trade_value_usd']):,} USD</div>
                    </div>
                    <div class="podium-bar gold">
                        <div class="medal" style="top: {gold_medal_top}px;">🥇</div>
                        <div class="bar" style="height:{podium_df.iloc[0]['bar_height']}px; background:#FFD700;"></div>
                        <div class="podium-label">{podium_df.iloc[0]['token_bought_symbol']} ({podium_df.iloc[0]['chain']})</div>
                        <div class="podium-value">${round(podium_df.iloc[0]['trade_value_usd']):,} USD</div>
                    </div>
                    <div class="podium-bar bronze">
                        <div class="medal" style="top: {bronze_medal_top}px;">🥉</div>
                        <div class="bar" style="height:{podium_df.iloc[2]['bar_height']}px; background:#CD7F32;"></div>
                        <div class="podium-label">{podium_df.iloc[2]['token_bought_symbol']} ({podium_df.iloc[2]['chain']})</div>
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
                        <div class="podium-label">{podium_df.iloc[1]['token_bought_symbol']} ({podium_df.iloc[1]['chain']})</div>
                        <div class="podium-value">${round(podium_df.iloc[1]['trade_value_usd']):,} USD</div>
                    </div>
                    <div class="podium-bar gold">
                        <div class="medal" style="top: {gold_medal_top}px;">🥇</div>
                        <div class="bar" style="height:{podium_df.iloc[0]['bar_height']}px; background:#FFD700;"></div>
                        <div class="podium-label">{podium_df.iloc[0]['token_bought_symbol']} ({podium_df.iloc[0]['chain']})</div>
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
                        <div class="podium-label">{podium_df.iloc[0]['token_bought_symbol']} ({podium_df.iloc[0]['chain']})</div>
                        <div class="podium-value">${round(podium_df.iloc[0]['trade_value_usd']):,} USD</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        '''
    except Exception as e:
        st.error(f"Unexpected error: {e}")