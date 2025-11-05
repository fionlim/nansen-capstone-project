import streamlit as st
import streamlit.components.v1 as components


@st.fragment
def render_llamaswap_iframe(chain: str, token: str):
    """
    Renders LlamaSwap iframe for token swapping.
    
    Args:
        chain: Blockchain network (ethereum, arbitrum, etc.)
        token: Target token address to swap to
    """
    
    # Default values
    default_chain = "ethereum"
    default_from_token = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48" # USDC on Ethereum
    default_to_token = "0xe0f63a424a4439cbe457d80e4f4b51ad25b2c56c" # SPX on Ethereum
    
    # Use provided values or fallback to defaults
    swap_chain = chain if chain else default_chain
    to_token = token if token else default_to_token
    
    # Build LlamaSwap URL
    llama_swap_url = f"https://swap.defillama.com/?chain={swap_chain}&from={default_from_token}&to={to_token}"
    
    # Center the iframe using columns
    left, mid, right = st.columns([1, 2, 1])
    with mid:
        components.iframe(
            llama_swap_url, 
            width=450, 
            height=750, 
            scrolling=True
        )
