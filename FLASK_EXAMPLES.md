# eBV Mock API - Flask with Swagger UI - Code Examples & Documentation

## Overview

The eBV (Electronic Benefits Verification) Mock API is built with **Flask** and **Flasgger** (Swagger UI). It provides a lightweight alternative to FastAPI with automatic Swagger documentation.

**Architecture:** Pure Python Flask + Flasgger (no FastAPI, no async overhead)

---

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

**Current Dependencies:**
- `flask>=2.3.0` - Lightweight web framework
- `flasgger>=0.9.7.1` - Automatic Swagger UI generation
- `requests>=2.32.0` - HTTP client
- `python-dotenv>=1.0.0` - Environment variables

### 2. Start the API Server
```bash
python app.py
```

Server runs at: `http://localhost:8000`

### 3. Access Swagger UI
- **Interactive Swagger UI:** http://localhost:8000/apidocs/
- **Swagger JSON:** http://localhost:8000/swagger.json

---

## Authentication

All protected endpoints require a **Bearer Token** in the Authorization header.

**Default Token:** `ebv-mock-token-123`

**Custom Token (Set via Environment):**
```bash
export BEARER_TOKEN="your-custom-token"
python app.py
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

### 2. Get Benefits Eligibility
```
POST http://localhost:8000/ebv/benefits
```

**Headers Required:**
- `Authorization: Bearer ebv-mock-token-123`
- `Content-Type: application/json`
- `x-scenario: covered_no_restrictions` (optional)

---

## Code Examples

### Python - Requests Library
```python
import requests
import json

BEARER_TOKEN = "ebv-mock-token-123"
API_URL = "http://localhost:8000/ebv/benefits"

headers = {
    "Authorization": f"Bearer {BEARER_TOKEN}",
    "x-scenario": "covered_no_restrictions",
    "Content-Type": "application/json"
}

payload = {
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
                        "drug": {"ndc": "00074153903"},
                        "quantity": "1",
                        "daysSupply": "28"
                    }
                ]
            }
        }
    }
}

response = requests.post(API_URL, headers=headers, json=payload)
result = response.json()
print(json.dumps(result, indent=2))

# Output:
# {
#   "eBVResponse": {
#     "benefitsSummary": {
#       "benefitVerificationStatus": "Complete",
#       "drug": {
#         "drugName": "HUMIRA",
#         "ndc": "00074153903"
#       },
#       "coverageStatus": "Covered",
#       "copay": "$50",
#       "priorAuthorizationRequired": "No",
#       "stepTherapyRequired": "No"
#     }
#   }
# }
```

---

### Python - All Scenarios
```python
import requests

def check_coverage(scenario, first_name, last_name, ndc):
    headers = {
        "Authorization": "Bearer ebv-mock-token-123",
        "x-scenario": scenario,
        "Content-Type": "application/json"
    }
    
    payload = {
        "eBVRequest": {
            "patient": {
                "channelType": "Web",
                "firstName": first_name,
                "lastName": last_name,
                "dateOfBirth": "1980-01-01"
            },
            "diagnosis": {
                "name": "Test Condition",
                "prescriptions": {
                    "prescription": [
                        {
                            "drug": {"ndc": ndc},
                            "quantity": "1",
                            "daysSupply": "28"
                        }
                    ]
                }
            }
        }
    }
    
    response = requests.post(
        "http://localhost:8000/ebv/benefits",
        headers=headers,
        json=payload
    )
    
    return response.json()

# Test all scenarios
scenarios = [
    {
        "scenario": "covered_no_restrictions",
        "patient": ("John", "Doe"),
        "ndc": "00074153903"
    },
    {
        "scenario": "covered_pa_required",
        "patient": ("Sarah", "Smith"),
        "ndc": "PA-0000"
    },
    {
        "scenario": "covered_step_therapy",
        "patient": ("Peter", "Lee"),
        "ndc": "STEP-1234"
    },
    {
        "scenario": "not_covered",
        "patient": ("Jane", "Brown"),
        "ndc": "EXP-9999"
    }
]

for test in scenarios:
    result = check_coverage(
        test["scenario"],
        test["patient"][0],
        test["patient"][1],
        test["ndc"]
    )
    
    summary = result["eBVResponse"]["benefitsSummary"]
    print(f"\n{test['scenario'].upper()}")
    print(f"  Patient: {test['patient'][0]} {test['patient'][1]}")
    print(f"  Coverage: {summary['coverageStatus']}")
    print(f"  Copay: {summary['copay']}")
    print(f"  Prior Auth: {summary['priorAuthorizationRequired']}")
    print(f"  Step Therapy: {summary['stepTherapyRequired']}")
