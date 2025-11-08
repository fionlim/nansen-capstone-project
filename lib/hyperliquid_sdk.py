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


def get_available_trading_pairs() -> Dict[str, Any]:
    """
    Get all available trading pairs (perpetuals and spot) from Hyperliquid.

    Returns:
        dict: Combined list of trading pairs with type field
    """
    try:
        _, info, _ = get_hyperliquid_setup()

        trading_pairs = []

        # Get perpetual coins
        perp_meta = info.meta(dex="")
        for asset_info in perp_meta.get("universe", []):
            trading_pairs.append(
                {
                    "name": asset_info.get("name", ""),
                    "type": "perp",
                    "sz_decimals": asset_info.get("szDecimals", 0),
                    "max_leverage": asset_info.get("maxLeverage"),
                    "only_isolated": asset_info.get("onlyIsolated", False),
                }
            )

        # Get spot trading pairs
        spot_meta = info.spot_meta()
        tokens_dict = spot_meta.get("tokens", {})
        # Handle both dict and list format for tokens
        if isinstance(tokens_dict, list):
            tokens_dict = {str(i): token for i, token in enumerate(tokens_dict)}
        for spot_info in spot_meta.get("universe", []):
            base_idx, quote_idx = spot_info.get("tokens", [0, 0])
            base_token = tokens_dict.get(str(base_idx), {}) or {}
            quote_token = tokens_dict.get(str(quote_idx), {}) or {}

            # Build display name like "ETH/USDC"
            display_name = (
                f'{base_token.get("name", "")}/{quote_token.get("name", "")}'
                if base_token.get("name") and quote_token.get("name")
                else spot_info.get("name", "")
            )

            trading_pairs.append(
                {
                    "name": spot_info.get("name", ""),
                    "display_name": display_name,
                    "type": "spot",
                    "base_token": base_token.get("name", ""),
                    "quote_token": quote_token.get("name", ""),
                    "sz_decimals": base_token.get("szDecimals", 0),
                    "is_canonical": spot_info.get("isCanonical", False),
                }
            )

        return {
            "status": "success",
            "trading_pairs": trading_pairs,
            "total_perp": sum(1 for p in trading_pairs if p["type"] == "perp"),
            "total_spot": sum(1 for p in trading_pairs if p["type"] == "spot"),
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


def get_leverage(coin: str) -> Dict[str, Any]:
    """
    Get the current leverage for a specific coin, only works if there is an open position.

    Args:
        coin: Trading pair (e.g., "ETH", "BTC")

    Returns:
        dict: Leverage information (type, value, display, raw_usd) of open position of the coin
    """
    try:
        address, info, _ = get_hyperliquid_setup()

        user_state = info.user_state(address)

        # Find position for the specified coin
        for asset_position in user_state.get("assetPositions", []):
            position = asset_position.get("position", {})
            if position.get("coin") == coin:
                leverage_info = position.get("leverage", {})
                leverage_type = leverage_info.get("type", "cross")
                leverage_value = leverage_info.get("value", 0)
                raw_usd = leverage_info.get("rawUsd")  # Only for isolated

                return {
                    "status": "success",
                    "coin": coin,
                    "leverage": {
                        "type": leverage_type,
                        "value": leverage_value,
                        "display": f"{leverage_value}x",
                        "raw_usd": float(raw_usd) if raw_usd is not None else None,
                    },
                    "position_size": float(position.get("szi", 0)),
                    "margin_used": float(position.get("marginUsed", 0)),
                }

        # No position found for this coin
        return {
            "status": "error",
            "error": f"No open position found for {coin}",
            "coin": coin,
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "coin": coin,
        }


def place_limit_order(
    coin: str,
    is_buy: bool,
    sz: float,
    limit_px: float,
    time_in_force: str = "Gtc",
    leverage: Optional[int] = None,
    is_cross: bool = True,
) -> Dict[str, Any]:
    """
    Place a limit order on Hyperliquid.

    Args:
        coin: Trading pair (e.g., "ETH", "BTC")
        is_buy: True for buy, False for sell
        sz: Size of the order
        limit_px: Limit price
        time_in_force: Order time in force ("Gtc", "Ioc", "Alo")
        leverage: Optional leverage value to set before placing order (e.g., 10 for 10x)
        is_cross: If True, use cross margin, else isolated margin (only used if leverage is set)

    Returns:
        dict: Order result with status and order details
    """
    try:
        address, info, exchange = get_hyperliquid_setup()

        # Set leverage if specified
        leverage_result = None
        if leverage is not None:
            leverage_result = exchange.update_leverage(leverage, coin, is_cross)
            if leverage_result.get("status") != "ok":
                return {
                    "status": "error",
                    "error": f"Failed to set leverage: {leverage_result}",
                    "leverage_result": leverage_result,
                }

        # Place limit order
        order_result = exchange.order(
            coin, is_buy, sz, limit_px, {"limit": {"tif": time_in_force}}
        )

        result = {
            "status": order_result.get("status", "unknown"),
            "order_result": order_result,
        }

        # Include leverage result if it was set
        if leverage_result is not None:
            result["leverage_set"] = True
            result["leverage_result"] = leverage_result

        # If order was placed successfully, extract order ID
        if order_result.get("status") == "ok":
            statuses = (
                order_result.get("response", {}).get("data", {}).get("statuses", [])
            )
            if statuses:
                status = statuses[0]
                if "resting" in status:
                    result["order_id"] = status["resting"]["oid"]
                    result["resting"] = True
                elif "filled" in status:
                    result["filled"] = True
                elif "error" in status:
                    result["error"] = status["error"]

        return result
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }