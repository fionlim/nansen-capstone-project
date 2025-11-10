import copy
from datetime import datetime, timedelta, timezone
from nansen_client import NansenClient
from dataframes import tgm_dex_trades_to_dataframe
import streamlit as st
import plotly.graph_objects as go


@st.fragment
def render_gauge_charts(token_address: str, chain: str, period: str):
    """
    Fragment that renders two gauge charts:
    1st gauge: % of transactions by smart money
    2nd gauge: % of unique addresses out of the smart money transactions
    
    Stores results in session state instead of returning values.
    """
    
    st.subheader("% of Smart Money Transactions")
    
    # Initialize default values
    total_trades = 0
    smart_trades = 0
    unique_smart_addresses = 0
    gauge_1_value = 0
    gauge_2_value = 0
    has_data = False
    
    # Only fetch data if all inputs are provided
    if token_address and chain and period:
        try:
            # Show loading spinner during data fetch
            with st.spinner("Fetching Smart Money data..."):
                # Period validation
                period_mapping = {
                    "1h": timedelta(hours=1),
                    "24h": timedelta(hours=24),
                    "7d": timedelta(days=7),
                    "30d": timedelta(days=30),
                }
                
                if period not in period_mapping:
                    valid_periods = ", ".join(period_mapping.keys())
                    st.error(f"❌ Invalid period: {period}. Must be one of: {valid_periods}")
                else:
                    # Calculate date range
                    now = datetime.now(timezone.utc)
                    to_datetime = now.strftime("%Y-%m-%dT%H:%M:%SZ")
                    from_datetime = (now - period_mapping[period]).strftime("%Y-%m-%dT%H:%M:%SZ")
                    
                    # Initialize client
                    client = NansenClient()
                    
                    # Prepare payloads
                    payload = {
                        "chain": chain,
                        "token_address": token_address,
                        "date": {"from": from_datetime, "to": to_datetime},
                        "pagination": {"page": 1, "per_page": 1000},
                        "order_by": [{"field": "block_timestamp", "direction": "ASC"}],
                    }
                    
                    smart_payload = copy.deepcopy(payload)
                    smart_payload["only_smart_money"] = True
                    
                    # Fetch data from Nansen API
                    all_dex_trades = client.tgm_dex_trades(payload, fetch_all=True)
                    smart_money_trades = client.tgm_dex_trades(smart_payload, fetch_all=True)
                    
                    # Convert to dataframes
                    df_all = tgm_dex_trades_to_dataframe(all_dex_trades)
                    df_smart = tgm_dex_trades_to_dataframe(smart_money_trades)
                    
                    # Calculate metrics
                    total_trades = len(df_all)
                    smart_trades = len(df_smart)
                    unique_smart_addresses = df_smart["trader_address"].nunique() if len(df_smart) > 0 else 0
                    
                    # Calculate gauge values
                    gauge_1_value = (smart_trades / total_trades * 100) if total_trades > 0 else 0
                    gauge_2_value = (unique_smart_addresses / smart_trades * 100) if smart_trades > 0 else 0
                    has_data = True
        
        except KeyError as e:
            st.error(f"❌ Data format error: Missing expected field {e}")
        
        except ValueError as e:
            st.error(f"❌ Value error: {str(e)}")
        
        except ConnectionError:
            st.error("❌ Connection error: Unable to reach Nansen API. Please check your internet connection.")
        
        except TimeoutError:
            st.error("❌ Request timeout: The API took too long to respond. Please try again.")
        
        except Exception as e:
            st.error(f"❌ Unexpected error occurred: {type(e).__name__}")
            st.caption(f"Details: {str(e)}")
    
    # Helper function for gauge colors
    def get_bar_color(val):
        if val < 25:
            return "#dc2626"  # red
        elif val < 50:
            return "#f59e0b"  # orange
        elif val < 75:
            return "#eab308"  # yellow
        else:
            return "#10b981"  # green
    
    # Always render gauges (empty or with data)
    fig1 = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=gauge_1_value,
            number={"suffix": "%", "font": {"size": 18}, "valueformat": ".2f"},
            gauge={
                "axis": {"visible": False, "range": [0, 100]},
                "bar": {"color": get_bar_color(gauge_1_value) if has_data else "#d1d5db"}  # gray if no data
            },
        )
    )
    fig1.update_layout(height=250, margin=dict(l=10, r=10, t=30, b=20))
    st.plotly_chart(fig1, width='stretch', key="gauge1")
    
    if has_data:
        st.caption(
            f"📊 {smart_trades:,} of {total_trades:,} dex trades in the last {period} were by smart money"
        )
    
    # Second Gauge - only shows if first gauge is not 0
    if gauge_1_value != 0:
        st.subheader("% of Unique Smart Money Wallets")
        fig2 = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=gauge_2_value,
                number={"suffix": "%", "font": {"size": 18}, "valueformat": ".2f"},
                gauge={
                    "axis": {"visible": False, "range": [0, 100]},
                    "bar": {"color": get_bar_color(gauge_2_value) if has_data else "#d1d5db"}  # gray if no data
                },
            )
        )
        fig2.update_layout(height=250, margin=dict(l=10, r=10, t=30, b=20))
        st.plotly_chart(fig2, width='stretch', key="gauge2")
        
        if has_data:
            st.caption(
                f"🏛️ {unique_smart_addresses:,} unique addresses in {smart_trades:,} smart money trades"
            )
    
    st.session_state.gauge_data = {
        "smart_money_percentage": round(gauge_1_value, 2),
        "total_transactions": total_trades,
        "smart_money_transactions": smart_trades,
        "unique_smart_addresses": unique_smart_addresses,
        "period": period,
        "token_address": token_address,
        "chain": chain,
        "has_data": has_data,
    }
