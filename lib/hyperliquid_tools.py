from typing import Dict, Any, Optional, List, Tuple, Callable

from lib.hyperliquid_sdk import fetch_balances_and_positions


def get_hyperliquid_tools() -> Tuple[List[Dict[str, Any]], Dict[str, Callable]]:
    """
    Get Hyperliquid tools in OpenAI function calling format.
    
    Returns:
        tuple: (tools_list, handler_registry)
            - tools_list: List of tools in OpenAI format
            - handler_registry: Dict mapping function names to handler functions
    """

    # ============================================================================
    # FETCH/QUERY FUNCTIONS
    # ============================================================================

    def fetch_balances_handler() -> Dict[str, Any]:
        """Handler for fetching balances and positions."""
        return fetch_balances_and_positions()

    tools = [
        {
            "type": "function",
            "function": {
                "name": "fetch_balances_positions",
                "description": "Fetch account balances and open positions from Hyperliquid. Returns margin summary, perpetual positions, and spot balances.",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
    ]
    
    # Build handler registry mapping function names to handlers
    handler_registry = {
        "fetch_balances_positions": fetch_balances_handler,
    }

    return tools, handler_registry
