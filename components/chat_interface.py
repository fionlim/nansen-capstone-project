import streamlit as st
import streamlit_openai

def initialize_chat(openai_api_key: str, nansen_mcp_url: str, nansen_api_key: str):
    """
    Initialize the chat with Nansen MCP.

    Args:
        openai_api_key: OpenAI API key
        nansen_mcp_url: Nansen MCP server URL
        nansen_api_key: Nansen API key

    Returns:
        bool: True if initialization succeeded, False otherwise
    """
    if "chat" in st.session_state:
        return True

    try:
        nansen_mcp = streamlit_openai.RemoteMCP(
            server_label="nansen-mcp",
            server_url=nansen_mcp_url,
            headers={"NANSEN-API-KEY": nansen_api_key},
        )

        st.session_state.chat = streamlit_openai.Chat(
            api_key=openai_api_key,
            model="gpt-4o-mini",
            mcps=[nansen_mcp],
        )

        return True

    except Exception as e:
        st.error(f"Failed to initialize chat: {str(e)}")
        return False