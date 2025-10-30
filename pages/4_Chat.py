import streamlit as st

from components.chat_interface import initialize_chat

# Get secrets
OPENAI_API_KEY = st.secrets.get("openai_api_key", "")
NANSEN_MCP_URL = st.secrets.get("nansen_mcp_url", "")
NANSEN_API_KEY = st.secrets.get("nansen_api_key", "")

# Initialize chat
initialize_chat(OPENAI_API_KEY, NANSEN_MCP_URL, NANSEN_API_KEY)

# Page header
st.title("❇️ Chat with Nansen AI Data")

# Run the chat
if "chat" in st.session_state:
    st.session_state.chat.run()
