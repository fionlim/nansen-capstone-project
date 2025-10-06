from typing import Dict, List
import requests
import streamlit as st

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
    
     # Add more function as needed for other endpoints below :D
    
    def tgm_dex_trades(self, payload: Dict, fetch_all: bool = False, n: int = 1):
        if fetch_all:
            return self._post_all_pages(payload, "/tgm/dex-trades")
        elif n > 1:
            return self._post_n_pages(payload, "/tgm/dex-trades", n)
        else:
            return self._post("/tgm/dex-trades", payload).get("data", [])

    def tgm_holders(self, payload: Dict, fetch_all: bool = False, n: int = 1):
        if fetch_all:
            return self._post_all_pages(payload, "/tgm/holders")
        elif n > 1:
            return self._post_n_pages(payload, "/tgm/holders", n)
        else:
            return self._post("/tgm/holders", payload).get("data", [])
    
    def tgm_pnl_leaderboard(self, payload: Dict, fetch_all: bool = False, n: int = 1):
        """
        Fetch all pages of /tgm/pnl-leaderboard, aggregating results into a single list.
        """
        if fetch_all:
            return self._post_all_pages(payload, "/tgm/pnl-leaderboard")
        elif n > 1:
            return self._post_n_pages(payload, "/tgm/pnl-leaderboard", n)
        else:
            return self._post("/tgm/pnl-leaderboard", payload).get("data", [])
    
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
