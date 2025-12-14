# RiverGen PSA - Prompt-to-SQL Analysis System

A comprehensive AI-powered system for intent classification, data governance, execution planning, visualization, and analysis. This system processes natural language prompts and generates optimized database queries (SQL/NoSQL) with built-in security and governance policies.

## 🚀 Features

- **Intent Classification**: Automatically identifies user intent from natural language prompts
- **Data Governance**: Applies row-level security (RLS) and column masking rules
- **Execution Planning**: Generates database-specific commands (SQL/NoSQL) based on intent and governance
- **Visualization Recommendations**: Suggests appropriate charts and visualizations based on query results
- **AI Analysis**: Provides confidence scores, reasoning, and suggestions for generated plans
- **Multi-Database Support**: Supports PostgreSQL, MySQL, MongoDB, Cassandra, Redis, DynamoDB, Elasticsearch, and more
- **Retry Logic**: Built-in retry mechanism for stable API calls with exponential backoff

## 📋 Prerequisites

- Python 3.8 or higher
- Google Gemini API key ([Get one here](https://aistudio.google.com/app/apikey))

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
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your Gemini API key:
   ```env
   GEMINI_API_KEY=your_actual_api_key_here
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

3. **Test the API:**
   - Use the interactive Swagger UI to test endpoints
   - Or use curl/Postman with the example request below

### Running the Standalone Script

For testing without the API server:
```bash
python main.py
```

## 📚 Project Structure

```
rivergen-psa/
├── agent/                    # AI agent modules
│   ├── intent_agent.py      # Intent classification
│   ├── governance_agent.py  # Data governance and RLS
│   ├── planning_agent.py    # Execution plan generation
│   ├── visualization_agent.py  # Visualization recommendations
│   └── analyze_ai_agent.py  # AI analysis and confidence scoring
├── service/                  # Service layer
│   └── service.py           # AI service wrapper with retry logic
├── api_models.py            # Pydantic models for API request/response
├── database_config.py       # Database configuration and constants
├── app.py                   # FastAPI application
├── main.py                  # Standalone script for testing
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
└── README.md               # This file
```

## 🤖 AI Agents Architecture

The system uses a multi-agent architecture where each agent specializes in a specific task. Agents work sequentially, with each agent's output feeding into the next. All agents use Google Gemini AI models with structured output (Pydantic schemas) and dynamic prompt engineering based on database type, intent, and context.

### Agent Pipeline Flow

```
User Request
    ↓
[1] Intent Agent → Classifies user intent
    ↓
[2] Governance Agent → Applies security rules
    ↓
[3] Planning Agent → Generates execution plan
    ↓
[4] Visualization Agent (optional) → Recommends charts
    ↓
[5] Analyze AI Agent → Evaluates plan quality
    ↓
Final Response
```

---

### 1. Intent Agent (`agent/intent_agent.py`)

**Purpose**: Classifies the user's intent from natural language prompts and determines what type of database operation is needed.

#### How It Works

1. **Input Analysis**: Receives user prompt, data source information, schema details, and user context
2. **Database Type Detection**: Determines if the data source is SQL or NoSQL
3. **Intent Classification**: Identifies the specific intent type from available options
4. **Feature Detection**: Determines if the query needs aggregation, joins, time filters, etc.

#### Prompt Engineering

The agent uses **dynamic system instructions** that adapt based on:
- **Database Type**: PostgreSQL, MySQL, MongoDB, etc.
- **Source Category**: SQL vs Non-SQL
- **Available Intent Types**: Different sets for SQL and NoSQL databases

**System Instruction Structure**:
```
You are an intent classification agent specialized in analyzing user queries for {database_type} databases.
- Database Type: {sql_type}
- Source Category: {source_category}
- Available Intent Types: {intent_type_description}

Analyze the user prompt and determine:
1. Primary intent type from available types
2. Whether aggregation is needed
3. Whether joins are required
4. Whether time-based filtering is needed
5. Estimated number of rows to return
```

**Prompt Context Includes**:
- User prompt text
- Data source name and type
- User context (ID, workspace, organization, roles, permissions, attributes)
- Available tables/collections and schemas (full schema structure)
- Execution context (max rows, timeout)
- Governance policies (if present)

#### Supported Intent Types

**SQL Intent Types**:
- `query` - Simple data retrieval
- `write` - INSERT, UPDATE, DELETE operations
- `transform` - Data transformation operations
- `join` - Multi-table joins
- `aggregate` - Aggregation queries (GROUP BY, aggregate functions)
- `analytics` - Complex analytical queries
- `schema_inspection` - Schema exploration queries
- `pipeline` - ETL pipeline operations
- `governance` - Governance-related queries
- `explain` - Query explanation and optimization

**NoSQL Intent Types**:
- `query` - Document/record retrieval
- `write` - Document creation/update
- `document_transform` - Document transformation
- `search` - Full-text search operations
- `index` - Index management
- `stream` - Streaming operations
- `aggregate` - Aggregation pipelines (MongoDB, etc.)

#### Output Schema

```python
{
    "intent_type": "query" | "aggregate" | "join" | ...,
    "intent_summary": "Human-readable summary",
    "source_category": "sql" | "non_sql",
    "needs_aggregation": bool,
    "needs_join": bool,
    "needs_time_filter": bool,
    "no_rows": int  # Estimated rows
}
```

#### Handling Cases

- **Ambiguous Prompts**: Analyzes context (tables, columns) to disambiguate
- **Multi-Intent Queries**: Identifies primary intent, flags secondary needs
- **Database-Specific Features**: Considers database capabilities (e.g., MongoDB aggregation pipelines)
- **Schema-Aware**: Uses available tables/columns to refine intent classification

---

### 2. Governance Agent (`agent/governance_agent.py`)

**Purpose**: Applies data governance rules including row-level security (RLS) and column masking based on user context and governance policies.

#### How It Works

1. **Policy Analysis**: Reviews the complete `governance_policies` object from the request
2. **Placeholder Resolution**: Resolves placeholders like `{user_id}`, `{user.attributes.*}` with actual values
3. **Rule Application**: Determines which RLS and masking rules apply to the current request
4. **Planning Notes**: Generates notes to help the planning agent construct secure queries

#### Prompt Engineering

**Dynamic System Instruction** based on:
- **Intent Type**: Different rules for read vs write operations
- **Database Type**: SQL vs NoSQL syntax differences
- **Operation Type**: Read/query vs write operations

**System Instruction Structure**:
```
You are a data governance agent specialized in applying row-level security (RLS) and column masking rules to {database_type} database operations.

Context:
- Database Type: {database_type}
- Source Category: {source_category}
- Intent Type: {intent_type} ({operation_type})

Your responsibilities:
1. Analyze user prompt and intent to determine which governance rules apply
2. Review the complete governance_policies object
3. Resolve placeholders with actual user context values
4. Generate row-level security filters for {database_type}
5. Generate column masking rules for sensitive data
6. Explain how governance rules protect data
7. Provide planning notes for secure command construction
```

**Prompt Context Includes**:
- User prompt and intent classification result
- Complete `governance_policies` object (row_level_security and column_masking)
- User context (for placeholder resolution)
- Table/collection schemas with PII flags
- Database type and source category

#### Placeholder Resolution

The agent resolves placeholders in governance rules:
- `{user_id}` → Actual user ID from context
- `{workspace_id}` → Workspace ID
- `{organization_id}` → Organization ID
- `{user.attributes.assigned_region}` → User attribute values

**Example**:
```
Rule: "region IN (SELECT region FROM user_access WHERE user_id = {user_id})"
Resolved: "region IN (SELECT region FROM user_access WHERE user_id = 1)"
```

#### Output Schema

```python
{
    "row_filters": [
        "region IN (SELECT region FROM user_access WHERE user_id = 1)",
        "status = 'active'"
    ],
    "column_masking_rules": [
        {
            "column": "email",
            "condition": "region != 'US-WEST'",
            "masking_function": "email_mask",
            "description": "Mask emails for users outside assigned region"
        }
    ],
    "governance_applied": [
        "region_filter",
        "email_mask_region"
    ],
    "governance_impact": "Explanation of how rules protect data",
    "planning_notes": [
        "Apply region filter in WHERE clause",
        "Use CASE statement for email masking"
    ]
}
```

#### Handling Cases

- **No Governance Policies**: Returns empty rules (system still works)
- **Multiple Rules**: Applies all relevant rules, combines them logically
- **Conflicting Rules**: Prioritizes more restrictive rules
- **Database-Specific Syntax**: Generates filters appropriate for SQL vs NoSQL
- **Conditional Masking**: Applies masking based on conditions (e.g., region, role)

---

### 3. Planning Agent (`agent/planning_agent.py`)

**Purpose**: Generates detailed execution plans with actual database queries/commands that implement the user's request while applying governance rules.

#### How It Works

1. **Plan Strategy**: Determines execution strategy (pushdown, hybrid, etc.)
2. **Step Generation**: Breaks down operations into logical steps with dependencies
3. **Query Generation**: Creates actual database queries/commands with governance applied
4. **Query Payload**: Structures query metadata (filters, projections, sorting, limits)
5. **Governance Integration**: Embeds RLS filters and column masking into queries

#### Prompt Engineering

**Highly Dynamic System Instruction** based on:
- **Database Type**: PostgreSQL, MySQL, MongoDB, etc.
- **Database Dialect**: Specific SQL dialect or NoSQL query language
- **Intent Type**: Query, aggregate, join, write, etc.
- **Source Category**: SQL vs NoSQL

**System Instruction Structure**:
```
You are an execution planning agent specialized in creating detailed execution plans for {database_type} database operations.

Context:
- Database Type: {database_type}
- Database Dialect: {dialect}
- Query Language: {language}
- Source Category: {source_category}
- Intent Type: {intent_type}

Your responsibilities:
1. Analyze user prompt, intent, and governance rules
2. Create comprehensive execution plan with step-by-step operations
3. Generate actual {database_type} queries/commands
4. Apply governance rules (RLS and column masking)
5. Define query payloads with filters, projections, sorting, limits
6. Specify compute requirements and dependencies
7. Optimize for {database_type} performance and security
```

**Database-Specific Query Guidance**:
The system includes detailed query patterns for each database type:
- **PostgreSQL**: Includes examples for SELECT, JOIN, aggregation, masking with CASE statements
- **MongoDB**: Includes find(), aggregate() pipelines, projection with $cond for masking
- **Cassandra**: CQL syntax with partition keys
- **Redis**: Key-based operations and SCAN patterns
- **DynamoDB**: Query/Scan with KeyConditionExpression
- **Elasticsearch**: JSON query DSL examples

**Prompt Context Includes**:
- User request (prompt, context, data sources)
- Intent classification result
- Governance result (row filters, masking rules)
- Complete schema information (tables, columns, types, indexes)
- Execution context (max rows, timeout)
- Database-specific query patterns and examples

#### Output Schema

```python
{
    "strategy": "pushdown" | "hybrid" | "compute",
    "type": "sql_query" | "nosql_query",
    "operations": [
        {
            "step": 1,
            "step_id": "step_1",
            "operation_type": "read" | "write" | "transform",
            "type": "source_query" | "aggregation" | "join",
            "description": "Human-readable description",
            "data_source_id": 1,
            "compute_type": "source_native" | "query" | "aggregation",
            "compute_engine": "postgresql" | "mongodb" | ...,
            "dependencies": [],
            "query": "SELECT ... WITH governance applied",
            "query_payload": {
                "language": "sql" | "nosql",
                "dialect": "postgresql" | "mongodb" | ...,
                "statement": "Full query statement",
                "query_type": "select" | "aggregate" | "find",
                "parameters": [...],
                "filters": [...],
                "projections": [...],
                "sort_field": "revenue",
                "sort_order": "desc",
                "limit": 10,
                "offset": 0
            },
            "governance_applied": {
                "rls_rules": ["region_filter"],
                "masking_rules": ["email_mask_region"],
                "applied_rules": ["Applied region filter", "Applied email masking"]
            },
            "output_artifact": "result_set_1"
        }
    ]
}
```

#### Query Generation Examples

**SQL Example (PostgreSQL with Governance)**:
```sql
WITH filtered_customers AS (
    SELECT * FROM customers 
    WHERE region IN (SELECT region FROM user_access WHERE user_id = 1)
)
SELECT 
    c.id, 
    c.name, 
    CASE 
        WHEN c.region = 'US-WEST' THEN c.email 
        ELSE CONCAT(LEFT(c.email, 3), '***@', SPLIT_PART(c.email, '@', 2)) 
    END as email,
    SUM(o.amount) as revenue
FROM filtered_customers c
JOIN orders o ON c.id = o.customer_id
WHERE o.created_at >= '2025-01-01' AND o.created_at <= '2025-03-31'
GROUP BY c.id, c.name, c.region, c.email
ORDER BY revenue DESC
LIMIT 10
```

**NoSQL Example (MongoDB with Governance)**:
```javascript
db.customers.aggregate([
    { $match: { 
        region: { $in: db.user_access.distinct("region", { user_id: 1 }) }
    }},
    { $lookup: {
        from: "orders",
        localField: "id",
        foreignField: "customer_id",
        as: "orders"
    }},
    { $project: {
        id: 1,
        name: 1,
        email: {
            $cond: {
                if: { $eq: ["$region", "US-WEST"] },
                then: "$email",
                else: { $concat: [
                    { $substr: ["$email", 0, 3] },
                    "***@",
                    { $arrayElemAt: [{ $split: ["$email", "@"] }, 1] }
                ]}
            }
        },
        revenue: { $sum: "$orders.amount" }
    }},
    { $sort: { revenue: -1 }},
    { $limit: 10 }
])
```

#### Handling Cases

- **Complex Queries**: Breaks into multiple steps with dependencies
- **Governance Integration**: Seamlessly embeds RLS and masking into queries
- **Database Dialects**: Uses correct syntax for each database type
- **Optimization**: Considers indexes, query patterns, best practices
- **Error Prevention**: Validates query structure, column names, table names
- **Multi-Step Operations**: Handles ETL pipelines, transformations, joins

---

### 4. Visualization Agent (`agent/visualization_agent.py`)

**Purpose**: Recommends appropriate data visualizations based on the execution plan, query results structure, and user intent. Only runs if `include_visualization: true` in the request.

#### How It Works

1. **Plan Analysis**: Analyzes the execution plan to understand data structure
2. **Column Analysis**: Identifies columns, their types, and relationships
3. **Visualization Selection**: Chooses appropriate chart types based on data characteristics
4. **Multi-Visualization**: Generates multiple visualizations (1, 2, 3, or more) for different perspectives
5. **Configuration**: Sets up chart configuration (orientation, colors, sortable, filterable)

#### Prompt Engineering

**System Instruction Structure**:
```
You are a data visualization agent specialized in recommending appropriate visualizations for {database_type} query results.

Your responsibilities:
1. Analyze execution plan and identify data structure
2. Determine appropriate visualization types based on:
   - Intent type and query purpose
   - Number and types of columns
   - Whether data is aggregated, time-series, categorical, or numerical
   - Relationships between columns
3. Recommend visualizations:
   - Tables for detailed views
   - Bar charts for categorical comparisons
   - Line charts for time-series
   - Pie charts for proportional data
   - Scatter plots for relationships
4. Mark one visualization as primary (typically table)
5. Provide titles, axis labels, and configuration
```

**Key Guidelines**:
- **Generate multiple visualizations** (1, 2, 3, or more) based on complexity
- Always include at least one **table** visualization (marked as primary)
- For analytical queries, consider multiple perspectives:
  - Table for detailed view (primary)
  - Bar/Line chart for comparisons or trends
  - Additional charts for multiple dimensions

**Prompt Context Includes**:
- User prompt and intent
- Execution plan (operations, queries, columns)
- Data structure from query projections
- Intent type (affects visualization choice)

#### Output Schema

```python
{
    "visualizations": [
        {
            "type": "table" | "bar" | "line" | "pie" | "scatter" | ...,
            "title": "Top 10 Customers by Revenue (Q1 2025)",
            "x_axis": "name" | null,  # For charts
            "y_axis": "revenue" | null,  # For charts
            "config": {
                "sortable": true,
                "filterable": true,
                "orientation": "vertical" | "horizontal",
                "color_scheme": "default" | ...
            },
            "is_primary": true  # One visualization marked as primary
        }
    ]
}
```

#### Visualization Type Selection Logic

- **Tables**: Always included (primary) for detailed data viewing
- **Bar Charts**: For categorical comparisons, top N lists, grouped data
- **Line Charts**: For time-series data, trends over time
- **Pie Charts**: For proportional data, percentage breakdowns
- **Scatter Plots**: For relationships between two numerical variables
- **Heatmaps**: For correlation matrices, multi-dimensional data

#### Handling Cases

- **Simple Queries**: Generates 1-2 visualizations (table + one chart)
- **Complex Analytics**: Generates 3+ visualizations (multiple perspectives)
- **Time-Series Data**: Prioritizes line charts
- **Aggregated Data**: Uses bar/pie charts for summaries
- **No Visualization Requested**: Agent is skipped entirely
- **Empty Results**: Still provides visualization recommendations (for empty state handling)

---

### 5. Analyze AI Agent (`agent/analyze_ai_agent.py`)

**Purpose**: Evaluates the quality, correctness, and completeness of the generated execution plan. Provides confidence scores, reasoning, and improvement suggestions.

#### How It Works

1. **Plan Evaluation**: Analyzes the execution plan for correctness and completeness
2. **Confidence Scoring**: Assigns a confidence score (0-100) based on multiple factors
3. **Reasoning**: Explains the confidence assessment with clear reasoning steps
4. **Suggestions**: Provides actionable suggestions for improvement if confidence < 100%

#### Prompt Engineering

**System Instruction Structure**:
```
You are an AI analysis agent specialized in evaluating execution plans for {database_type} database operations.

Your responsibilities:
1. Analyze execution plan and assess quality, correctness, completeness
2. Provide confidence score (0-100) indicating confidence that plan will:
   - Correctly execute user's request
   - Apply governance rules properly
   - Generate accurate results
   - Follow best practices for {database_type}
3. Explain confidence assessment with clear reasoning
4. List key reasoning steps
5. Provide actionable suggestions for improvement if confidence < 100%
```

**Confidence Score Guidelines**:
- **90-100**: Excellent plan, very confident it will work correctly
- **80-89**: Good plan with minor potential issues
- **70-79**: Acceptable plan but has some concerns
- **60-69**: Plan has notable issues that may cause problems
- **Below 60**: Plan has significant issues and may not work correctly

**Evaluation Factors**:
1. Query Correctness: Does syntax match database standards?
2. Governance Application: Are RLS and masking rules properly applied?
3. Intent Alignment: Does plan address user's intent?
4. Data Access: Are correct tables/collections and columns accessed?
5. Aggregations: Are aggregations correctly implemented?
6. Filtering: Are filters (including governance) correctly applied?
7. Sorting and Limits: Are sorting and limiting correct?
8. Best Practices: Does plan follow database best practices?
9. Completeness: Are all necessary steps included?
10. Dependencies: Are step dependencies correctly defined?

**Prompt Context Includes**:
- User request (prompt, context)
- Intent classification result
- Governance result
- Execution plan (full plan with queries)
- Token usage and generation time (for metadata)

#### Output Schema

```python
{
    "confidence": 95,  # 0-100 scale
    "confidence_score": 0.95,  # 0.0-1.0 scale
    "explanation": "Detailed explanation of confidence assessment",
    "reasoning_steps": [
        "Identified tables: customers, orders",
        "Detected join condition: customer_id",
        "Applied RLS filter for user's assigned regions",
        "Applied email masking for regions outside user's assigned region",
        "Added date range filter for Q1 2025",
        "Aggregated by SUM(amount)",
        "Limited to top 10"
    ],
    "suggestions": [
        "Consider filtering by customer segment for more insights",
        "You might want to compare with previous quarter"
    ]
}
```

#### Handling Cases

- **High Confidence (90-100)**: Plan is excellent, minimal or no suggestions
- **Medium Confidence (70-89)**: Plan is good but has minor issues, provides suggestions
- **Low Confidence (<70)**: Plan has notable issues, provides detailed suggestions
- **Syntax Errors**: Detects and flags syntax issues
- **Missing Governance**: Flags if governance rules are not properly applied
- **Performance Issues**: Suggests optimizations (indexes, query structure)
- **Best Practice Violations**: Identifies and suggests improvements

---

## 🔧 AI Service Layer (`service/service.py`)

The `AIService` class provides a unified interface for all AI model interactions with built-in retry logic and error handling.

### Features

- **Structured Output**: Uses Pydantic models for type-safe responses
- **Retry Logic**: Automatic retries with exponential backoff (3 attempts)
- **Error Classification**: Distinguishes retryable vs non-retryable errors
- **Token Tracking**: Returns token usage for each API call
- **Model Flexibility**: Supports different Gemini models

### Retry Mechanism

**Retryable Errors** (automatically retried):
- Rate limits (429)
- Server errors (500, 502, 503)
- Network issues (timeout, connection errors)
- Temporary failures (service unavailable, resource exhausted)

**Non-Retryable Errors** (fail immediately):
- Authentication failures (401, 403)
- Bad requests (400)
- Not found (404)
- Invalid API key

**Retry Strategy**:
- Max attempts: 3
- Exponential backoff: 1s, 2s, 4s delays
- Error logging: Detailed error messages for debugging

### Usage Example

```python
from service.service import AIService
from agent.intent_agent import IntentOutput

service = AIService(api_key=os.getenv("GEMINI_API_KEY"), model="gemini-2.5-flash-lite")
response_dict, token_count = service.generate_response(
    system_instruction="...",
    prompt="...",
    output_schema=IntentOutput
)
```

---

## 🔌 API Endpoints

### POST `/analyze`

Main endpoint that processes requests through all agents.

**Request Body:**
```json
{
  "request_id": "req-12345",
  "execution_id": "exec-67890",
  "timestamp": "2025-01-15T10:00:00Z",
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
      "schemas": [...]
    }
  ],
  "ai_model": "gemini-2.5-flash-lite",
  "temperature": 0.1,
  "include_visualization": true
}
```

**Response:**
```json
{
  "request_id": "req-12345",
  "execution_id": "exec-67890",
  "plan_id": "plan-abc123",
  "status": "success",
  "timestamp": "2025-01-15T10:00:02Z",
  "intent_type": "query",
  "intent_summary": "Retrieve top 10 customers by total revenue for Q1 2025",
  "execution_plan": {
    "strategy": "pushdown",
    "type": "sql_query",
    "operations": [...]
  },
  "visualization": [...],
  "ai_metadata": {
    "model": "gemini-2.5-flash-lite",
    "confidence": 0.95,
    "tokens_used": 1250,
    "generation_time_ms": 2340
  },
  "suggestions": [...]
}
```

## 🔧 Configuration

### Supported AI Models

- `gemini-2.5-flash-lite` (default) - Faster, cost-effective
- `gemini-2.5-flash` - More capable, higher quality

### Supported Database Types

**SQL Databases:**
- PostgreSQL
- MySQL
- MariaDB
- SQL Server
- Oracle

**NoSQL Databases:**
- MongoDB
- Cassandra
- Redis
- DynamoDB
- Elasticsearch

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Your Google Gemini API key | Yes |

## 🧪 Testing

### Using Swagger UI

1. Start the server: `python app.py`
2. Navigate to http://localhost:8000/docs
3. Click on `/analyze` endpoint
4. Click "Try it out"
5. Modify the example request body
6. Click "Execute"

### Using cURL

```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d @example_request.json
```

## 🔒 Security

- **API Key Management**: Never commit `.env` files to version control
- **Row-Level Security**: Automatically applied based on user context
- **Column Masking**: PII data is masked according to governance policies
- **Input Validation**: Comprehensive validation of all request fields

## 🐛 Error Handling

The API includes robust error handling:

- **400 Bad Request**: Invalid request data or missing required fields
- **422 Unprocessable Entity**: Pydantic validation errors
- **500 Internal Server Error**: Unexpected errors with detailed logging

All errors include structured error messages for easy debugging.

## 🔄 Retry Logic

The AI service includes automatic retry logic:
- **Max Retries**: 3 attempts
- **Exponential Backoff**: 1s, 2s, 4s delays
- **Retryable Errors**: Rate limits, network issues, 5xx errors
- **Non-Retryable Errors**: Authentication failures, bad requests

## 📊 Performance Metrics

The API tracks and returns:
- **Total Tokens Used**: Across all agent calls
- **Generation Time**: Total processing time in milliseconds
- **Confidence Score**: AI confidence in the generated plan (0-100)

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

- Google Gemini API for AI capabilities
- FastAPI for the web framework
- Pydantic for data validation

---

**Note**: Make sure to never commit your `.env` file with actual API keys. Always use `.env.example` as a template.

