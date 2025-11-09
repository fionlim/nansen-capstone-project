from typing import Dict, Any, Optional, List, Tuple, Callable

from lib.hyperliquid_sdk import (
    fetch_balances_and_positions,
    get_available_trading_pairs,
    get_leverage,
    place_limit_order,
    place_market_order,
    set_take_profit_stop_loss,
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

        # ============================================================================
        # ORDER PLACING FUNCTIONS
        # ============================================================================

        {
            "type": "function",
            "function": {
                "name": "place_limit_order",
                "description": "Place a limit order on Hyperliquid. Specify the coin, buy/sell direction, size, and limit price. Optionally set leverage before placing the order.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "coin": {
                            "type": "string",
                            "description": "The trading pair symbol (e.g., 'ETH', 'BTC').",
                        },
                        "is_buy": {
                            "type": "boolean",
                            "description": "True for buy order, False for sell order.",
                        },
                        "sz": {"type": "number", "description": "Notional size of the order."},
                        "limit_px": {
                            "type": "number",
                            "description": "Limit price for the order.",
                        },
                        "time_in_force": {
                            "type": "string",
                            "description": "Order time in force: 'Gtc' (Good till Cancel), 'Ioc' (Immediate or Cancel), or 'Alo' (Allow Orders). Default is 'Gtc'.",
                            "enum": ["Gtc", "Ioc", "Alo"],
                        },
                        "leverage": {
                            "type": "integer",
                            "description": "Optional leverage value to set before placing order (e.g., 10 for 10x leverage). If not provided, uses existing leverage setting.",
                        },
                        "is_cross": {
                            "type": "boolean",
                            "description": "If true, use cross margin, else isolated margin. Only used if leverage is set. Default is true (cross margin).",
                        },
                    },
                    "required": ["coin", "is_buy", "sz", "limit_px"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "place_market_order",
                "description": "Place a market order on Hyperliquid. This executes immediately at the best available price with slippage tolerance. Optionally set leverage before placing the order.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "coin": {
                            "type": "string",
                            "description": "The trading pair symbol (e.g., 'ETH', 'BTC').",
                        },
                        "is_buy": {
                            "type": "boolean",
                            "description": "True for buy order, False for sell order.",
                        },
                        "sz": {"type": "number", "description": "Notional size of the order."},
                        "slippage": {
                            "type": "number",
                            "description": "Maximum slippage tolerance as decimal (e.g., 0.05 for 5%). Default is 0.05.",
                        },
                        "leverage": {
                            "type": "integer",
                            "description": "Optional leverage value to set before placing order (e.g., 10 for 10x leverage). If not provided, uses existing leverage setting.",
                        },
                        "is_cross": {
                            "type": "boolean",
                            "description": "If true, use cross margin, else isolated margin. Only used if leverage is set. Default is true (cross margin).",
                        },
                    },
                    "required": ["coin", "is_buy", "sz"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "set_take_profit_stop_loss",
                "description": "Set take profit (tp) and/or stop loss (sl) orders using trigger orders for open positions. At least one of take_profit_price or stop_loss_price must be provided.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "coin": {
                            "type": "string",
                            "description": "The trading pair symbol (e.g., 'ETH', 'BTC').",
                        },
                        "take_profit_price": {
                            "type": "number",
                            "description": "Trigger price for take profit order (optional).",
                        },
                        "stop_loss_price": {
                            "type": "number",
                            "description": "Trigger price for stop loss order (optional).",
                        },
                        "is_market": {
                            "type": "boolean",
                            "description": "If true, use market order when triggered, else limit order. Default is true.",
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
        "place_limit_order": place_limit_order,
        "place_market_order": place_market_order,
        "set_take_profit_stop_loss": set_take_profit_stop_loss,
    }

    return tools, handler_registry
