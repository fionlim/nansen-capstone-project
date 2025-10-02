from typing import Dict, List, Optional
import requests
import streamlit as st
from copy import deepcopy

API_BASE = st.secrets.get("NANSEN_API_BASE", "https://api.nansen.ai/api/v1")
API_KEY = st.secrets.get("apiKey", "")

class NansenClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or API_BASE
        self.headers = {
            "apiKey": API_KEY,
            "Content-Type": "application/json",
        }
        if not self.headers["apiKey"]:
            raise ValueError("Missing apiKey. Add it to .streamlit/secrets.toml.")

    # ---------- Core HTTP ----------
    def _post(self, path: str, json_body: Dict, timeout: int = 60) -> Dict:
        url = f"{self.base_url}{path}"
        resp = requests.post(url, headers=self.headers, json=json_body, timeout=timeout)
        resp.raise_for_status()
        return resp.json()

    def _post_all_pages(
        self,
        path: str,
        json_body: Dict,
        data_key: str = "data",
        per_page: int = 100,
        timeout: int = 60,
    ) -> List[Dict]:
        pl = deepcopy(json_body)
        p = pl.setdefault("pagination", {})
        p.setdefault("page", 1)
        p.setdefault("per_page", per_page)

        out: List[Dict] = []
        while True:
            url = f"{self.base_url}{path}"
            resp = requests.post(url, headers=self.headers, json=pl, timeout=timeout)
            resp.raise_for_status()
            js = resp.json()
            out.extend(js.get(data_key, []))
            pg = js.get("pagination", {})
            if pg.get("is_last_page", True):
                break
            pl["pagination"]["page"] = pg.get("page", pl["pagination"]["page"]) + 1
        return out

    def _post_first_n(
        self,
        path: str,
        json_body: Dict,
        n: int,
        data_key: str = "data",
        per_page: int = 50,
        timeout: int = 60,
    ) -> List[Dict]:
        pl = deepcopy(json_body)
        p = pl.setdefault("pagination", {})
        p.setdefault("page", 1)
        p.setdefault("per_page", per_page)

        out: List[Dict] = []
        while len(out) < n:
            url = f"{self.base_url}{path}"
            resp = requests.post(url, headers=self.headers, json=pl, timeout=timeout)
            resp.raise_for_status()
            js = resp.json()
            rows = js.get(data_key, [])
            out.extend(rows)
            pg = js.get("pagination", {})
            if pg.get("is_last_page", True):
                break
            pl["pagination"]["page"] = pg.get("page", pl["pagination"]["page"]) + 1
        return out[:n]

    # ---------- Smart Money endpoints ----------
    def smart_money_netflow(self, payload: Dict):
        return self._post("/smart-money/netflow", payload)

    def smart_money_holdings(self, payload: Dict):
        return self._post("/smart-money/holdings", payload)
    
    # ---------- TGM endpoints ----------

    def tgm_token_screener(self, payload: Dict):
        return self._post("/token-screener", payload)

    def tgm_flow_intelligence(self, payload: Dict):
        return self._post("/tgm/flow-intelligence", payload)

    # ---------- Profiler endpoints ----------
    # Base prefix for Profiler
    _P = "/profiler"

    def profiler_address_current_balance(self, payload: Dict) -> Dict:
        return self._post(f"{self._P}/address/current-balance", payload)

    def profiler_address_historical_balances_all(self, payload: Dict) -> List[Dict]:
        return self._post_all_pages(f"{self._P}/address/historical-balances", payload)

    def profiler_address_counterparties(self, payload: Dict) -> Dict:
        return self._post(f"{self._P}/address/counterparties", payload)

    def profiler_address_related_wallets(self, payload: Dict) -> Dict:
        return self._post(f"{self._P}/address/related-wallets", payload)

    def profiler_address_pnl_summary(self, payload: Dict) -> Dict:
        return self._post(f"{self._P}/address/pnl-summary", payload)

    def profiler_address_transactions_first_n(self, payload: Dict, n: int = 100) -> List[Dict]:
        return self._post_first_n(f"{self._P}/address/transactions", payload, n=n)