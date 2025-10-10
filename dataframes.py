from typing import List, Dict
import pandas as pd


# ---------- Smart Money ----------

# smart-money/netflow
def net_flow_to_dataframe(items: List[Dict]) -> pd.DataFrame:
    if not items:
        return pd.DataFrame(
            columns=[
                "token_address",
                "token_symbol",
                "netflow_24h_usd",
                "net_flow_7d_usd",
                "net_flow_30d_usd",
                "chain",
                "token_sectors",
                "trader_count",
                "token_age_days",
                "market_cap_usd",
            ]
        )
    df = pd.DataFrame(items)
    if "token_sectors" in df.columns:
        df["token_sectors"] = df["token_sectors"].apply(
            lambda x: ", ".join(x) if isinstance(x, list) else x
        )
    numeric_cols = [
        "netflow_24h_usd",
        "net_flow_7d_usd",
        "net_flow_30d_usd",
        "trader_count",
        "token_age_days",
        "market_cap_usd",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

# smart-money/dex-trades
def dex_trades_to_dataframe(items: List[Dict]) -> pd.DataFrame:
    if not items:
        return pd.DataFrame(
            columns=[
                "chain",
                "block_timestamp",
                "transaction_hash",
                "trader_address",
                "trader_address_label",
                "token_bought_address",
                "token_sold_address",
                "token_bought_amount",
                "token_sold_amount",
                "token_bought_symbol",
                "token_sold_symbol",
                "token_bought_age_days",
                "token_sold_age_days",
                "trader_bought_market_cap",
                "token_sold_market_cap",
                "trade_value_usd",
            ]
        )
    df = pd.DataFrame(items)
    if "block_timestamp" in df.columns:
        df["block_timestamp"] = pd.to_datetime(df["block_timestamp"], errors="coerce")
    numeric_cols = [
        "token_bought_amount",
        "token_sold_amount",
        "token_bought_age_days",
        "token_sold_age_days",
        "trader_bought_market_cap",
        "token_sold_market_cap",
        "trade_value_usd",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


# ---------- TGM ----------

# tgm/dex-trades
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

# /token-screener (but under tgm)
def tgm_token_screener_to_dataframe(items: List[Dict]) -> pd.DataFrame:
    if not items:
        return pd.DataFrame(
            columns=[
                "chain",
                "token_address",
                "token_symbol",
                "token_age_days",
                "market_cap_usd",
                "liquidity",
                "price_usd",
                "price_change",
                "fdv",
                "fdv_mc_ratio",
                "buy_volume",
                "inflow_fdv_ratio",
                "outflow_fdv_ratio",
                "sell_volume",
                "volume",
                "netflow",
            ]
        )
    df = pd.DataFrame(items)
    numeric_cols = [
        "token_age_days",
        "market_cap_usd",
        "liquidity",
        "price_usd",
        "price_change",
        "fdv",
        "fdv_mc_ratio",
        "buy_volume",
        "inflow_fdv_ratio",
        "outflow_fdv_ratio",
        "sell_volume",
        "volume",
        "netflow",
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Format columns for display in metric cards
    if "token_age_days" in df.columns:
        df["token_age_days"] = df["token_age_days"].apply(
            lambda x: f"{x:.0f} days" if pd.notna(x) else "N/A"
        )

    if "market_cap_usd" in df.columns:
        df["market_cap_usd"] = df["market_cap_usd"].apply(
            lambda x: (
                f"${x/1_000_000:,.2f}M"
                if pd.notna(x) and x >= 100_000
                else f"${x:,.0f}" if pd.notna(x) else "N/A"
            )
        )

    if "liquidity" in df.columns:
        df["liquidity"] = df["liquidity"].apply(
            lambda x: (
                f"${x/1_000_000:,.2f}M"
                if pd.notna(x) and x >= 100_000
                else f"${x:,.0f}" if pd.notna(x) else "N/A"
            )
        )

    if "price_usd" in df.columns:
        df["price_usd"] = df["price_usd"].apply(
            lambda x: f"${x:.6f}" if pd.notna(x) else "N/A"
        )

    if "price_change" in df.columns:
        df["price_change"] = df["price_change"].apply(
            lambda x: f"{x*100:.2f}%" if pd.notna(x) else "N/A"
        )

    if "fdv" in df.columns:
        df["fdv"] = df["fdv"].apply(
            lambda x: (
                f"${x/1_000_000:,.2f}M"
                if pd.notna(x) and x >= 100_000
                else f"${x:,.0f}" if pd.notna(x) else "N/A"
            )
        )

    if "volume" in df.columns:
        df["volume"] = df["volume"].apply(
            lambda x: (
                f"${x/1_000_000:,.2f}M"
                if pd.notna(x) and x >= 100_000
                else f"${x:,.0f}" if pd.notna(x) else "N/A"
            )
        )

    if "netflow" in df.columns:
        df["netflow"] = df["netflow"].apply(
            lambda x: (
                f"${x/1_000_000:,.2f}M"
                if pd.notna(x) and abs(x) >= 100_000
                else f"${x:,.0f}" if pd.notna(x) else "N/A"
            )
        )

    if "buy_volume" in df.columns:
        df["buy_volume"] = df["buy_volume"].apply(
            lambda x: (
                f"${x/1_000_000:,.2f}M"
                if pd.notna(x) and x >= 100_000
                else f"${x:,.0f}" if pd.notna(x) else "N/A"
            )
        )

    if "sell_volume" in df.columns:
        df["sell_volume"] = df["sell_volume"].apply(
            lambda x: (
                f"${x/1_000_000:,.2f}M"
                if pd.notna(x) and x >= 100_000
                else f"${x:,.0f}" if pd.notna(x) else "N/A"
            )
        )

    if "inflow_fdv_ratio" in df.columns:
        df["inflow_fdv_ratio"] = df["inflow_fdv_ratio"].apply(
            lambda x: f"{x*100:.2f}%" if pd.notna(x) else "N/A"
        )

    if "outflow_fdv_ratio" in df.columns:
        df["outflow_fdv_ratio"] = df["outflow_fdv_ratio"].apply(
            lambda x: f"{x*100:.2f}%" if pd.notna(x) else "N/A"
        )
    return df

# tgm/holders
def holders_to_dataframe(data: List[Dict]) -> pd.DataFrame:
    if not data:
        return pd.DataFrame(
            columns=[
                "address",
                "address_label",
                "token_amount",
                "total_outflow",
                "total_inflow",
                "balance_change_24h",
                "balance_change_7d",
                "balance_change_30d",
                "ownership_percentage",
                "value_usd",
            ]
        )
    df = pd.DataFrame(data)
    def categorize_holder_type(address_label: str) -> str:
        if "🏦" in address_label:
            return "exchange"
        address_label = address_label.lower()
        if (
            "🤓" in address_label
            or "smart trader" in address_label
            or "fund" in address_label
        ):
            return "smart_money"
        elif "whale" in address_label:
            return "whale"
        elif "👤" in address_label:
            return "public_figure"
        else:
            return "other"
    df["holder_type"] = df["address_label"].apply(categorize_holder_type)
    return df

# tgm/pnl-leaderboard
def pnl_leaderboard_to_dataframe(data: List[Dict]) -> pd.DataFrame:
    if not data:
        return pd.DataFrame(
            columns=[
                "trader_address",
                "trader_address_label",
                "price_usd",
                "pnl_usd_realised",
                "pnl_usd_unrealised",
                "holding_amount",
                "holding_usd",
                "max_balance_held",
                "max_balance_held_usd",
                "still_holding_balance_ratio",
                "netflow_amount_usd",
                "netflow_amount",
                "roi_percent_total",
                "roi_percent_realised",
                "roi_percent_unrealised",
                "pnl_usd_total",
                "nof_trades",
            ]
        )
    df = pd.DataFrame(data)
    return df


# ---------- Profiler ----------

# profiler/address/pnl-summary
def pnl_summary_to_dataframe(data: List[Dict]) -> pd.DataFrame:
    """
    For now just get the traded_token_count, traded_times, realised_pnl_usd, realized_pnl_percent, and win_rate of the wallet
    """
    if not data:
        return pd.DataFrame(
            columns=[
                "address",
                "traded_token_count",
                "traded_times",
                "realised_pnl_usd",
                "realized_pnl_percent",
                "win_rate",
            ]
        )
    data_new = []
    for record in data:
        record_new = {
            k: record.get(k, None)
            for k in [
                "address",
                "traded_token_count",
                "traded_times",
                "realised_pnl_usd",
                "realized_pnl_percent",
                "win_rate",
            ]
        }
        data_new.append(record_new)
    df = pd.DataFrame(data_new)
    return df

# TODO: use this for pfl_roi_pnl_scatter & pfl_token_pnl_waterfall components
# profiler/address/pnl-summary
def single_pnl_summary_to_dataframe(data: List[Dict]) -> pd.DataFrame:
    if not data:
        return pd.DataFrame(
            columns=[
                "top5_tokens",
                "traded_token_count",
                "traded_times",
                "realised_pnl_usd",
                "realized_pnl_percent",
                "win_rate",
            ]
        )
    top5_tokens = data.get("top5_tokens", [])
    for token in top5_tokens:
        for col in ["realized_pnl", "realized_roi"]:
            if col in token:
                try:
                    token[col] = float(token[col])
                except (TypeError, ValueError):
                    token[col] = 0
    data_flat = data.copy()
    data_flat["top5_tokens"] = top5_tokens
    
    df = pd.DataFrame([data_flat])

    numeric_cols = [
        "traded_token_count",
        "traded_times",
        "realised_pnl_usd",
        "realized_pnl_percent",
        "win_rate",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

#profiler/address/historical-balances
def historical_balances_to_dataframe(data: List[Dict]) -> pd.DataFrame:
    if not data:
        return pd.DataFrame(
            columns=[
                "block_timestamp",
                "token_address",
                "chain",
                "token_amount",
                "value_usd",
                "token_symbol",
            ]
        )
    df = pd.DataFrame(data)
    if "block_timestamp" in df.columns:
        df["block_timestamp"] = pd.to_datetime(df["block_timestamp"], errors="coerce")
    numeric_cols = ["token_decimals", "balance", "value_usd"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

#profiler/address/counterparties
def counterparties_to_dataframe(data: List[Dict]) -> pd.DataFrame:
    if not data:
        return pd.DataFrame(
            columns=[
                "counterparty_address",
                "token_info",
                "interaction_count",
                "total_volume_usd",
                "volume_in_usd",
                "volume_out_usd",
                "counterparty_address_label"
            ]
        )
    df = pd.DataFrame(data)
    numeric_cols = [
        "interaction_count",
        "total_volume_usd",
        "volume_in_usd",
        "volume_out_usd",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

#profiler/address/related-wallets
def related_wallets_to_dataframe(data: List[Dict]) -> pd.DataFrame:
    if not data:
        return pd.DataFrame(
            columns=[
                "address",
                "address_label",
                "relation",
                "transaction_hash",
                "block_timestamp",
                "order",
                "chain"
            ]
        )
    df = pd.DataFrame(data)
    if "order" in df.columns:
        df["order"] = pd.to_numeric(df["order"], errors="coerce")
    return df