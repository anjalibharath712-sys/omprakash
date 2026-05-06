import os
from flask import Flask, request, jsonify
from flasgger import Flasgger
from benefits_client import BenefitsClient

app = Flask(__name__)
swagger = Flasgger(app)

client = BenefitsClient()


# ==================== Endpoints ====================

@app.route('/', methods=['GET'])
def root():
    """Root endpoint - API information"""
    return jsonify({
        "status": "healthy",
        "service": "eBV Benefits Eligibility Mock API",
        "version": "1.0.0",
        "documentation": "/apidocs"
    })


@app.route('/health', methods=['GET'])
def health():
    """
    Health check endpoint
    ---
    tags:
      - Health
    responses:
      200:
        description: API is healthy
        schema:
          type: object
          properties:
            status:
              type: string
              example: "healthy"
            timestamp:
              type: string
              example: "2026-05-06T00:00:00Z"
    """
    return jsonify({
        "status": "healthy",
        "timestamp": "2026-05-06T00:00:00Z"
    })


@app.route('/ebv/benefits', methods=['POST'])
def get_benefits_eligibility():
    """
    Proxy the incoming request to the external eBV benefits API.
    ---
    tags:
      - Benefits
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: "Bearer token for the external eBV API"
      - name: x-scenario
        in: header
        type: string
        required: false
        description: "Scenario type forwarded to the external API"
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            eBVRequest:
              type: object
              required:
                - patient
                - diagnosis
              properties:
                healthCareProfessional:
                  type: object
                  properties:
                    npi:
                      type: string
                      example: "1083773444"
                patient:
                  type: object
                  required:
                    - firstName
                    - lastName
                    - dateOfBirth
                  properties:
                    channelType:
                      type: string
                      example: "Web"
                    firstName:
                      type: string
                      example: "Alex"
                    lastName:
                      type: string
                      example: "Carter"
                    dateOfBirth:
                      type: string
                      example: "1985-03-12"
                diagnosis:
                  type: object
                  required:
                    - name
                    - prescriptions
                  properties:
                    name:
                      type: string
                      example: "Rheumatoid Arthritis (RA)"
                    prescriptions:
                      type: object
                      properties:
                        prescription:
                          type: array
                          items:
                            type: object
                            properties:
                              drug:
                                type: object
                                properties:
                                  ndc:
                                    type: string
                                    example: "00074153903"
                              quantity:
                                type: string
                                example: "1"
                              daysSupply:
                                type: string
                                example: "28"
    responses:
      200:
        description: Forwarded response from external API
      400:
        description: Bad request (invalid request format)
      401:
        description: Missing Authorization header
      502:
        description: External API error
    """
    data = request.get_json()
    if not data or 'eBVRequest' not in data:
        return jsonify({"detail": "Invalid request format"}), 400

    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"detail": "Missing Authorization header"}), 401

    external_headers = {
        'Authorization': auth_header,
        'Content-Type': 'application/json'
    }
    scenario = request.headers.get('x-scenario')
    if scenario:
        external_headers['x-scenario'] = scenario

    result = client.check_eligibility(data, headers=external_headers)
    if not result.get('success'):
        return jsonify({
            'detail': result.get('error', 'External API error'),
            'url': result.get('url')
        }), 502

    return jsonify(result.get('body')), result.get('status_code', 200)


# ==================== Error Handlers ====================

@app.errorhandler(404)
def not_found(e):
    return jsonify({"detail": "Endpoint not found"}), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"detail": "Method not allowed"}), 405


@app.errorhandler(500)
def internal_error(e):
    return jsonify({"detail": "Internal server error"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)
