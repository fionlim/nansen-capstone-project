from typing import List, Dict
import pandas as pd


def inflows_to_dataframe(items: List[Dict]) -> pd.DataFrame:
    if not items:
        return pd.DataFrame(columns=[
            "chain", "tokenAddress", "symbol", "sectors",
            "volume24hUSD", "volume7dUSD", "volume30dUSD",
            "nofTraders", "tokenAgeDays", "marketCap"
        ])
    df = pd.DataFrame(items)
    if "sectors" in df.columns:
        df["sectors"] = df["sectors"].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
    for col in ["volume24hUSD", "volume7dUSD", "volume30dUSD", "marketCap"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "tokenAgeDays" in df.columns:
        df["tokenAgeDaysNum"] = pd.to_numeric(df["tokenAgeDays"], errors="coerce")
    return df


def holdings_to_dataframe(items: List[Dict]) -> pd.DataFrame:
    if not items:
        return pd.DataFrame(columns=[
            "chain", "tokenAddress", "symbol", "sectors",
            "balanceUsd", "balancePctChange24H", "nofHolders",
            "shareOfHoldings", "tokenAgeDays", "marketCap"
        ])
    df = pd.DataFrame(items)
    if "sectors" in df.columns:
        df["sectors"] = df["sectors"].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
    if "balancePctChange24H" not in df.columns and "balancePctChange24h" in df.columns:
        df["balancePctChange24H"] = df["balancePctChange24h"]
    for col in ["balanceUsd", "balancePctChange24H", "shareOfHoldings", "marketCap"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "tokenAgeDays" in df.columns:
        df["tokenAgeDaysNum"] = pd.to_numeric(df["tokenAgeDays"], errors="coerce")
    return df


def screener_to_dataframe(items: List[Dict]) -> pd.DataFrame:
    if not items:
        return pd.DataFrame(columns=[
            "chain", "tokenAddressHex", "tokenSymbol", "tokenAgeDays",
            "marketCap", "liquidity", "priceUsd", "priceChange", "fdv", "fdvMcRatio",
            "buyVolume", "inflowFdvRatio", "outflowFdvRatio", "sellVolume", "volume", "netflow"
        ])
    df = pd.DataFrame(items)
    numeric_cols = ["marketCap", "fdv", "fdvMcRatio", "buyVolume", "sellVolume", "volume", "netflow"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ["priceUsd", "priceChange", "liquidity", "inflowFdvRatio", "outflowFdvRatio"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "tokenAgeDays" in df.columns:
        df["tokenAgeDaysNum"] = pd.to_numeric(df["tokenAgeDays"], errors="coerce")
    return df


def flow_to_dataframe(items: List[Dict]) -> pd.DataFrame:
    if not items:
        return pd.DataFrame(columns=[
            "public_figure_net_flow_usd",
            "public_figure_avg_flow_usd",
            "public_figure_wallet_count",
            "top_pnl_net_flow_usd",
            "top_pnl_avg_flow_usd",
            "top_pnl_wallet_count",
            "whale_net_flow_usd",
            "whale_avg_flow_usd",
            "whale_wallet_count",
            "smart_trader_net_flow_usd",
            "smart_trader_avg_flow_usd",
            "smart_trader_wallet_count",
            "exchange_net_flow_usd",
            "exchange_avg_flow_usd",
            "exchange_wallet_count",
            "fresh_wallets_net_flow_usd",
            "fresh_wallets_avg_flow_usd",
            "fresh_wallets_wallet_count"])
    df = pd.DataFrame(items)
    return df

def holders_to_dataframe(data: List[Dict]) -> pd.DataFrame:
    if not data:
        return pd.DataFrame(columns=[
            "address", "address_label", "token_amount",
            "total_outflow", "total_inflow", "balance_change_24h",
            "balance_change_7d", "balance_change_30d", "ownership_percentage",
            "value_usd"])
    df = pd.DataFrame(data)
    return df
