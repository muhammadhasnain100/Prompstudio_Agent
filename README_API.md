# RiverGen PSA API

FastAPI endpoint for intent classification, governance, planning, visualization, and analysis.

## Quick Start

1. **Start the server:**
   ```bash
   python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Access Swagger UI:**
   - Open your browser and go to: `http://localhost:8000/docs`
   - The Swagger UI will show all available endpoints with interactive testing

3. **Access ReDoc:**
   - Alternative documentation: `http://localhost:8000/redoc`

## API Endpoints

### POST `/analyze`
Main endpoint that processes requests through all agents:
- Intent Classification
- Governance Application
- Execution Planning
- Visualization Generation (if requested)
- AI Analysis

**Request Body:** JSON matching `RequestModel` schema
**Response:** JSON matching `ResponseModel` schema

### POST `/analyze-raw`
Same as `/analyze` but returns raw response without strict validation (useful for debugging).

### GET `/health`
Health check endpoint.

### GET `/`
Root endpoint with API information.

## Environment Variables

- `GEMINI_API_KEY`: Your Gemini API key (optional, defaults to hardcoded key)

## Testing with Swagger

1. Start the server
2. Navigate to `http://localhost:8000/docs`
3. Click on `/analyze` endpoint
4. Click "Try it out"
5. Use the example request body provided in the schema
6. Click "Execute" to test

## Example Request

See the `RequestModel` schema in Swagger UI for a complete example with all fields.