```

---

### JavaScript - Fetch API
```javascript
const BEARER_TOKEN = 'ebv-mock-token-123';
const API_URL = 'http://localhost:8000/ebv/benefits';

async function checkBenefits(scenario = 'covered_no_restrictions') {
    const headers = {
        'Authorization': `Bearer ${BEARER_TOKEN}`,
        'x-scenario': scenario,
        'Content-Type': 'application/json'
    };
    
    const payload = {
        eBVRequest: {
            patient: {
                channelType: 'Web',
                firstName: 'Alex',
                lastName: 'Carter',
                dateOfBirth: '1985-03-12'
            },
            diagnosis: {
                name: 'Rheumatoid Arthritis (RA)',
                prescriptions: {
                    prescription: [
                        {
                            drug: { ndc: '00074153903' },
                            quantity: '1',
                            daysSupply: '28'
                        }
                    ]
                }
            }
        }
    };
    
    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(payload)
        });
        
        const result = await response.json();
        console.log(JSON.stringify(result, null, 2));
        return result;
    } catch (error) {
        console.error('Error:', error);
    }
}

// Run test
checkBenefits('covered_no_restrictions');
```

---

### JavaScript - All Scenarios
```javascript
const BEARER_TOKEN = 'ebv-mock-token-123';
const API_URL = 'http://localhost:8000/ebv/benefits';

async function testAllScenarios() {
    const scenarios = [
        {
            name: 'covered_no_restrictions',
            patient: { firstName: 'Alex', lastName: 'Carter' },
            ndc: '00074153903'
        },
        {
            name: 'covered_pa_required',
            patient: { firstName: 'Sarah', lastName: 'Smith' },
            ndc: 'PA-0000'
        },
        {
            name: 'covered_step_therapy',
            patient: { firstName: 'Peter', lastName: 'Lee' },
            ndc: 'STEP-1234'
        },
        {
            name: 'not_covered',
            patient: { firstName: 'Jane', lastName: 'Brown' },
            ndc: 'EXP-9999'
        }
    ];
    
    for (const scenario of scenarios) {
        const headers = {
            'Authorization': `Bearer ${BEARER_TOKEN}`,
            'x-scenario': scenario.name,
            'Content-Type': 'application/json'
        };
        
        const payload = {
            eBVRequest: {
                patient: {
                    channelType: 'Web',
                    firstName: scenario.patient.firstName,
                    lastName: scenario.patient.lastName,
                    dateOfBirth: '1980-01-01'
                },
                diagnosis: {
                    name: 'Test Condition',
                    prescriptions: {
                        prescription: [
                            {
                                drug: { ndc: scenario.ndc },
                                quantity: '1',
                                daysSupply: '28'
                            }
                        ]
                    }
                }
            }
        };
        
        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(payload)
            });
            
            const result = await response.json();
            const summary = result.eBVResponse.benefitsSummary;
            
            console.log(`\n${scenario.name.toUpperCase()}`);
            console.log(`  Patient: ${scenario.patient.firstName} ${scenario.patient.lastName}`);
            console.log(`  Coverage: ${summary.coverageStatus}`);
            console.log(`  Copay: ${summary.copay}`);
            console.log(`  Prior Auth: ${summary.priorAuthorizationRequired}`);
            console.log(`  Step Therapy: ${summary.stepTherapyRequired}`);
        } catch (error) {
            console.error(`Error testing ${scenario.name}:`, error);
        }
    }
}

// Run all tests
testAllScenarios();
```

---

### cURL - All Scenarios

#### Scenario 1: Covered (No Restrictions)
```bash
curl -X POST http://localhost:8000/ebv/benefits \
  -H "Authorization: Bearer ebv-mock-token-123" \
  -H "x-scenario: covered_no_restrictions" \
  -H "Content-Type: application/json" \
  -d '{
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

#### Scenario 2: Prior Authorization Required
```bash
curl -X POST http://localhost:8000/ebv/benefits \
  -H "Authorization: Bearer ebv-mock-token-123" \
  -H "x-scenario: covered_pa_required" \
  -H "Content-Type: application/json" \
  -d '{
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
            {"drug": {"ndc": "PA-0000"}, "quantity": "1", "daysSupply": "28"}
          ]
        }
      }
    }
  }'
```

