# InsureAI Backend API Reference

This directory houses the backend API endpoints powered by FastAPI.

## Endpoints Overview

### Chat & Document RAG
* **POST `/chat`**: Chat with policy assistant.
  * Request: `{"query": "string", "insurance_type": "string"}`
  * Response: `{"answer": "string", "sources": [], "route": "string", "confidence": "string", "degraded": bool}`
* **POST `/upload`**: Ingest policy PDF or text.
  * Request: multipart/form-data with `file`
  * Response: `{"status": "success", "filename": "string", "chunks": 12}`
* **GET `/history`**: Retrieve conversation history.
* **DELETE `/history`**: Reset conversational history.

### Claims Processing
* **POST `/claims/motor`**: File a motor insurance claim with photo damage analysis.
  * Request: Multipart Form Fields (`claimant_name`, `vehicle_number`, `vehicle_make`, `vehicle_model`, `year`, `incident_date`, `incident_description`, `policy_number`) and file `damage_photo`.
  * Response: Repair estimates breakdown, deductible calculations, and confidence levels.
* **POST `/claims/health`**: Submit a health claim.
  * Request: `HealthClaimRequest`
  * Response: Validated medical treatment/drug payouts.
* **POST `/claims/travel`**: Submit a travel claim.
  * Request: `TravelClaimRequest`
  * Response: Travel/flight delay/baggage loss analysis.

### Specialized Agents
* **POST `/fraud/analyze`**: Run fraud heuristics and LLM checks.
  * Request: `{"insurance_type": "motor", "claim_amount": 5000, ...}`
  * Response: Fraud score, verdict, reasons.
* **POST `/risk/profile`**: Evaluate lifestyle/health/demographics risk.
  * Request: `RiskProfileRequest`
  * Response: Risk category, score, suggested premium adjustments.
* **POST `/renewal/negotiate`**: Compare policies and suggest market alternatives.
  * Request: `RenewalRequest`
  * Response: Current premium comparison, savings, switch suggestions.
* **POST `/crop/analyze`**: Crop satellite weather indices payout calculation.
  * Request: `CropAnalyzeRequest`
  * Response: Crop status, rainfall/temp analysis, payout status.
* **GET `/crop/farmers`**: Demo farmer list.

### Orchestrator Automation
* **POST `/automation/run`**: Full agent automation pipeline trigger.
  * Request: `{"message": "string", "insurance_type": "string", "policy_number": "string"}`
  * Response: Intent, structured pipeline execution logs, final summary.
