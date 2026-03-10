"""
HTTP clients that let the v666 engine consume the optional v3 FastAPI nodes.
The scanner can work without them (fail-open), but if they exist we use them
to veto spoof/rug conditions and to enrich the opportunity with regime/macro context.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from config.config import cfg


class ServiceClients:
    def __init__(self) -> None:
        self.endpoints = {
            "spoofhunter": cfg.SPOOFHUNTER_URL,
            "antirug": cfg.ANTIRUG_URL,
            "newtonian": cfg.NEWTONIAN_URL,
            "narrative": cfg.NARRATIVE_URL,
            "econopredator": cfg.ECONOPREDATOR_URL,
        }

    def enabled(self, service: str) -> bool:
        return cfg.FUSION_USE_REMOTE_SERVICES and bool(self.endpoints.get(service))

    async def _request_json(
        self,
        service: str,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        base = (self.endpoints.get(service) or "").rstrip("/")
        if not base:
            return None
        url = f"{base}/{path.lstrip('/')}"
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.request(method.upper(), url, json=json)
            resp.raise_for_status()
            return resp.json()

    async def get_health(self, service: str) -> Optional[Dict[str, Any]]:
        return await self._request_json(service, "GET", "/health")

    async def get_spoof_state(self, symbol: str) -> Optional[Dict[str, Any]]:
        clean = symbol.replace("/", "").replace(":", "")
        return await self._request_json("spoofhunter", "GET", f"/spoof_state/{clean}")

    async def get_regime_state(self, asset: str) -> Optional[Dict[str, Any]]:
        clean = asset.replace("/", "").replace(":", "")
        return await self._request_json("newtonian", "GET", f"/gravity_state/{clean}")

    async def get_narrative_state(self, symbol_or_asset: str) -> Optional[Dict[str, Any]]:
        clean = symbol_or_asset.replace("/", "").replace(":", "")
        return await self._request_json("narrative", "GET", f"/sentiment_state/{clean}")

    async def get_macro_state(self, symbol: str) -> Optional[Dict[str, Any]]:
        clean = symbol.replace("/", "").replace(":", "")
        return await self._request_json("econopredator", "GET", f"/market_data/{clean}")

    async def analyze_token(self, metrics: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return await self._request_json("antirug", "POST", "/analyze_token_v2", json=metrics)

    async def health(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        for name in self.endpoints:
            try:
                data[name] = await self.get_health(name)
            except Exception as exc:
                data[name] = {"ok": False, "error": str(exc)}
        return data


service_clients = ServiceClients()
