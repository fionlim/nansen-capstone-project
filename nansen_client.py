import json
from typing import Dict, List

import requests
import streamlit as st

API_BASE = "https://api.nansen.ai/api/v1"

class NansenClient:
    def __init__(self):
        self.base_url = API_BASE
        self.headers = {
            "apiKey": st.secrets["apiKey"],
            "Content-Type": "application/json",
        }
        if not self.headers["apiKey"]:
            raise ValueError("Missing apiKey. Add it to .env file.")

    def _post(self, path: str, json_body: Dict):
        url = f"{self.base_url}{path}"
        resp = requests.post(url, headers=self.headers, data=json.dumps(json_body))
        data = resp.json()
        if isinstance(data, dict) and "data" in data:
            return data["data"]
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data
        return []

    def smart_money_inflows(self, payload: Dict) -> List[Dict]:
        return self._post("/smart-money/inflows", payload)

    def smart_money_holdings(self, payload: Dict) -> List[Dict]:
        return self._post("/smart-money/holdings", payload)

    def token_screener(self, payload: Dict) -> List[Dict]:
        return self._post("/token-screener", payload)

    def flow_intelligence(self, payload: Dict) -> List[Dict]:
        return self._post("/tgm/flow-intelligence", payload)
    
    def dex_trades(self, payload: Dict) -> List[Dict]:
        all_results = []
        page = payload["pagination"]["page"]
        per_page = payload["pagination"]["per_page"]
        while True:
            payload["pagination"]["page"] = page
            print("page: ", page)
            results = self._post("/tgm/dex-trades", payload)
            if not results:
                break
            all_results.extend(results)
            if len(results) < per_page:
                break  # Last page reached
            page += 1
        payload["pagination"]["page"] = 1  # Reset page to original
        return self._post("/tgm/dex-trades", payload)

    def tgm_holders(self, payload: Dict) -> List[Dict]: 
        """
        Fetch all pages of /tgm/holders, aggregating results into a single list.
        """
        all_results = []
        page = payload["pagination"]["page"]
        per_page = payload["pagination"]["per_page"]
        while True:
            payload["pagination"]["page"] = page
            print("page: ", page)
            results = self._post("/tgm/holders", payload)
            if not results:
                break
            all_results.extend(results)
            if len(results) < per_page:
                break  # Last page reached
            page += 1
        payload["pagination"]["page"] = 1  # Reset page to original
        return all_results 
    
    def tgm_pnl_leaderboard(self, payload: Dict) -> List[Dict]:
        """
        Fetch all pages of /tgm/pnl-leaderboard, aggregating results into a single list.
        """
        all_results = []
        page = payload["pagination"]["page"]
        per_page = payload["pagination"]["per_page"]
        while True:
            payload["pagination"]["page"] = page
            results = self._post("/tgm/pnl-leaderboard", payload)
            if not results:
                break
            all_results.extend(results)
            if len(results) < per_page:
                break  # Last page reached
            page += 1
        payload["pagination"]["page"] = 1  # Reset page to original
        return all_results
    
    def pfl_address_pnl_summary(self, payloads: List[Dict]) -> List[Dict]:
        """Fetch PnL summary for a specific address."""
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

    def token_flows(self, payload: Dict) -> List[Dict]:
        """Token God Mode flows (price history and flows)."""
        return self._post("/tgm/flows", payload)