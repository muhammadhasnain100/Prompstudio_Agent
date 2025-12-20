# RiverGen PSA - Prompt-to-SQL Analysis API

A FastAPI-based AI-powered system for intelligent SQL planning, governance enforcement, and execution plan generation. This system processes natural language prompts and generates optimized database queries (SQL/NoSQL) with built-in security and governance policies using Groq LLM.

## 🚀 Features

- **Single Unified Endpoint**: One `/analyze` endpoint that handles the entire analysis pipeline
- **Intent Classification**: Automatically identifies user intent from natural language prompts
- **Data Governance**: Applies row-level security (RLS) and column masking rules
- **Execution Planning**: Generates database-specific commands (SQL/NoSQL) based on intent and governance
- **Visualization Recommendations**: Suggests appropriate charts and visualizations based on query results
- **AI Analysis**: Provides confidence scores, reasoning steps, and suggestions for generated plans
- **Multi-Database Support**: Supports PostgreSQL, MySQL, MongoDB, Cassandra, Redis, DynamoDB, Elasticsearch, and more
- **Asynchronous Processing**: Fully async FastAPI application for concurrent request handling
- **Security Features**: Rate limiting, security headers, CORS protection
- **Caching**: Built-in response caching with TTL
- **Retry Logic**: Automatic retry mechanism with exponential backoff (3 attempts)
- **Comprehensive Logging**: Structured logging for debugging and monitoring

## 📋 Prerequisites

