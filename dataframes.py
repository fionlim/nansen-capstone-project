from typing import List, Dict
import pandas as pd


def inflows_to_dataframe(items: List[Dict]) -> pd.DataFrame:
    if not items:
        return pd.DataFrame(
            columns=[
                "chain",
                "tokenAddress",
                "symbol",
                "sectors",
                "volume24hUSD",
                "volume7dUSD",
                "volume30dUSD",
                "nofTraders",
                "tokenAgeDays",
                "marketCap",
            ]
        )
    df = pd.DataFrame(items)
    if "sectors" in df.columns:
        df["sectors"] = df["sectors"].apply(
            lambda x: ", ".join(x) if isinstance(x, list) else x
        )
    for col in ["volume24hUSD", "volume7dUSD", "volume30dUSD", "marketCap"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "tokenAgeDays" in df.columns:
        df["tokenAgeDaysNum"] = pd.to_numeric(df["tokenAgeDays"], errors="coerce")
    return df

def net_flow_to_dataframe(items: List[Dict]) -> pd.DataFrame:
    if not items:
        return pd.DataFrame(columns=[
            "token_address", "token_symbol", "netflow_24h_usd",
            "net_flow_7d_usd", "net_flow_30d_usd", "chain",
            "token_sectors", "trader_count", "token_age_days",
            "market_cap_usd"
        ])
    df = pd.DataFrame(items)
    if "token_sectors" in df.columns:
        df["token_sectors"] = df["token_sectors"].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
    numeric_cols = ["netflow_24h_usd", "net_flow_7d_usd", 
                    "net_flow_30d_usd", "trader_count", 
                    "token_age_days", "market_cap_usd"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

def holdings_to_dataframe(items: List[Dict]) -> pd.DataFrame:
    if not items:
        return pd.DataFrame(
            columns=[
                "chain",
                "tokenAddress",
                "symbol",
                "sectors",
                "balanceUsd",
                "balancePctChange24H",
                "nofHolders",
                "shareOfHoldings",
                "tokenAgeDays",
                "marketCap",
            ]
        )
    df = pd.DataFrame(items)
    if "sectors" in df.columns:
        df["sectors"] = df["sectors"].apply(
            lambda x: ", ".join(x) if isinstance(x, list) else x
        )
    if "balancePctChange24H" not in df.columns and "balancePctChange24h" in df.columns:
        df["balancePctChange24H"] = df["balancePctChange24h"]
    for col in ["balanceUsd", "balancePctChange24H", "shareOfHoldings", "marketCap"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "tokenAgeDays" in df.columns:
        df["tokenAgeDaysNum"] = pd.to_numeric(df["tokenAgeDays"], errors="coerce")
    return df

def dex_trades_to_dataframe(items: List[Dict]) -> pd.DataFrame:
    if not items:
        return pd.DataFrame(columns=[
            "chain", "block_timestamp", "transaction_hash",
            "trader_address", "trader_address_label", "token_bought_address",
            "token_sold_address", "token_bought_amount", "token_sold_amount",
            "token_bought_symbol", "token_sold_symbol", "token_bought_age_days",
            "token_sold_age_days", "trader_bought_market_cap", "token_sold_market_cap",
            "trade_value_usd"
        ])
    df = pd.DataFrame(items)
    if "block_timestamp" in df.columns:
        df["block_timestamp"] = pd.to_datetime(df["block_timestamp"], errors="coerce")
    numeric_cols = ["token_bought_amount", "token_sold_amount", 
                "token_bought_age_days", "token_sold_age_days", 
                "trader_bought_market_cap", "token_sold_market_cap",
                "trade_value_usd"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

def dcas_to_dataframe(items: List[Dict]) -> pd.DataFrame:
    if not items:
        return pd.DataFrame(columns=[
            "dca_created_at", "dca_updated_at", "trader_address", 
            "transaction_hash", "trader_address_label", "dca_vault_address",
            "input_token_address", "output_token_address", "deposit_token_amount",
            "token_spent_amount", "output_token_redeemed_amount", "dca_status",
            "input_token_symbol", "output_token_symbol", "deposit_value_usd"
        ])
    df = pd.DataFrame(items)
    for col in ["dca_created_at", "dca_updated_at"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    numeric_cols = ["deposit_token_amount", "token_spent_amount", 
                    "output_token_redeemed_amount", "deposit_value_usd"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

def screener_to_dataframe(items: List[Dict]) -> pd.DataFrame:
    if not items:
        return pd.DataFrame(
            columns=[
                "chain",
                "tokenAddressHex",
                "tokenSymbol",
                "tokenAgeDays",
                "marketCap",
                "liquidity",
                "priceUsd",
                "priceChange",
                "fdv",
                "fdvMcRatio",
                "buyVolume",
                "inflowFdvRatio",
                "outflowFdvRatio",
                "sellVolume",
                "volume",
                "netflow",
            ]
        )
    df = pd.DataFrame(items)
    numeric_cols = [
        "marketCap",
        "fdv",
        "fdvMcRatio",
        "buyVolume",
        "sellVolume",
        "volume",
        "netflow",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in [
        "priceUsd",
        "priceChange",
        "liquidity",
        "inflowFdvRatio",
        "outflowFdvRatio",
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "tokenAgeDays" in df.columns:
        df["tokenAgeDaysNum"] = pd.to_numeric(df["tokenAgeDays"], errors="coerce")
    return df


def flow_to_dataframe(items: List[Dict]) -> pd.DataFrame:
    if not items:
        return pd.DataFrame(
            columns=[
                "publicFigureFlow",
                "publicFigureAvgAbsFlow",
                "publicFigureWallets",
                "topPnlFlow",
                "topPnlAvgAbsFlow",
                "topPnlWallets",
                "whaleFlow",
                "whaleAvgAbsFlow",
                "whaleWallets",
                "smartTraderFlow",
                "smartTraderAvgAbsFlow",
                "smartTraderWallets",
                "exchangeFlow",
                "exchangeAvgAbsFlow",
                "exchangeWallets",
                "freshWalletsFlow",
                "freshWalletsAvgAbsFlow",
                "freshWalletsWallets",
            ]
        )
    df = pd.DataFrame(items)
    for col in [
        "publicFigureAvgAbsFlow",
        "topPnlAvgAbsFlow",
        "whaleAvgAbsFlow",
        "smartTraderAvgAbsFlow",
        "exchangeAvgAbsFlow",
        "freshWalletsAvgAbsFlow",
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def tgm_dex_trades_to_dataframe(items: List[Dict]) -> pd.DataFrame:
    if not items:
        return pd.DataFrame(
            columns=[
                "block_timestamp",
                "transaction_hash",
                "trader_address",
                "trader_address_label",
                "action",
                "token_address",
                "token_name",
                "token_amount",
                "traded_token_address",
                "traded_token_name",
                "traded_token_amount",
                "estimated_swap_price_usd",
                "estimated_value_usd",
            ]
        )
    df = pd.DataFrame(items)

    # Convert timestamp to datetime
    df["block_timestamp"] = pd.to_datetime(df["block_timestamp"], errors="coerce")

    # Convert numeric columns
    numeric_cols = [
        "token_amount",
        "traded_token_amount",
        "estimated_swap_price_usd",
        "estimated_value_usd",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Handle trader_address_label as it might be null
    if "trader_address_label" in df.columns:
        df["trader_address_label"] = df["trader_address_label"].fillna("Unknown")

    return df

def tgm_token_screener_to_dataframe(items: List[Dict]) -> pd.DataFrame:

    if not items:
        return pd.DataFrame(
            columns=[
                'chain', 'token_address_hex', 'token_symbol', 'token_age_days',
                'market_cap_usd', 'liquidity', 'price_usd', 'price_change',
                'fdv', 'fdv_mc_ratio', 'buy_volume', 'inflow_fdv_ratio',
                'outflow_fdv_ratio', 'sell_volume', 'volume', 'netflow'
            ]
        )
    df = pd.DataFrame(items)
    numeric_cols = [
        'token_age_days', 'market_cap_usd', 'liquidity', 'price_usd',
        'price_change', 'fdv', 'fdv_mc_ratio', 'buy_volume',
        'inflow_fdv_ratio', 'outflow_fdv_ratio', 'sell_volume',
        'volume', 'netflow'
    ]
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Format columns for display in metric cards
    if 'market_cap_usd' in df.columns:
        df['market_cap_usd_formatted'] = df['market_cap_usd'].apply(
            lambda x: f"${x/1_000_000:,.2f}M" if pd.notna(x) else 'N/A'
        )
    
    if 'liquidity' in df.columns:
        df['liquidity_formatted'] = df['liquidity'].apply(
            lambda x: f"${x/1_000_000:,.2f}M" if pd.notna(x) else 'N/A'
        )
    
    if 'price_usd' in df.columns:
        df['price_usd_formatted'] = df['price_usd'].apply(
            lambda x: f"${x:.6f}" if pd.notna(x) else 'N/A'
        )
    
    if 'price_change' in df.columns:
        df['price_change_formatted'] = df['price_change'].apply(
            lambda x: f"{x*100:.2f}%" if pd.notna(x) else 'N/A'
        )
    
    if 'fdv' in df.columns:
        df['fdv_formatted'] = df['fdv'].apply(
            lambda x: f"${x/1_000_000:,.2f}M" if pd.notna(x) else 'N/A'
        )
    
    if 'volume' in df.columns:
        df['volume_formatted'] = df['volume'].apply(
            lambda x: f"${x/1_000_000:,.2f}M" if pd.notna(x) else 'N/A'
        )
    
    if 'netflow' in df.columns:
        df['netflow_formatted'] = df['netflow'].apply(
            lambda x: f"${x/1_000_000:,.2f}M" if pd.notna(x) else 'N/A'
        )
    
    if 'buy_volume' in df.columns:
        df['buy_volume_formatted'] = df['buy_volume'].apply(
            lambda x: f"${x/1_000_000:,.2f}M" if pd.notna(x) else 'N/A'
        )
    
    if 'sell_volume' in df.columns:
        df['sell_volume_formatted'] = df['sell_volume'].apply(
            lambda x: f"${x/1_000_000:,.2f}M" if pd.notna(x) else 'N/A'
        )
    
    if 'inflow_fdv_ratio' in df.columns:
        df['inflow_fdv_ratio_formatted'] = df['inflow_fdv_ratio'].apply(
            lambda x: f"{x*100:.2f}%" if pd.notna(x) else 'N/A'
        )
    
    if 'outflow_fdv_ratio' in df.columns:
        df['outflow_fdv_ratio_formatted'] = df['outflow_fdv_ratio'].apply(
            lambda x: f"{x*100:.2f}%" if pd.notna(x) else 'N/A'
        )
    
    return df