# eBV Mock API - Postman Testing Guide

## Overview

The eBV (Electronic Benefits Verification) Mock API provides endpoints for checking drug coverage and benefits eligibility. The API follows the eBV specification and requires bearer token authentication.

## Quick Start

### 1. Start the API Server
```bash
pip install -r requirements.txt
python app.py
```

The server will start at `http://localhost:8000`

### 2. Access API Documentation
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## Authentication

All protected endpoints require a **Bearer Token** in the Authorization header.

**Default Token:** `ebv-mock-token-123`

To use a custom token, set the environment variable:
```bash
export BEARER_TOKEN="your-custom-token"
```

**Header Format:**
```
Authorization: Bearer ebv-mock-token-123
```

---

## API Endpoints

### 1. Health Check (No Auth Required)
```
GET http://localhost:8000/health
```

**Response:**
```json
{
    "status": "healthy",
    "timestamp": "2026-05-06T00:00:00Z"
}
```

---

### 2. Get Benefits Eligibility (Primary Endpoint)
```
POST http://localhost:8000/ebv/benefits
```

**Headers:**
```
Authorization: Bearer ebv-mock-token-123
x-scenario: covered_no_restrictions
Content-Type: application/json
```

**Request Body:**
```json
{
  "eBVRequest": {
    "healthCareProfessional": {
      "npi": "1083773444"
    },
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
          {
            "drug": {
              "ndc": "00074153903"
            },
            "quantity": "1",
            "daysSupply": "28"
          }
        ]
      }
    }
  }
}
```

**Response (200 OK):**
```json
{
  "eBVResponse": {
    "benefitsSummary": {
      "benefitVerificationStatus": "Complete",
      "drug": {
        "drugName": "HUMIRA",
        "ndc": "00074153903"
      },
      "coverageStatus": "Covered",
      "copay": "$50",
      "priorAuthorizationRequired": "No",
      "stepTherapyRequired": "No"
    }
  }
}
```

---

## Scenario Testing

The `x-scenario` header controls the mock response behavior. The following scenarios are supported:

### Scenario 1: Covered (No Restrictions)
```
x-scenario: covered_no_restrictions
```

**Response:**
```json
{
  "eBVResponse": {
    "benefitsSummary": {
      "benefitVerificationStatus": "Complete",
      "drug": {"drugName": "HUMIRA", "ndc": "00074153903"},
      "coverageStatus": "Covered",
      "copay": "$50",
      "priorAuthorizationRequired": "No",
      "stepTherapyRequired": "No"
    }
  }
}
```

---

### Scenario 2: Prior Authorization Required
```
x-scenario: covered_pa_required
```

**Response:**
```json
{
  "eBVResponse": {
    "benefitsSummary": {
      "benefitVerificationStatus": "Complete",
      "drug": {"drugName": "SPECIALTY DRUG", "ndc": "PA-0000"},
      "coverageStatus": "Covered",
      "copay": "$100",
      "priorAuthorizationRequired": "Yes",
      "stepTherapyRequired": "No"
    }
  }
}
```

---

### Scenario 3: Step Therapy Required
```
x-scenario: covered_step_therapy
```

**Response:**
```json
{
  "eBVResponse": {
    "benefitsSummary": {
      "benefitVerificationStatus": "Complete",
      "drug": {"drugName": "STEP THERAPY DRUG", "ndc": "STEP-1234"},
      "coverageStatus": "Covered",
      "copay": "$35",
      "priorAuthorizationRequired": "No",
      "stepTherapyRequired": "Yes"
    }
  }
}
```

---

### Scenario 4: Not Covered
```
x-scenario: not_covered
```

**Response:**
```json
{
  "eBVResponse": {
    "benefitsSummary": {
      "benefitVerificationStatus": "Complete",
      "drug": {"drugName": "EXPERIMENTAL DRUG", "ndc": "EXP-9999"},
      "coverageStatus": "Not Covered",
      "copay": "N/A",
      "priorAuthorizationRequired": "No",
      "stepTherapyRequired": "No"
    }
  }
}
```

---

## cURL Examples

### Test 1: Covered (No Restrictions)
```bash
curl --location 'http://localhost:8000/ebv/benefits' \
  --header 'x-scenario: covered_no_restrictions' \
  --header 'Content-Type: application/json' \
  --header 'Authorization: Bearer ebv-mock-token-123' \
  --data '{
    "eBVRequest": {
      "healthCareProfessional": {
        "npi": "1083773444"
      },
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
            {
              "drug": {
                "ndc": "00074153903"
              },
              "quantity": "1",
              "daysSupply": "28"
            }
          ]
        }
      }
    }
  }'
```

