import streamlit as st

from components.chat_interface import initialize_chat, run_chat
from components.chat_network_indicator import render_network_indicator

# Get secrets
OPENAI_API_KEY = st.secrets.get("openai_api_key", "")
NANSEN_MCP_URL = st.secrets.get("nansen_mcp_url", "")
NANSEN_API_KEY = st.secrets.get("nansen_api_key", "")

# Page header
st.title("❇️ Chat with Nansen AI Data")

# Add network indicator
render_network_indicator()

# Initialize chat
if initialize_chat(OPENAI_API_KEY, NANSEN_MCP_URL, NANSEN_API_KEY):
    # Run the chat interface
    run_chat()
else:
    st.error("Failed to initialize chat. Please check your API keys and configuration.")
