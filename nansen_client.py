import requests
import streamlit as st
from typing import Dict, List

API_BASE = st.secrets.get("NANSEN_API_BASE", "https://api.nansen.ai/api/v1")
API_KEY = st.secrets.get("apiKey", "")

class NansenClient:
    def __init__(self):
        self.base_url = API_BASE
        self.headers = {
            "apiKey": API_KEY,
            "Content-Type": "application/json",
        }
        if not self.headers["apiKey"]:
            raise ValueError("Missing apiKey. Add it to .streamlit/secrets.toml.")


    # ---------- Helper functions ----------

    def _post(self, path: str, json_body: Dict, timeout: int = 45):
        url = f"{self.base_url}{path}"
        resp = requests.post(url, headers=self.headers, json=json_body, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        return data
    
    def _post_all_pages(self, payload: Dict, path: str):
        all_items = []
        while True:
            response = self._post(path, payload)
            items = response.get("data", [])
            all_items.extend(items)
            if response["pagination"]["is_last_page"] is True:
                break
            payload["pagination"]["page"] += 1
        return all_items

    def _post_n_pages(self, payload: Dict, path: str, n: int):
        all_items = []
        for _ in range(n):
            response = self._post(path, payload)
            items = response.get("data", [])
            all_items.extend(items)
            if response["pagination"]["is_last_page"] is True:
                break
            payload["pagination"]["page"] += 1
        return all_items
        

    # ---------- Smart Money endpoints ----------

    def smart_money_netflow(self, payload: Dict, fetch_all: bool = False, n: int = 1):
        if fetch_all:
            return self._post_all_pages(payload, "/smart-money/netflow")
        elif n > 1:
            return self._post_n_pages(payload, "/smart-money/netflow", n)
        else:
            return self._post("/smart-money/netflow", payload).get("data", [])

    def smart_money_dex_trades(self, payload: Dict, fetch_all: bool = False, n: int = 1):
        if fetch_all:
            return self._post_all_pages(payload, "/smart-money/dex-trades")
        elif n > 1:
            return self._post_n_pages(payload, "/smart-money/dex-trades", n)
        else:
            return self._post("/smart-money/dex-trades", payload).get("data", [])
    

    # ---------- TGM endpoints ----------

    def tgm_dex_trades(self, payload: Dict, fetch_all: bool = False, n: int = 1):
        if fetch_all:
            return self._post_all_pages(payload, "/tgm/dex-trades")
        elif n > 1:
            return self._post_n_pages(payload, "/tgm/dex-trades", n)
        else:
            return self._post("/tgm/dex-trades", payload).get("data", [])
    
    def tgm_token_screener(self, payload: Dict):
        return self._post("/token-screener", payload).get("data", [])

    def tgm_holders(self, payload: Dict, fetch_all: bool = False, n: int = 1):
        if fetch_all:
            return self._post_all_pages(payload, "/tgm/holders")
        elif n > 1:
            return self._post_n_pages(payload, "/tgm/holders", n)
        else:
            return self._post("/tgm/holders", payload).get("data", [])
    
    def tgm_pnl_leaderboard(self, payload: Dict, fetch_all: bool = False, n: int = 1):
        if fetch_all:
            return self._post_all_pages(payload, "/tgm/pnl-leaderboard")
        elif n > 1:
            return self._post_n_pages(payload, "/tgm/pnl-leaderboard", n)
        else:
            return self._post("/tgm/pnl-leaderboard", payload).get("data", [])
    
    
    # ---------- Profiler endpoints ----------

    # Base prefix for Profiler
    _P = "/profiler"

    def profiler_address_current_balance(self, payload: Dict, fetch_all: bool = False, n: int = 1):
        path = f"{self._P}/address/current-balance"
        if fetch_all:
            return self._post_all_pages(payload, path)
        elif n > 1:
            return self._post_n_pages(payload, path, n)
        else:
            return self._post(path, payload).get("data", [])

    def profiler_address_historical_balances(self, payload: Dict, fetch_all: bool = False, n: int = 1):
        path = f"{self._P}/address/historical-balances"
        if fetch_all:
            return self._post_all_pages(payload, path)
        elif n > 1:
            return self._post_n_pages(payload, path, n)
        else:
            return self._post(path, payload).get("data", [])

    def profiler_address_counterparties(self, payload: Dict, fetch_all: bool = False, n: int = 1):
        path = f"{self._P}/address/counterparties"
        if fetch_all:
            return self._post_all_pages(payload, path)
        elif n > 1:
            return self._post_n_pages(payload, path, n)
        else:
            return self._post(path, payload).get("data", [])

    def profiler_address_related_wallets(self, payload: Dict, fetch_all: bool = False, n: int = 1):
        path = f"{self._P}/address/related-wallets"
        if fetch_all:
            return self._post_all_pages(payload, path)
        elif n > 1:
            return self._post_n_pages(payload, path, n)
        else:
            return self._post(path, payload).get("data", [])

    def profiler_address_transactions(self, payload: Dict, fetch_all: bool = False, n: int = 1):
        path = f"{self._P}/address/transactions"
        if fetch_all:
            return self._post_all_pages(payload, path)
        elif n > 1:
            return self._post_n_pages(payload, path, n)
        else:
            return self._post(path, payload).get("data", [])

    def profiler_address_pnl_summary(self, payload: Dict):
        """
        NOTE: This endpoint returns a single summary object (not a list under 'data').
        Kept as a simple _post (no pagination flags) so components can access keys like
        'top5_tokens' directly, e.g., resp.get('top5_tokens', []).
        """
        path = f"{self._P}/address/pnl-summary"
        return self._post(path, payload)
        
    # TODO: COMBINE WITH PROFILER_ADDRESS_PNL_SUMMARY in the future
    def pfl_address_pnl_summary(self, payloads: List[Dict]):
        """Fetch PnL summary for array of addresses. Fixed number of pages for each address."""
        all_results = []
        for payload in payloads:
            try:
                data = self._post("/profiler/address/pnl-summary", payload)
                # add address to each item in data
                if "error" in data:
                    print(f"Error in response for address {payload['address']}: {data['error']}")
                    continue
                data['address'] = payload['address']
                all_results.append(data)
            except Exception as e:
                print(f"Error fetching PnL summary for address {payload['address']}: {e}")
                continue
        return all_results
    

    # TODO: REMOVE THESE WHEN MERGED WITH ABOVE
    def get_counterparties(self, payload: dict):
        return self._post("/profiler/address/counterparties", payload).get("data", [])

    def get_related_wallets(self, payload: dict):
        return self._post("/profiler/address/related-wallets", payload).get("data", [])

