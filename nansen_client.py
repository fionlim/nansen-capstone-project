import os
from typing import Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE = os.getenv("NANSEN_BASE_URL", "https://api.nansen.ai/api/beta")
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
