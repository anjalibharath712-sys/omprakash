import os
import requests
from typing import Any, Dict, Optional


class BenefitsClient:
    """Client for the external benefits eligibility API."""

    def __init__(self) -> None:
        self.url = os.getenv(
            "BENEFITS_API_URL",
            "https://76f12bb8-05d1-4e12-a0bd-5e5830ae7b37.mock.pstmn.io/ebv/benefits"
        )
        self.timeout = int(os.getenv("BENEFITS_API_TIMEOUT", "15"))

    def check_eligibility(
        self,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        return self._call_remote_api(payload, headers=headers)

    def _call_remote_api(
        self,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        try:
            response = requests.post(
                self.url,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
            try:
                body = response.json()
            except ValueError:
                body = response.text
            return {
                "success": response.ok,
                "status_code": response.status_code,
                "body": body,
                "url": self.url,
            }
        except requests.RequestException as exc:
            return {
                "success": False,
                "error": str(exc),
                "url": self.url,
            }
