import streamlit as st
from typing import Dict, Any, List, Optional

from eth_account import Account
from eth_account.signers.local import LocalAccount

from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from hyperliquid.utils import constants


# ============================================================================
# SETUP/CONNECTION FUNCTIONS
# ============================================================================


def get_hyperliquid_setup():
    """
    Setup Hyperliquid connection using secrets from Streamlit.

    Returns:
        tuple: (address, info, exchange)
    """
    use_mainnet = st.session_state.get("hyperliquid_mainnet", False)
    base_url = (
        constants.MAINNET_API_URL if use_mainnet else constants.TESTNET_API_URL
    )
    print(f"Using base_url: {base_url}")

    secret_key = st.secrets.get("hl", {}).get("secret_key", "").strip()
    if not secret_key:
        raise Exception(
            "No secret_key configured. Please set secret_key in secrets.toml"
        )

    account: LocalAccount = Account.from_key(secret_key)
    address = st.secrets.get("hl", {}).get("account_address", "").strip()
    if not address:
        raise Exception(
            "No account_address configured. Please set account_address in secrets.toml"
        )

    if address.lower() != account.address.lower():
        print("Warning: Running with agent address:", account.address)

    info = Info(base_url=base_url, skip_ws=True, perp_dexs=None)
    exchange = Exchange(account, base_url, account_address=address, perp_dexs=None)

    # Check if account has value (connection test)
    try:
        user_state = info.user_state(address)
        spot_user_state = info.spot_user_state(address)
        margin_summary = user_state.get("marginSummary", {})

        if (
            float(margin_summary.get("accountValue", 0)) == 0
            and len(spot_user_state.get("balances", [])) == 0
        ):
            url = base_url.split(".", 1)[1] if "." in base_url else base_url
            error_string = (
                f"No accountValue:\n"
                f"If you think this is a mistake, make sure that {address} has a balance on {url}.\n"
                f"If address shown is your API wallet address, update the config to specify the address "
                f"of your account, not the address of the API wallet."
            )
            raise Exception(error_string)
    except Exception as e:
        # Re-raise if it's our accountValue check, otherwise let it propagate
        if "No accountValue" in str(e):
            raise
        # If it's a connection error, let it propagate
        raise

    return address, info, exchange


# ============================================================================
# FETCH/QUERY FUNCTIONS
# ============================================================================


def fetch_balances_and_positions() -> Dict[str, Any]:
    """
    Fetch account balances and positions from Hyperliquid.

    Returns:
        dict: Contains margin_summary, positions, and spot_balances
    """
    try:
        address, info, _ = get_hyperliquid_setup()

        user_state = info.user_state(address)
        spot_user_state = info.spot_user_state(address)

        return {
            "status": "success",
            "address": address,
            "user_state": user_state,
            "spot_user_state": spot_user_state,
        }

    except Exception as e:
        print(f"Error fetching balances and positions: {e}")
        return {
            "status": "error",
            "error": str(e),
        }