---

### Test 2: Prior Authorization Required
```bash
curl --location 'http://localhost:8000/ebv/benefits' \
  --header 'x-scenario: covered_pa_required' \
  --header 'Content-Type: application/json' \
  --header 'Authorization: Bearer ebv-mock-token-123' \
  --data '{
    "eBVRequest": {
      "patient": {
        "channelType": "Web",
        "firstName": "Sarah",
        "lastName": "Smith",
        "dateOfBirth": "1975-10-21"
      },
      "diagnosis": {
        "name": "Chronic Disease",
        "prescriptions": {
          "prescription": [
            {
              "drug": {
                "ndc": "PA-0000"
              },
              "quantity": "1",
              "daysSupply": "28"
            }
          ]
        }
      }
    }
  }'
```

---

### Test 3: Step Therapy Required
```bash
curl --location 'http://localhost:8000/ebv/benefits' \
  --header 'x-scenario: covered_step_therapy' \
  --header 'Content-Type: application/json' \
  --header 'Authorization: Bearer ebv-mock-token-123' \
  --data '{
    "eBVRequest": {
      "patient": {
        "channelType": "Web",
        "firstName": "Peter",
        "lastName": "Lee",
        "dateOfBirth": "1990-06-15"
      },
      "diagnosis": {
        "name": "Condition Requiring Step Therapy",
        "prescriptions": {
          "prescription": [
            {
              "drug": {
                "ndc": "STEP-1234"
              },
              "quantity": "1",
              "daysSupply": "28"
            }
          ]
        }
      }
    }
  }'
```

---

## Error Responses

### 401 Unauthorized (Missing/Invalid Token)
```
Authorization: Bearer invalid-token
```

**Response:**
```json
{
  "detail": "Invalid or missing bearer token"
}
```

---

### 400 Bad Request (Missing Prescriptions)
```json
{
  "detail": "At least one prescription is required"
}
```

---

## Environment Variables

Create a `.env` file in the project root:

```env
# Bearer token for API authentication
BEARER_TOKEN=ebv-mock-token-123

# Optional: Remote benefits API URL (if not set, uses local mock)
BENEFITS_API_URL=http://your-benefits-api.com/check

# Optional: API timeout in seconds
BENEFITS_API_TIMEOUT=15
```

---

## Postman Collection Setup

### Import Environment Variables
Create a Postman environment with:
```json
{
  "token": "ebv-mock-token-123",
  "base_url": "http://localhost:8000",
  "scenario": "covered_no_restrictions"
}
```

### Use in Requests
```
Authorization: Bearer {{token}}
x-scenario: {{scenario}}
URL: {{base_url}}/ebv/benefits
```

---

## Request/Response Schema

### eBVRequest Schema
- **healthCareProfessional** (optional)
  - `npi`: National Provider Identifier (10 digits)
- **patient** (required)
  - `channelType`: Channel type (Web, Mobile, etc.)
  - `firstName`: Patient first name
  - `lastName`: Patient last name
  - `dateOfBirth`: Date of birth (YYYY-MM-DD)
- **diagnosis** (required)
  - `name`: Diagnosis name
  - `prescriptions.prescription[]`: Array of prescriptions
    - `drug.ndc`: National Drug Code
    - `quantity`: Drug quantity (default: "1")
    - `daysSupply`: Days supply (default: "28")

### eBVResponse Schema
- **eBVResponse**
  - **benefitsSummary**
    - `benefitVerificationStatus`: Verification status
    - **drug**
      - `drugName`: Drug name from NDC
      - `ndc`: National Drug Code
    - `coverageStatus`: Coverage status (Covered, Not Covered, etc.)
    - `copay`: Copay amount
    - `priorAuthorizationRequired`: Yes/No
    - `stepTherapyRequired`: Yes/No

---

## Testing Checklist

- [ ] Health check endpoint responds with 200
- [ ] Covered (no restrictions) scenario returns correct response
- [ ] Prior authorization scenario returns correct response
- [ ] Step therapy scenario returns correct response
- [ ] Not covered scenario returns correct response
- [ ] Missing bearer token returns 401
- [ ] Invalid bearer token returns 401
- [ ] Missing prescriptions returns 400
- [ ] Different NDCs trigger correct scenarios
- [ ] Multiple prescriptions are supported

---

## Notes

- The MCP layer is preserved but not used in the `/ebv/benefits` endpoint
- The API supports both scenario-based and NDC-based routing
- All responses include the `eBVResponse` wrapper as per specification
- Timestamps are in ISO 8601 format
- Drug names are determined by NDC or scenario
