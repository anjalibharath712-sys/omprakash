import json
import os
import re
from typing import Any, Dict, List, Optional

try:
    from langchain.chat_models import ChatOpenAI
    from langchain.chains import LLMChain
    from langchain.prompts import PromptTemplate
except ImportError:
    ChatOpenAI = None
    LLMChain = None
    PromptTemplate = None

from benefits_client import BenefitsClient

REQUIRED_PATIENT_FIELDS = ["first_name", "last_name", "dob", "gender", "member_id"]


class BenefitMCP:
    def __init__(self) -> None:
        self.client = BenefitsClient()
        self.llm = self._create_llm()
        self.prompt_template = self._build_prompt_template()

    def _create_llm(self) -> Optional[Any]:
        if os.getenv("OPENAI_API_KEY") and ChatOpenAI is not None:
            try:
                return ChatOpenAI(temperature=0, model_name=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"))
            except Exception:
                return None
        return None

    def _build_prompt_template(self) -> Optional[PromptTemplate]:
        if PromptTemplate is None:
            return None

        prompt_text = (
            "You are an assistant that converts free-form benefit eligibility requests into a structured payload. "
            "The user may provide NPI, patient details, and drug NDC. "
            "Return only a valid JSON object with keys: npi, patient, drug, payer_id, group_id, place_of_service. "
            "If you cannot find a value, omit that key. "
            "Example response:\n"
            "{\n"
            "  \"npi\": \"1234567890\",\n"
            "  \"patient\": {\"first_name\": \"Jane\", \"last_name\": \"Doe\", \"dob\": \"1980-01-01\", \"gender\": \"female\", \"member_id\": \"ABC123\"},\n"
            "  \"drug\": {\"ndc\": \"12345-6789\", \"name\": \"drug name\"}\n"
            "}\n"
        )
        return PromptTemplate(input_variables=["user_text"], template=prompt_text)

    def parse_nlp_payload(self, user_text: str) -> Dict[str, Any]:
        if self.llm and self.prompt_template:
            try:
                chain = LLMChain(llm=self.llm, prompt=self.prompt_template)
                raw = chain.run(user_text=user_text)
                parsed = self._safe_parse_json(raw)
                if parsed:
                    return parsed
            except Exception:
                pass

        return self._fallback_parse(user_text)

    def _safe_parse_json(self, raw_text: str) -> Dict[str, Any]:
        text = raw_text.strip()
        if text.startswith("```"):
            text = text.strip("` \n")
        text = re.sub(r"^.*?\{", "{", text, flags=re.S)
        try:
            return json.loads(text)
        except ValueError:
            try:
                json_text = re.search(r"\{.*\}", text, flags=re.S)
                if json_text:
                    return json.loads(json_text.group(0))
            except ValueError:
                pass
        return {}

    def _fallback_parse(self, text: str) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        npi = self._search(r"\bNPI\s*[:\- ]*([0-9]{10})\b", text)
        ndc = self._search(r"\bNDC\s*[:\- ]*([0-9]{4,5}-?[0-9]{3,4})\b", text)
        member_id = self._search(r"\b(member id|member number|member#|member No\.?|member)\s*[:\- ]*([A-Za-z0-9\-]+)\b", text, group=2)
        dob = self._search(r"\b(DOB|date of birth)\s*[:\- ]*([0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9]{2}/[0-9]{2}/[0-9]{4})\b", text, group=2)
        first_name = self._search(r"patient\s+([A-Z][a-z]+)\s+([A-Z][a-z]+)" , text, group=1)
        last_name = self._search(r"patient\s+([A-Z][a-z]+)\s+([A-Z][a-z]+)" , text, group=2)
        gender = self._search(r"\b(male|female|other|m)\b", text, flags=re.I)

        if npi:
            result["npi"] = npi
        patient: Dict[str, str] = {}
        if first_name:
            patient["first_name"] = first_name
        if last_name:
            patient["last_name"] = last_name
        if dob:
            patient["dob"] = dob.replace('/', '-')
        if gender:
            patient["gender"] = gender.lower()
        if member_id:
            patient["member_id"] = member_id
        if patient:
            result["patient"] = patient

        drug: Dict[str, str] = {}
        if ndc:
            drug["ndc"] = ndc
        name_match = self._search(
            r"(?:drug|medication|product)\s+([A-Za-z0-9 \-]+)", text, flags=re.I
        )
        if name_match and ndc is None:
            drug["name"] = name_match.strip()
        if drug:
            result["drug"] = drug

        payer_id = self._search(r"\b(payer id|payer)\s*[:\- ]*([A-Za-z0-9\-]+)\b", text, group=2)
        if payer_id:
            result["payer_id"] = payer_id

        return result

    def _search(self, pattern: str, text: str, group: int = 1, flags: int = 0) -> Optional[str]:
        match = re.search(pattern, text, flags)
        if not match:
            return None
        return match.group(group).strip()

    def merge_payloads(self, base: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
        merged = dict(base)
        for key, value in incoming.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = self.merge_payloads(merged.get(key, {}), value)
            else:
                merged[key] = value
        return merged

    def validate_payload(self, payload: Dict[str, Any]) -> List[str]:
        missing: List[str] = []
        if not payload.get("npi"):
            missing.append("npi")

        patient = payload.get("patient", {})
        if not isinstance(patient, dict):
            missing.extend([f"patient.{field}" for field in REQUIRED_PATIENT_FIELDS])
        else:
            for field_name in REQUIRED_PATIENT_FIELDS:
                if not patient.get(field_name):
                    missing.append(f"patient.{field_name}")

        drug = payload.get("drug", {})
        if not isinstance(drug, dict) or not drug.get("ndc"):
            missing.append("drug.ndc")

        return missing

    def handle_text_input(self, text: str, current_payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if current_payload is None:
            current_payload = {}

        incoming_payload = self.parse_nlp_payload(text)
        merged_payload = self.merge_payloads(current_payload, incoming_payload)
        missing_fields = self.validate_payload(merged_payload)

        if missing_fields:
            message = (
                "I need a few more values before checking eligibility. "
                "Please provide the missing fields listed below."
            )
            return {
                "status": "missing_fields",
                "message": message,
                "missing_fields": missing_fields,
                "payload": merged_payload,
            }

        api_result = self.client.check_eligibility(merged_payload)
        return {
            "status": "success",
            "message": "The payload is complete and the eligibility check was executed.",
            "payload": merged_payload,
            "api_result": api_result,
        }
