import streamlit as st
import streamlit_openai

OPENAI_API_KEY = st.secrets.get("openai_api_key", "")
NANSEN_MCP_URL = st.secrets.get("nansen_mcp_url", "")
NANSEN_API_KEY = st.secrets.get("nansen_api_key", "")

if "chat" not in st.session_state:
    nansen_mcp = streamlit_openai.RemoteMCP(
        server_label="nansen-mcp",
        server_url=NANSEN_MCP_URL,
        headers={"NANSEN-API-KEY": NANSEN_API_KEY}
    )
    st.session_state.chat = streamlit_openai.Chat(
        api_key=OPENAI_API_KEY,
        model="gpt-5-nano",
        mcps=[nansen_mcp],
    )

st.title("❇️ Chat with Nansen AI Data")
st.session_state.chat.run()
