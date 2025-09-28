import os
from typing import Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE = os.getenv("NANSEN_BASE_URL", "https://api.nansen.ai/api/v1")
API_KEY = os.getenv("apiKey")
CANDLES_PATH = os.getenv("NANSEN_CANDLES_PATH", "")

class NansenClient:
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.base_url = base_url or API_BASE
        self.headers = {
            "apiKey": api_key or API_KEY,
            "Content-Type": "application/json",
        }
        if not self.headers["apiKey"]:
            raise ValueError("Missing apiKey. Add it to .env file.")

    def _post(self, path: str, json_body: Dict, timeout: int = 45):
        url = f"{self.base_url}{path}"
        resp = requests.post(url, headers=self.headers, json=json_body, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict) and "data" in data:
            return data["data"]
        if isinstance(data, list):
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
            data = self._post("/profiler/address/pnl-summary", payload)
            print("summary data: ", data)
            # add address to each item in data
            data['address'] = payload['address']
            all_results.append(data)
        return all_results
    

    def token_candles(self, payload: Dict, path: Optional[str] = None) -> List[Dict]:
        """
        Fetch OHLCV candles for a token. The endpoint path must be provided via env NANSEN_CANDLES_PATH
        or explicitly via the path argument, to comply with documented endpoints.
        """
        candles_path = (path or CANDLES_PATH).strip()
        if not candles_path:
            raise ValueError("Missing NANSEN_CANDLES_PATH env or explicit path for candles endpoint.")
        if not candles_path.startswith("/"):
            candles_path = "/" + candles_path
        return self._post(candles_path, payload)

    def token_flows(self, payload: Dict) -> List[Dict]:
        """Token God Mode flows (price history and flows)."""
        return self._post("/tgm/flows", payload)