- Python 3.8 or higher
- Groq API key ([Get one here](https://console.groq.com/))

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd rivergen-psa
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Create a `.env` file in the project root:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   LOG_LEVEL=INFO
   RATE_LIMIT_PER_MINUTE=60
   ENABLE_CACHE=true
   ```

## 🏃 Quick Start

### Running the FastAPI Server

1. **Start the server:**
   ```bash
   python app.py
   ```
   
   Or using uvicorn directly:
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Access the API documentation:**
   - **Swagger UI**: http://localhost:8000/docs
   - **ReDoc**: http://localhost:8000/redoc
   - **OpenAPI Schema**: http://localhost:8000/openapi.json

3. **Test the API:**
   - Use the interactive Swagger UI to test endpoints
   - Or use curl/Postman with the example request from `request_example.json`

## 📚 Project Structure

```
rivergen-psa/
├── app.py                  # FastAPI application (main entry point)
│                           # - FastAPI app initialization
│                           # - Request/Response models
│                           # - API endpoints (/analyze, /health)
│                           # - Exception handlers
│
├── schema/                 # Schema definitions
│   ├── __init__.py
│   ├── agent.py           # Response schemas (ExecutionResponse, AIMetadata, etc.)
│   └── prompts.py         # Prompt engineering functions
│                           # - getdatabase() - Database type detection
│                           # - get_system_prompt() - System prompt generation
│                           # - prepare_prompt() - User prompt preparation
│
├── services/               # Service layer
│   ├── __init__.py
│   └── ai.py              # AI service (Groq LLM integration)
│                           # - AIService class
│                           # - Async response generation
│                           # - Retry logic with exponential backoff
│
├── middleware.py           # FastAPI middleware
│                           # - RateLimitMiddleware (sliding window)
│                           # - SecurityHeadersMiddleware
│
├── utils.py                # Utility functions
│                           # - retry_on_failure decorator
│                           # - Caching functions (TTL cache)
│                           # - Logging setup
│
├── requirements.txt        # Python dependencies
├── request_example.json    # Example API request JSON
├── .gitignore             # Git ignore rules
└── README.md              # This file
```

## 🔌 API Endpoints

### POST `/analyze`

Main endpoint that processes user requests and generates execution plans with governance enforcement.

**Request Body:**
```json
{
  "request_id": "req-12345",
  "execution_id": "exec-67890",
  "user_context": {
    "user_id": 1,
    "workspace_id": 5,
    "organization_id": 10,
    "roles": ["analyst"],
    "permissions": ["read:customers"],
    "attributes": {
      "assigned_region": "US-WEST"
    }
  },
  "user_prompt": "Show me top 10 customers by revenue this quarter",
  "data_sources": [
    {
      "data_source_id": 1,
      "name": "PostgreSQL Production",
      "type": "postgresql",
      "schemas": [...],
      "governance_policies": {
        "row_level_security": {...},
        "column_masking": {...}
      }
    }
  ],
  "ai_model": "meta-llama/llama-4-scout-17b-16e-instruct",
  "temperature": 0.1,
  "include_visualization": true,
  "selected_schema_names": ["public"],
  "execution_context": {
    "max_rows": 1000,
    "timeout_seconds": 30
  }
}
```

**Response:**
```json
{
  "request_id": "req-12345",
  "execution_id": "exec-67890",
  "plan_id": "plan-abc123",
  "status": "success",
  "timestamp": "2025-12-20T19:53:31.908946",
  "intent_type": "aggregate",
  "intent_summary": "Show top 10 customers by revenue this quarter",
  "execution_plan": {
    "strategy": "pushdown",
    "type": "sql_query",
    "operations": [...]
  },
  "visualization": [
    {
      "type": "table",
      "title": "Top 10 Customers by Revenue",
      "x_axis": "",
      "y_axis": "",
      "config": {},
      "is_primary": true
    }
  ],
  "ai_metadata": {
    "confidence": 95,
    "confidence_score": 0.95,
    "explanation": "...",
    "reasoning_steps": [...],
    "model": "meta-llama/llama-4-scout-17b-16e-instruct",
    "input_tokens": 7472,
    "output_tokens": 694,
    "generation_time_ms": 2273
  },
  "suggestions": [...]
}
```

### GET `/health`

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "rivergen-psa"
}
```

## 🔧 Configuration

### Supported AI Models

- `meta-llama/llama-4-scout-17b-16e-instruct` (required) - Groq-optimized Llama model

### Supported Database Types

**SQL Databases:**
- PostgreSQL
- MySQL
- MariaDB
- SQL Server
- Oracle

**Cloud Warehouse:**
- Snowflake
- BigQuery
- Redshift
- Databricks

**NoSQL Databases:**
- MongoDB
- Cassandra
- Redis
- DynamoDB
- Elasticsearch

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GROQ_API_KEY` | Your Groq API key | Yes | - |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No | INFO |
| `RATE_LIMIT_PER_MINUTE` | Rate limit per IP address | No | 60 |
| `ENABLE_CACHE` | Enable response caching | No | true |
| `ALLOWED_ORIGINS` | CORS allowed origins (comma-separated) | No | localhost origins |

## 🧪 Testing

### Using Swagger UI

1. Start the server: `python app.py`
2. Navigate to http://localhost:8000/docs
3. Click on `/analyze` endpoint
4. Click "Try it out"
5. Use the example request body from `request_example.json` or modify it
6. Click "Execute"

### Using cURL

```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d @request_example.json
```

## 🔒 Security Features

- **Rate Limiting**: Sliding window rate limiter (60 requests/minute per IP by default)
- **Security Headers**: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, CSP
- **CORS Protection**: Configurable CORS with localhost allowed by default
- **Input Validation**: Comprehensive Pydantic validation for all request fields
- **Row-Level Security**: Automatically applied based on user context
- **Column Masking**: PII data masking according to governance policies
- **API Key Protection**: Environment variable-based API key management

## 🐛 Error Handling

The API includes comprehensive error handling:

- **400 Bad Request**: Invalid request data or validation errors
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Unexpected errors with error IDs for tracking
- **503 Service Unavailable**: AI service temporarily unavailable (after retries)

All errors include structured error messages and error IDs for debugging.

## 🔄 Retry Logic

The AI service includes automatic retry logic:
- **Max Retries**: 3 attempts
- **Exponential Backoff**: 1s, 2s, 4s delays
- **Retryable Errors**: Rate limits, network issues, 5xx errors
- **Non-Retryable Errors**: Authentication failures, bad requests

## 📊 Performance Features

- **Response Caching**: TTL-based caching (5 minutes default) for identical requests
- **Asynchronous Processing**: Full async/await support for concurrent requests
- **Token Tracking**: Tracks input/output tokens and generation time
- **Performance Logging**: Detailed request timing and token usage in logs

## 🔍 Response Structure

The `/analyze` endpoint returns a comprehensive response:

- **Request Tracking**: `request_id`, `execution_id`, `plan_id`, `status`, `timestamp`
- **Intent Analysis**: `intent_type`, `intent_summary`
- **Execution Plan**: Complete plan with operations, queries, and governance
- **Visualization**: Array of visualization recommendations (if requested)
- **AI Metadata**: Confidence scores, reasoning steps, token usage, generation time
- **Suggestions**: Improvement suggestions for the generated plan

## 📝 Development

### Project Architecture

The application follows a clean architecture:

1. **API Layer** (`app.py`): FastAPI endpoints, request/response models, exception handling
2. **Schema Layer** (`schema/`): Pydantic models for validation and type safety
3. **Service Layer** (`services/`): Business logic, external API integration
4. **Core Utilities** (`middleware.py`, `utils.py`): Shared infrastructure and utilities

### Code Style

- Follows PEP 8 Python style guide
- Type hints throughout
- Async/await for I/O operations
- Comprehensive error handling and logging

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

[Add your license information here]

## 🆘 Support

For issues, questions, or contributions, please open an issue on the repository.

## 🙏 Acknowledgments

- Groq API for LLM capabilities
- FastAPI for the web framework
- Pydantic for data validation
- Meta Llama models for AI capabilities

---

**Note**: Make sure to never commit your `.env` file with actual API keys. The `.gitignore` file is configured to exclude environment files and secrets.