#### Scenario 3: Step Therapy Required
```bash
curl -X POST http://localhost:8000/ebv/benefits \
  -H "Authorization: Bearer ebv-mock-token-123" \
  -H "x-scenario: covered_step_therapy" \
  -H "Content-Type: application/json" \
  -d '{
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
            {"drug": {"ndc": "STEP-1234"}, "quantity": "1", "daysSupply": "28"}
          ]
        }
      }
    }
  }'
```

#### Scenario 4: Not Covered
```bash
curl -X POST http://localhost:8000/ebv/benefits \
  -H "Authorization: Bearer ebv-mock-token-123" \
  -H "x-scenario: not_covered" \
  -H "Content-Type: application/json" \
  -d '{
    "eBVRequest": {
      "patient": {
        "channelType": "Web",
        "firstName": "Jane",
        "lastName": "Brown",
        "dateOfBirth": "1992-03-15"
      },
      "diagnosis": {
        "name": "Experimental Treatment",
        "prescriptions": {
          "prescription": [
            {"drug": {"ndc": "EXP-9999"}, "quantity": "1", "daysSupply": "28"}
          ]
        }
      }
    }
  }'
```

---

## Response Examples

### Covered (No Restrictions)
```json
{
  "eBVResponse": {
    "benefitsSummary": {
      "benefitVerificationStatus": "Complete",
      "copay": "$50",
      "coverageStatus": "Covered",
      "drug": {
        "drugName": "HUMIRA",
        "ndc": "00074153903"
      },
      "priorAuthorizationRequired": "No",
      "stepTherapyRequired": "No"
    }
  }
}
```

### Prior Authorization Required
```json
{
  "eBVResponse": {
    "benefitsSummary": {
      "benefitVerificationStatus": "Complete",
      "copay": "$100",
      "coverageStatus": "Covered",
      "drug": {
        "drugName": "SPECIALTY DRUG",
        "ndc": "PA-0000"
      },
      "priorAuthorizationRequired": "Yes",
      "stepTherapyRequired": "No"
    }
  }
}
```

### Step Therapy Required
```json
{
  "eBVResponse": {
    "benefitsSummary": {
      "benefitVerificationStatus": "Complete",
      "copay": "$35",
      "coverageStatus": "Covered",
      "drug": {
        "drugName": "STEP THERAPY DRUG",
        "ndc": "STEP-1234"
      },
      "priorAuthorizationRequired": "No",
      "stepTherapyRequired": "Yes"
    }
  }
}
```

### Not Covered
```json
{
  "eBVResponse": {
    "benefitsSummary": {
      "benefitVerificationStatus": "Complete",
      "copay": "N/A",
      "coverageStatus": "Not Covered",
      "drug": {
        "drugName": "EXPERIMENTAL DRUG",
        "ndc": "EXP-9999"
      },
      "priorAuthorizationRequired": "No",
      "stepTherapyRequired": "No"
    }
  }
}
```

---

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Invalid or missing bearer token"
}
```

### 400 Bad Request
```json
{
  "detail": "At least one prescription is required"
}
```

---

## Key Advantages of Flask Version

| Aspect | FastAPI | Flask |
|--------|---------|-------|
| Dependencies | Many (async, validation) | Minimal |
| Framework Size | Large | Lightweight |
| Swagger Support | Auto (built-in) | Manual (Flasgger) |
| Learning Curve | Steeper | Gentler |
| Performance | Async/faster | Sync/simpler |
| Code Complexity | More complex | Simpler |

---

## Files

- `app.py` - Main Flask application with Flasgger Swagger UI
- `mcp.py` - Natural Language Processing module (unchanged)
- `benefits_client.py` - Benefits API client (unchanged)
- `requirements.txt` - Updated: Flask + Flasgger only
- `POSTMAN_TESTING.md` - Original Postman guide
- `FLASK_EXAMPLES.md` - This file with code examples

---

## Summary

✅ **Removed:** FastAPI, Uvicorn, Pydantic models
✅ **Added:** Flask, Flasgger for Swagger UI
✅ **Kept:** Same API specification, same response format
✅ **Result:** Lightweight, simple, pure Python solution with automatic Swagger documentation
