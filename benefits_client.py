import os
import requests
from typing import Any, Dict


class BenefitsClient:
    """Simple wrapper for the benefits eligibility backend or a local fallback mock."""

    def __init__(self) -> None:
        self.url = os.getenv("BENEFITS_API_URL", "")
        self.timeout = int(os.getenv("BENEFITS_API_TIMEOUT", "15"))

    def check_eligibility(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if self.url:
            return self._call_remote_api(payload)
        return self._local_mock(payload)

    def _call_remote_api(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            response = requests.post(self.url, json=payload, timeout=self.timeout)
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

    def _local_mock(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        ndc = str(payload.get("drug", {}).get("ndc", "")).lower()
        decision = {
            "coverage": "covered_no_restrictions",
            "message": "The drug appears covered without restrictions.",
            "details": payload,
        }

        if "pa" in ndc or "prior" in ndc:
            decision = {
                "coverage": "covered_pa_required",
                "message": "This drug requires prior authorization.",
                "details": payload,
            }
        elif "step" in ndc:
            decision = {
                "coverage": "covered_step_therapy",
                "message": "Step therapy is required before coverage is approved.",
                "details": payload,
            }
        elif "alternative" in ndc or "alternative" in str(payload.get("drug", {}).get("name", "")).lower():
            decision = {
                "coverage": "not_covered_alternative",
                "message": "An alternative drug is recommended for coverage.",
                "details": payload,
            }
        elif "gap" in ndc or "gap" in str(payload.get("drug", {}).get("name", "")).lower():
            decision = {
                "coverage": "coverage_gap",
                "message": "There is a coverage gap for this patient.",
                "details": payload,
            }
        elif "inactive" in ndc or "noactive" in ndc:
            decision = {
                "coverage": "no_active_coverage",
                "message": "The patient does not have active coverage for this request.",
                "details": payload,
            }

        return {
            "success": True,
            "mock": True,
            "payload": payload,
            "response": decision,
        }
