import streamlit as st
from openai import OpenAI
from typing import Dict, Any, Optional
import json


def prepare_summary_data() -> Optional[Dict[str, Any]]:
    """
    Collect and prepare all summarized data from session state for LLM summarization.
    Returns None if insufficient data is available.
    """
    summary_data = {
        "token_info": {
            "address": st.session_state.get("token", ""),
            "chain": st.session_state.get("chain", ""),
            "period": st.session_state.get("period", "")
        }
    }
    
    # Smart Money Metrics (from gauge charts)
    gauge_data = st.session_state.get("gauge_data")
    if gauge_data and gauge_data.get("has_data"):
        summary_data["smart_money_metrics"] = {
            "smart_money_percentage": gauge_data.get("smart_money_percentage", 0),
            "total_transactions": gauge_data.get("total_transactions", 0),
            "smart_money_transactions": gauge_data.get("smart_money_transactions", 0),
            "unique_smart_addresses": gauge_data.get("unique_smart_addresses", 0),
            "period": gauge_data.get("period", "")
        }
    
    # Token Metrics
    token_metrics = st.session_state.get("tgm_token_metrics_summary")
    if token_metrics:
        summary_data["token_metrics"] = token_metrics
    
    # Holder Distribution
    holder_dist = st.session_state.get("tgm_holders_summary")
    if holder_dist:
        summary_data["holder_distribution"] = holder_dist
    
    # Holder Flows
    holder_flows = st.session_state.get("tgm_holder_flows_summary")
    if holder_flows:
        summary_data["holder_flows"] = holder_flows
    
    # PnL Leaderboard
    pnl_data = st.session_state.get("tgm_pnl_summary")
    if pnl_data:
        summary_data["pnl_leaderboard"] = pnl_data
    
    # DEX Trading Activity
    dex_trades = st.session_state.get("tgm_dex_trades_summary")
    if dex_trades:
        summary_data["dex_trading_activity"] = dex_trades
    
    # Check if we have at least some data
    if len(summary_data) <= 1:  # Only token_info
        return None
    
    return summary_data


def generate_ai_summary(summary_data: Dict[str, Any], openai_client: OpenAI) -> str:
    """
    Generate a natural language summary using OpenAI.
    """
    prompt = f"""You are analyzing a Token Dashboard (TGM) for token {summary_data['token_info']['address'][:10]}... on {summary_data['token_info']['chain']}.

The dashboard contains the following data:

{json.dumps(summary_data, indent=2)}

Generate a concise, insightful summary (2-3 paragraphs) that:
1. Highlights the most important metrics and their values
2. Identifies notable patterns or trends (e.g., smart money activity, holder distribution, PnL performance, trading activity)
3. Provides actionable insights about the token's current state

Write in a clear, professional tone suitable for displaying at the top of a dashboard.
Focus on the most significant findings - don't list every metric. Use natural language and avoid jargon when possible."""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a blockchain data analyst summarizing token insights. Be concise and focus on actionable insights."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=400
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating summary: {str(e)}"


def render_dashboard_summary():
    """
    Component to render AI-generated summary for loaded TGM Dashboard.
    Should be called after all other components have run and stored their data.
    Renders content inside an expander (caller should handle the expander wrapper).
    """
    # Check if we have a token selected
    token = st.session_state.get("token", "")
    if not token:
        st.info("👆 Please enter a token address above and click '🔄 Update Dashboard' to generate an AI summary.")
        return
    
    # Check if OpenAI client is available
    if "openai_client" not in st.session_state:
        # Try to initialize if API key is available
        try:
            openai_api_key = st.secrets.get("openai_api_key", "")
            if openai_api_key:
                st.session_state.openai_client = OpenAI(api_key=openai_api_key)
            else:
                # No API key found
                st.warning("⚠️ OpenAI API key not found. Please add `openai_api_key` to your `secrets.toml` file to enable AI summaries.")
                return
        except Exception as e:
            # Failed to initialize
            st.error(f"❌ Failed to initialize OpenAI client: {str(e)}")
            return
    
    # Create cache key based on token, chain, period
    chain = st.session_state.get("chain", "")
    period = st.session_state.get("period", "")
    cache_key = f"tgm_summary_{token}_{chain}_{period}"
    
    # Check if summary already exists in cache
    if cache_key in st.session_state:
        summary_text = st.session_state[cache_key]
    else:
        # Prepare data and generate summary
        summary_data = prepare_summary_data()
        
        if not summary_data:
            # Data not ready yet - components are still fetching
            st.info("⏳ Preparing summary... Please wait while dashboard data is being fetched.")
            return
        
        # Generate summary
        with st.spinner("🤖 Generating AI summary..."):
            summary_text = generate_ai_summary(summary_data, st.session_state.openai_client)
            st.session_state[cache_key] = summary_text
    
    # Display summary
    if summary_text and not summary_text.startswith("Error"):
        st.text(summary_text)
    elif summary_text and summary_text.startswith("Error"):
        st.error(f"❌ Unable to generate AI summary: {summary_text}")

