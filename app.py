import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Header, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from mcp import BenefitMCP

app = FastAPI(
    title="eBV Benefits Eligibility Mock API",
    description="Mock API for electronic benefits verification",
    version="1.0.0"
)

mcp = BenefitMCP()

# Mock bearer token for authentication
VALID_TOKEN = os.getenv("BEARER_TOKEN", "ebv-mock-token-123")


# ==================== Request Models ====================

class Drug(BaseModel):
    ndc: str = Field(..., description="National Drug Code")


class Prescription(BaseModel):
    drug: Drug
    quantity: str = Field(default="1", description="Drug quantity")
    daysSupply: str = Field(default="28", description="Days supply")


class Prescriptions(BaseModel):
    prescription: List[Prescription]


class Diagnosis(BaseModel):
    name: str = Field(..., description="Diagnosis name")
    prescriptions: Prescriptions


class Patient(BaseModel):
    channelType: str = Field(default="Web", description="Channel type (Web, Mobile, etc.)")
    firstName: str = Field(..., description="Patient first name")
    lastName: str = Field(..., description="Patient last name")
    dateOfBirth: str = Field(..., description="Date of birth (YYYY-MM-DD)")


class HealthCareProfessional(BaseModel):
    npi: str = Field(..., description="National Provider Identifier")


class EBVRequest(BaseModel):
    healthCareProfessional: Optional[HealthCareProfessional] = None
    patient: Patient
    diagnosis: Diagnosis


class BenefitsRequest(BaseModel):
    eBVRequest: EBVRequest


# ==================== Response Models ====================

class DrugResponse(BaseModel):
    drugName: str
    ndc: str


class BenefitsSummary(BaseModel):
    benefitVerificationStatus: str = Field(default="Complete", description="Status of verification")
    drug: DrugResponse
    coverageStatus: str = Field(description="Coverage status (Covered, Not Covered, etc.)")
    copay: str = Field(description="Copay amount")
    priorAuthorizationRequired: str = Field(description="Prior auth required (Yes/No)")
    stepTherapyRequired: str = Field(description="Step therapy required (Yes/No)")


class EBVResponse(BaseModel):
    benefitsSummary: BenefitsSummary


class BenefitsResponse(BaseModel):
    eBVResponse: EBVResponse


# ==================== Scenario Handlers ====================

SCENARIO_RESPONSES = {
    "covered_no_restrictions": {
        "drug_name": "HUMIRA",
        "coverage": "Covered",
        "copay": "$50",
        "prior_auth": "No",
        "step_therapy": "No"
    },
    "covered_pa_required": {
        "drug_name": "SPECIALTY DRUG",
        "coverage": "Covered",
        "copay": "$100",
        "prior_auth": "Yes",
        "step_therapy": "No"
    },
    "covered_step_therapy": {
        "drug_name": "STEP THERAPY DRUG",
        "coverage": "Covered",
        "copay": "$35",
        "prior_auth": "No",
        "step_therapy": "Yes"
    },
    "not_covered": {
        "drug_name": "EXPERIMENTAL DRUG",
        "coverage": "Not Covered",
        "copay": "N/A",
        "prior_auth": "No",
        "step_therapy": "No"
    }
}


def get_drug_name_from_ndc(ndc: str) -> str:
    """Get drug name based on NDC or scenario"""
    ndc_lower = ndc.lower()
    if "humira" in ndc_lower or "00074" in ndc_lower:
        return "HUMIRA"
    elif "pa" in ndc_lower or "prior" in ndc_lower:
        return "SPECIALTY DRUG"
    elif "step" in ndc_lower:
        return "STEP THERAPY DRUG"
    else:
        return "GENERIC DRUG"


def get_response_for_scenario(scenario: str, ndc: str) -> Dict[str, Any]:
    """Get mock response based on scenario or NDC"""
    scenario_lower = scenario.lower() if scenario else "covered_no_restrictions"
    
    if scenario_lower in SCENARIO_RESPONSES:
        return SCENARIO_RESPONSES[scenario_lower]
    
    # Fallback: determine from NDC
    ndc_lower = ndc.lower()
    if "pa-" in ndc_lower or "prior" in ndc_lower:
        return SCENARIO_RESPONSES["covered_pa_required"]
    elif "step-" in ndc_lower:
        return SCENARIO_RESPONSES["covered_step_therapy"]
    else:
        return SCENARIO_RESPONSES["covered_no_restrictions"]


