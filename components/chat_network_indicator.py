import streamlit as st
from lib.hyperliquid_sdk import get_hyperliquid_setup


def render_network_indicator():
    """Render the network indicator and mainnet toggle."""
    # Initialize mainnet flag
    if "hyperliquid_mainnet" not in st.session_state:
        st.session_state.hyperliquid_mainnet = False

    # Store previous value to detect changes
    prev_mainnet = st.session_state.get("_prev_hyperliquid_mainnet", st.session_state.hyperliquid_mainnet)

    # Check connection
    cache_key = f"_hyperliquid_status_{st.session_state.hyperliquid_mainnet}"
    if cache_key not in st.session_state:
        with st.spinner("Connecting to Hyperliquid..."):
            connection_status = _check_connection()
        st.session_state[cache_key] = connection_status
    else:
        connection_status = st.session_state[cache_key]

    # Render UI
    col1, col2 = st.columns([1, 2])

    with col1:
        # Show connection status
        if connection_status["connected"]:
            network = "Mainnet" if st.session_state.hyperliquid_mainnet else "Testnet"
            status_text = f"✅ {network} Connected"
        else:
            status_text = "❌ Disconnected"
        
        st.markdown(
            f'<div style="padding-top: 0.5rem; line-height: 1.5;">{status_text}</div>',
            unsafe_allow_html=True
        )

    with col2:
        use_mainnet = st.checkbox(
            "Use Hyperliquid Mainnet",
            value=st.session_state.hyperliquid_mainnet,
            help="When enabled, Hyperliquid will use MAINNET.",
            key="hyperliquid_mainnet",
        )

        # Clear cache and rerun if network changed
        if use_mainnet != prev_mainnet:
            # Clear all connection status caches
            for key in list(st.session_state.keys()):
                if key.startswith("_hyperliquid_status_"):
                    del st.session_state[key]
            st.session_state["_prev_hyperliquid_mainnet"] = use_mainnet
            st.rerun()

    # Show error message below the entire row if disconnected
    if not connection_status["connected"] and connection_status.get("error"):
        st.error(f"Connection failed: {connection_status['error']}")


def _check_connection() -> dict:
    """Check if Hyperliquid connection is successful."""
    try:
        get_hyperliquid_setup()
        return {"connected": True}
    except Exception as e:
        return {"connected": False, "error": str(e)}
