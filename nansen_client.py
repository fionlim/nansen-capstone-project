from typing import Dict
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

    def smart_money_netflow(self, payload: Dict):
        return self._post("/smart-money/netflow", payload)

    def smart_money_holdings(self, payload: Dict):
        return self._post("/smart-money/holdings", payload)

    def tgm_token_screener(self, payload: Dict):
        return self._post("/token-screener", payload)

    def tgm_flow_intelligence(self, payload: Dict):
        return self._post("/tgm/flow-intelligence", payload)