def verify_bearer_token(authorization: Optional[str]) -> bool:
    """Verify bearer token"""
    if not authorization:
        return False
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return False
    return parts[1] == VALID_TOKEN


# ==================== Endpoints ====================

@app.get("/", tags=["Health"])
def read_root():
    """Root endpoint - API status"""
    return {
        "status": "healthy",
        "service": "eBV Benefits Eligibility Mock API",
        "version": "1.0.0",
        "documentation": "/docs"
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": "2026-05-06T00:00:00Z"
    }


@app.post("/ebv/benefits", response_model=BenefitsResponse, tags=["Benefits"])
def get_benefits_eligibility(
    request: BenefitsRequest,
    authorization: Optional[str] = Header(None),
    x_scenario: Optional[str] = Header(None)
):
    """
    Check benefits eligibility for a patient's prescription.
    
    **Authentication:** Bearer token in Authorization header
    
    **Headers:**
    - Authorization: Bearer <token> (required)
    - x-scenario: Scenario type (optional) - covered_no_restrictions, covered_pa_required, covered_step_therapy, not_covered
    
    **Request Body:** eBVRequest with patient, provider, and diagnosis information
    
    **Response:** eBVResponse with benefits summary
    
    **Example:**
    ```bash
    curl --location 'http://localhost:8000/ebv/benefits' \\
      --header 'Authorization: Bearer ebv-mock-token-123' \\
      --header 'x-scenario: covered_no_restrictions' \\
      --header 'Content-Type: application/json' \\
      --data '{
        "eBVRequest": {
          "healthCareProfessional": {"npi": "1083773444"},
          "patient": {
            "channelType": "Web",
            "firstName": "Alex",
            "lastName": "Carter",
            "dateOfBirth": "1985-03-12"
          },
          "diagnosis": {
            "name": "Rheumatoid Arthritis (RA)",
            "prescriptions": {
              "prescription": [
                {"drug": {"ndc": "00074153903"}, "quantity": "1", "daysSupply": "28"}
              ]
            }
          }
        }
      }'
    ```
    """
    
    # Verify authorization
    if not verify_bearer_token(authorization):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract data from request
    patient = request.eBVRequest.patient
    prescriptions = request.eBVRequest.diagnosis.prescriptions.prescription
    
    if not prescriptions:
        raise HTTPException(
            status_code=400,
            detail="At least one prescription is required"
        )
    
    # Process first prescription
    first_prescription = prescriptions[0]
    ndc = first_prescription.drug.ndc
    
    # Get scenario response
    scenario_response = get_response_for_scenario(x_scenario, ndc)
    drug_name = scenario_response.get("drug_name") or get_drug_name_from_ndc(ndc)
    
    # Build response
    benefits_summary = BenefitsSummary(
        benefitVerificationStatus="Complete",
        drug=DrugResponse(
            drugName=drug_name,
            ndc=ndc
        ),
        coverageStatus=scenario_response.get("coverage", "Covered"),
        copay=scenario_response.get("copay", "$50"),
        priorAuthorizationRequired=scenario_response.get("prior_auth", "No"),
        stepTherapyRequired=scenario_response.get("step_therapy", "No")
    )
    
    response = BenefitsResponse(
        eBVResponse=EBVResponse(
            benefitsSummary=benefits_summary
        )
    )
    
    return response


@app.post("/ebv/benefits/nlp", tags=["Benefits"])
def get_benefits_eligibility_nlp(
    text: str,
    authorization: Optional[str] = Header(None),
    current_payload: Optional[Dict[str, Any]] = None
):
    """
    Check benefits eligibility using natural language processing.
    
    This endpoint accepts free-form text and uses MCP to parse it into structured data.
    
    **Authentication:** Bearer token in Authorization header
    """
    
    # Verify authorization
    if not verify_bearer_token(authorization):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not text or not text.strip():
        raise HTTPException(
            status_code=400,
            detail="Text field cannot be empty"
        )
    
    # Use MCP to parse text
    result = mcp.handle_text_input(text, current_payload or {})
    
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
