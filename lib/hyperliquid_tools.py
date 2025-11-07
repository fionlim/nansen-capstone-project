from typing import Dict, Any, Optional, List, Tuple, Callable

from lib.hyperliquid_sdk import (
    fetch_balances_and_positions,
    get_available_trading_pairs,
    get_leverage,
)


def get_hyperliquid_tools() -> Tuple[List[Dict[str, Any]], Dict[str, Callable]]:
    """
    Get Hyperliquid tools in OpenAI function calling format.
    
    Returns:
        tuple: (tools_list, handler_registry)
            - tools_list: List of tools in OpenAI format
            - handler_registry: Dict mapping function names to handler functions
    """

    tools = [

        # ============================================================================
        # FETCH/QUERY FUNCTIONS
        # ============================================================================

        {
            "type": "function",
            "function": {
                "name": "fetch_balances_positions",
                "description": "Fetch account balances and open positions from Hyperliquid. Returns margin summary, perpetual positions, and spot balances.",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_available_trading_pairs",
                "description": "Get all available trading pairs (perpetuals and spot) from Hyperliquid. Returns list with type field indicating 'perp' or 'spot'.",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_leverage",
                "description": "Get the current leverage for a specific coin. Only works if there is an open position for the coin. Returns leverage type (cross/isolated), value, position size, and margin used.",
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "coin": {
                            "type": "string",
                            "description": "The trading pair symbol (e.g., 'ETH', 'BTC').",
                        },
                    },
                    "required": ["coin"],
                },
            },
        },
    ]
    
    # Build handler registry mapping function names to handlers
    handler_registry = {
        "fetch_balances_positions": fetch_balances_and_positions,
        "get_available_trading_pairs": get_available_trading_pairs,
        "get_leverage": get_leverage,
    }

    return tools, handler_registry
