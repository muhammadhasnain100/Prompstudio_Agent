"""Prompt definitions for LLM interactions."""

from typing import Dict, List, Tuple
import json

# Database type sets for categorization
SQL_TYPES = {"postgresql", "mysql", "mariadb", "sqlserver", "oracle"}
CLOUD_WAREHOUSE_TYPES = {"snowflake", "bigquery", "redshift", "synapse", "databricks"}
NOSQL_TYPES = {"mongodb", "cassandra", "redis", "dynamodb", "elasticsearch"}

# Intent type definitions
SQL_INTENT_TYPES: List[str] = [
    "query",
    "write",
    "transform",
    "join",
    "aggregate",
    "analytics",
    "schema_inspection",
    "pipeline",
    "governance",
    "explain",
]

NON_SQL_INTENT_TYPES: List[str] = [
    "query",
    "write",
    "aggregate",
    "index",
    "document_transform",
    "search",
    "pipeline",
    "stream",
    "governance",
    "schema_inspection",
]

# Query patterns - simplified version
SQL_QUERY_PATTERNS: Dict[str, Dict[str, str]] = {
    "postgresql": {
        "query": "SELECT column1, column2 FROM schema.table WHERE condition",
        "aggregate": "SELECT column, SUM(amount) FROM table GROUP BY column",
        "join": "SELECT * FROM table1 t1 JOIN table2 t2 ON t1.id = t2.id",
        "masking": "CASE WHEN condition THEN column ELSE CONCAT(LEFT(column, 3), '***') END",
        "string_functions": "CONCAT, LEFT, RIGHT, SUBSTRING, SPLIT_PART, REPLACE",
        "date_functions": "DATE_TRUNC, EXTRACT, NOW(), CURRENT_DATE, INTERVAL"
    },
    "mysql": {
        "query": "SELECT column1, column2 FROM schema.table WHERE condition",
        "aggregate": "SELECT column, SUM(amount) FROM table GROUP BY column",
        "join": "SELECT * FROM table1 t1 JOIN table2 t2 ON t1.id = t2.id",
        "masking": "CASE WHEN condition THEN column ELSE CONCAT(LEFT(column, 3), '***') END",
        "string_functions": "CONCAT, LEFT, RIGHT, SUBSTRING, REPLACE",
        "date_functions": "DATE_FORMAT, YEAR, MONTH, DAY, NOW(), CURDATE()"
    },
    "mariadb": {
        "query": "SELECT column1, column2 FROM schema.table WHERE condition",
        "aggregate": "SELECT column, SUM(amount) FROM table GROUP BY column",
        "join": "SELECT * FROM table1 t1 JOIN table2 t2 ON t1.id = t2.id",
        "masking": "CASE WHEN condition THEN column ELSE CONCAT(LEFT(column, 3), '***') END",
        "string_functions": "CONCAT, LEFT, RIGHT, SUBSTRING, REPLACE",
        "date_functions": "DATE_FORMAT, YEAR, MONTH, DAY, NOW(), CURDATE()"
    },
    "sqlserver": {
        "query": "SELECT column1, column2 FROM schema.table WHERE condition",
        "aggregate": "SELECT column, SUM(amount) FROM table GROUP BY column",
        "join": "SELECT * FROM table1 t1 JOIN table2 t2 ON t1.id = t2.id",
        "masking": "CASE WHEN condition THEN column ELSE LEFT(column, 3) + '***' END",
        "string_functions": "CONCAT, LEFT, RIGHT, SUBSTRING, REPLACE, STUFF",
        "date_functions": "GETDATE(), DATEADD, DATEDIFF, YEAR, MONTH, DAY"
    },
    "oracle": {
        "query": "SELECT column1, column2 FROM schema.table WHERE condition",
        "aggregate": "SELECT column, SUM(amount) FROM table GROUP BY column",
        "join": "SELECT * FROM table1 t1 JOIN table2 t2 ON t1.id = t2.id",
        "masking": "CASE WHEN condition THEN column ELSE SUBSTR(column, 1, 3) || '***' END",
        "string_functions": "CONCAT, SUBSTR, INSTR, REPLACE, LENGTH, UPPER, LOWER",
        "date_functions": "SYSDATE, TO_DATE, TO_CHAR, EXTRACT, ADD_MONTHS"
    }
}

CLOUD_WAREHOUSE_QUERY_PATTERNS: Dict[str, Dict[str, str]] = {
    "snowflake": {
        "query": "SELECT column1, column2 FROM database.schema.table WHERE condition",
        "aggregate": "SELECT column, SUM(amount) FROM table GROUP BY column",
        "join": "SELECT * FROM table1 t1 JOIN table2 t2 ON t1.id = t2.id",
        "masking": "CASE WHEN condition THEN column ELSE CONCAT(LEFT(column, 3), '***') END",
        "string_functions": "CONCAT, LEFT, RIGHT, SUBSTRING, REPLACE, UPPER, LOWER, TRIM",
        "date_functions": "DATE_TRUNC, DATEDIFF, DATEADD, CURRENT_DATE(), CURRENT_TIMESTAMP()",
        "warehouse_functions": "QUALIFY (window functions), PIVOT, UNPIVOT, LATERAL FLATTEN"
    },
    "bigquery": {
        "query": "SELECT column1, column2 FROM `project.dataset.table` WHERE condition",
        "aggregate": "SELECT column, SUM(amount) FROM table GROUP BY column",
        "join": "SELECT * FROM table1 t1 JOIN table2 t2 ON t1.id = t2.id",
        "masking": "CASE WHEN condition THEN column ELSE CONCAT(SUBSTR(column, 1, 3), '***') END",
        "string_functions": "CONCAT, SUBSTR, REPLACE, UPPER, LOWER, TRIM, REGEXP_REPLACE",
        "date_functions": "DATE_TRUNC, DATE_DIFF, DATE_ADD, CURRENT_DATE(), CURRENT_TIMESTAMP()",
        "warehouse_functions": "ARRAY_AGG, STRUCT, UNNEST, APPROX_COUNT_DISTINCT, PIVOT"
    },
    "redshift": {
        "query": "SELECT column1, column2 FROM schema.table WHERE condition",
        "aggregate": "SELECT column, SUM(amount) FROM table GROUP BY column",
        "join": "SELECT * FROM table1 t1 JOIN table2 t2 ON t1.id = t2.id",
        "masking": "CASE WHEN condition THEN column ELSE CONCAT(LEFT(column, 3), '***') END",
        "string_functions": "CONCAT, LEFT, RIGHT, SUBSTRING, REPLACE, UPPER, LOWER, TRIM",
        "date_functions": "DATE_TRUNC, DATEDIFF, DATEADD, GETDATE(), CURRENT_DATE",
        "warehouse_functions": "LISTAGG, WINDOW functions, APPROXIMATE functions"
    },
    "synapse": {
        "query": "SELECT column1, column2 FROM schema.table WHERE condition",
        "aggregate": "SELECT column, SUM(amount) FROM table GROUP BY column",
        "join": "SELECT * FROM table1 t1 JOIN table2 t2 ON t1.id = t2.id",
        "masking": "CASE WHEN condition THEN column ELSE LEFT(column, 3) + '***' END",
        "string_functions": "CONCAT, LEFT, RIGHT, SUBSTRING, REPLACE, UPPER, LOWER, TRIM",
        "date_functions": "GETDATE(), DATEADD, DATEDIFF, YEAR, MONTH, DAY, DATEPART",
        "warehouse_functions": "STRING_AGG, ARRAY_AGG, WINDOW functions, APPROX_COUNT_DISTINCT"
    },
    "databricks": {
        "query": "SELECT column1, column2 FROM catalog.schema.table WHERE condition",
        "aggregate": "SELECT column, SUM(amount) FROM table GROUP BY column",
        "join": "SELECT * FROM table1 t1 JOIN table2 t2 ON t1.id = t2.id",
        "masking": "CASE WHEN condition THEN column ELSE CONCAT(SUBSTRING(column, 1, 3), '***') END",
        "string_functions": "CONCAT, SUBSTRING, REPLACE, UPPER, LOWER, TRIM, REGEXP_REPLACE",
        "date_functions": "DATE_TRUNC, DATEDIFF, DATE_ADD, CURRENT_DATE(), CURRENT_TIMESTAMP()",
        "warehouse_functions": "ARRAY functions, MAP functions, STRUCT, LATERAL VIEW, EXPLODE"
    }
}

NON_SQL_QUERY_PATTERNS: Dict[str, Dict[str, str]] = {
    "mongodb": {
        "query": "db.collection.find({filter}, {projection})",
        "aggregate": "db.collection.aggregate([{$match: {filter}}, {$group: {_id: '$field', total: {$sum: '$amount'}}}])",
        "filter": "{field: value, field2: {$gte: value2}}",
        "projection": "{field1: 1, field2: 1, _id: 0}",
        "masking": "Use $project with $cond for conditional masking",
        "operators": "$match, $group, $project, $sort, $limit, $skip, $lookup, $unwind"
    },
    "cassandra": {
        "query": "SELECT column1, column2 FROM keyspace.table WHERE partition_key = ? AND clustering_key = ?",
        "filter": "WHERE partition_key = ? AND clustering_key > ?",
        "aggregate": "SELECT COUNT(*), SUM(amount) FROM table WHERE partition_key = ?",
        "masking": "Use CASE in SELECT for conditional masking",
        "note": "CQL requires partition key in WHERE clause, clustering key for range queries"
    },
    "redis": {
        "query": "GET key, HGET hash_key field, MGET key1 key2",
        "filter": "Use SCAN with MATCH pattern for filtering",
        "aggregate": "Use Lua scripts or client-side aggregation",
        "masking": "Apply masking in application layer or Lua scripts",
        "note": "Redis is key-value store, queries are key-based operations"
    },
    "dynamodb": {
        "query": "Query with KeyConditionExpression and FilterExpression",
        "filter": "FilterExpression: attribute_exists(field) AND field = :value",
        "projection": "ProjectionExpression: field1, field2",
        "aggregate": "Use Scan or Query with client-side aggregation",
        "masking": "Apply masking in application layer or use ProjectionExpression",
        "note": "DynamoDB uses ExpressionAttributeNames and ExpressionAttributeValues"
    },
    "elasticsearch": {
        "query": "GET /index/_search with query DSL",
        "filter": '{"query": {"bool": {"must": [{"term": {"field": "value"}}]}}}',
        "aggregate": '{"aggs": {"group_by_field": {"terms": {"field": "field"}, "aggs": {"total": {"sum": {"field": "amount"}}}}}}',
        "projection": '"source": ["field1", "field2"]',
        "masking": "Use script_fields for conditional masking",
        "note": "Elasticsearch uses JSON query DSL, supports complex aggregations"
    }
}


async def getdatabase(db_type: str) -> Tuple[str, Dict[str, str], List[str]]:
    """
    Determine database category, query patterns, and intent types.
    
    Args:
        db_type: Database type (e.g., "postgresql", "snowflake", "mongodb")
    
    Returns:
        Tuple of (databasetype, query_pattern, intent_types)
    """
    db_type_lower = db_type.lower()
    
    if db_type_lower in SQL_TYPES:
        databasetype = "sql"
        intent_types = SQL_INTENT_TYPES
        query_pattern = SQL_QUERY_PATTERNS.get(db_type_lower, {})
    elif db_type_lower in CLOUD_WAREHOUSE_TYPES:
        databasetype = "cloud_warehouse"
        intent_types = SQL_INTENT_TYPES
        query_pattern = CLOUD_WAREHOUSE_QUERY_PATTERNS.get(db_type_lower, {})
    elif db_type_lower in NOSQL_TYPES:
        databasetype = "nosql"
        intent_types = NON_SQL_INTENT_TYPES
        query_pattern = NON_SQL_QUERY_PATTERNS.get(db_type_lower, {})
    else:
        databasetype = "unknown"
        intent_types = []
        query_pattern = {}
    
    return databasetype, query_pattern, intent_types


async def get_system_prompt() -> str:
    """Get the system prompt for the LLM."""
    return """
You are an assistant that MUST return exactly one JSON object that conforms to the provided JSON schema.

- OUTPUT CONSTRAINTS:

  1) Return strictly valid JSON. Do NOT include any plaintext, Markdown, commentary, or code fences.

  2) Match types exactly: timestamps must be ISO 8601 strings where expected; arrays, objects and primitives must match the schema.

  3) If a value is unknown or cannot be determined from the provided input, set that field to null (or an empty list where appropriate) — DO NOT HALLUCINATE.


  5) Provide detailed but concise `ai_metadata.explanation` and `ai_metadata.reasoning_steps` for how you produced the execution_plan and query.

  6) If you detect possible schema validation problems (missing required sub-objects, type mismatches), include a top-level field `validation` with an object describing which parts are incomplete (field path -> short message). This `validation` object must not break the schema — place it under `ai_metadata.explanation` or inside `ai_metadata` as `validation` if needed.

- SCHEMA: follow the structure used by the ExecutionResponse Pydantic model.

- BE CONSERVATIVE: prefer null/empty rather than invented values.

{
  "intent_type": "<determine from user prompt and context - one of: query, write, transform, join, aggregate, analytics, etc.>",
  "intent_summary": "<brief summary of what the user wants to accomplish>",
  "execution_plan": {
    "strategy": "<strategy like 'pushdown', 'compute', etc.>",
    "type": "<type like 'sql_query', 'nosql_query', etc.>",
    "operations": [
      {
        "step": <step_number>,
        "step_id": "<unique step identifier>",
        "operation_type": "<operation type like 'read', 'write', etc.>",
        "type": "<type like 'source_query', 'transform', etc.>",
        "description": "<description of what this operation does>",
        "data_source_id": <data_source_id_from_request>,
        "compute_type": "<compute type like 'source_native', etc.>",
        "compute_engine": "<compute engine like 'source_native', etc.>",
        "dependencies": [<array_of_step_ids_this_depends_on>],
        "query": "<actual SQL/query statement with governance rules applied>",
        "query_payload": {
          "language": "<language like 'sql', 'nosql', etc.>",
          "dialect": "<dialect like 'postgresql', 'mysql', etc. or null>",
          "statement": "<same as query field - actual query statement>",
          "parameters": [<array_of_parameters_if_needed>]
        },
        "governance_applied": {
          "rls_rules": [<array_of_applied_rls_rule_names>],
          "masking_rules": [<array_of_applied_masking_rule_names>]
        },
        "output_artifact": "<output artifact name like 'result_frame'>"
      }
    ]
  },
  "visualization": [
    {
      "type": "<visualization type like 'table', 'bar', 'line', etc. - required>",
      "title": "<visualization title - required, must not be null or empty>",
      "x_axis": "<x_axis_field_name for charts like 'bar', 'line' - required this field cannot be none",
      "y_axis": "<y_axis_field_name for charts like 'bar', 'line' - required this field cannot be none",
      "config": {
        "<config options appropriate for visualization type - required, must not be null, at least empty object {{}}>"
      },
      "is_primary": <true_or_false>
    }
  ],
  "ai_metadata": {
    "confidence": <confidence_score_0_to_100>,
    "confidence_score": <confidence_score_0.0_to_1.0>,
    "explanation": "<detailed explanation of the execution plan and how governance was applied - required, must not be null>",
    "reasoning_steps": [
      "<step 1 of reasoning - REQUIRED, must have at least one step>",
      "<step 2 of reasoning>",
      "<continue with all reasoning steps - this array must not be empty>"
    ]
  },
  "suggestions": [
    "<suggestion 1 - REQUIRED field, array must be present, can be empty [] if no suggestions>",
    "<suggestion 2 if any>"
  ]
}
"""


async def prepare_prompt(
    databasetype: str,
    database_source: dict,
    intent_types: list,
    query_pattern: dict,
    user_context: dict,
    user_prompt: str,
    governance_policies: dict,
    execution_context: dict,
    selected_schema_names: list,
    include_visualization: bool = False
) -> str:
    """
    Prepare the user prompt for the LLM.
    
    Args:
        databasetype: Database type category (sql, cloud_warehouse, nosql)
        database_source: Data source dictionary
        intent_types: List of available intent types
        query_pattern: Query patterns for the database
        user_context: User context dictionary
        user_prompt: User's prompt/question
        governance_policies: Governance policies dictionary
        execution_context: Execution context dictionary
        selected_schema_names: List of selected schema names
    
    Returns:
        Formatted user prompt string
    """
    # Build visualization instruction based on include_visualization flag
    if include_visualization:
        viz_instruction = """
**VISUALIZATION GENERATION REQUIREMENTS**: Visualizations help users understand and explore query results through graphical representations and structured data views. You MUST generate a list of visualizations (array) that can contain one, two, or many more visualization objects depending on the complexity of the data and the user's intent. The visualization array should include at least a table visualization for detailed data viewing, and may include additional chart visualizations (such as bar charts, line charts, pie charts, or scatter plots) that provide different perspectives on the data.

**VISUALIZATION ARRAY CONSTRUCTION**: The visualization field must be an array that can contain multiple visualization objects. For simple queries, you might include just a table visualization. For analytical queries with aggregated data, you should include both a table visualization (for detailed data) and one or more chart visualizations (for trends, comparisons, or distributions). Each visualization object in the array must be complete and self-contained, with all required fields populated.

**REQUIRED FIELDS FOR EACH VISUALIZATION**:

1. **type**: A string specifying the visualization type. Use "table" for tabular data display, "bar" for bar charts comparing categories, "line" for line charts showing trends, "pie" for pie charts showing proportions, "scatter" for scatter plots showing relationships, or other appropriate types (like "area", "heatmap", "histogram") based on the data structure and what would best represent the query results. Choose visualization types that match the data characteristics - use "table" for detailed views, "bar" for categorical comparisons, "line" for trends over time, etc.

2. **title**: A descriptive string that clearly explains what the visualization shows. The title should be meaningful and context-aware, such as "Top 10 Customers by Revenue (Q1 2025)" or "Revenue Trends by Month". The title cannot be null or empty - it must provide clear information about what the visualization represents.

3. **x_axis**: A string containing the column name from the query results that should be used for the x-axis. For chart types like "bar", "line", or "scatter", this must be the actual column name from your SELECT statement (e.g., "customer_name", "month", "category"). For "table" visualizations, you can use an empty string "" since tables don't have axes. The x_axis field is REQUIRED for all visualizations - use empty string for table type, but provide actual column names for chart types.

4. **y_axis**: A string containing the column name from the query results that should be used for the y-axis. For chart types like "bar", "line", or "scatter", this must be the actual column name from your SELECT statement that represents the measure or value being visualized (e.g., "revenue", "count", "total_amount"). For "table" visualizations, you can use an empty string "" since tables don't have axes. The y_axis field is REQUIRED for all visualizations - use empty string for table type, but provide actual column names for chart types.

5. **config**: A dictionary object containing configuration options specific to the visualization type. This object cannot be null - it must be at least an empty dictionary {{}}. For table visualizations, config might include options like {{"sortable": true, "filterable": true, "pageSize": 50}}. For bar charts, config might include {{"orientation": "vertical", "color_scheme": "default", "stacked": false}}. For line charts, config might include {{"showMarkers": true, "smooth": true}}. Always provide appropriate configuration options based on the visualization type.

6. **is_primary**: A boolean value indicating whether this visualization is the primary/default visualization that should be displayed first. Typically, table visualizations are marked as primary (true) since they provide the most detailed view of the data, while chart visualizations are marked as secondary (false). Only one visualization in the array should have is_primary set to true.

**VISUALIZATION SELECTION STRATEGY**: When determining which visualizations to include, consider the query results structure, the user's intent, and the type of insights that would be most valuable. For aggregated data with categories and values, include both a table (for details) and a bar chart (for comparisons). For time-series data, include a table and a line chart. For data with multiple dimensions, consider multiple chart types that highlight different aspects. Always include at least one table visualization as it provides the most comprehensive view of the data.
"""
        viz_example = """
  "visualization": [
    {{
      "type": "table",
      "title": "<descriptive title for table visualization showing what data is displayed>",
      "x_axis": "",
      "y_axis": "",
      "config": {{
        "sortable": true,
        "filterable": true,
        "pageSize": 50
      }},
      "is_primary": true
    }},
    {{
      "type": "bar",
      "title": "<descriptive title for bar chart showing what comparison is visualized>",
      "x_axis": "<actual_column_name_from_query_results_for_categories>",
      "y_axis": "<actual_column_name_from_query_results_for_values>",
      "config": {{
        "orientation": "vertical",
        "color_scheme": "default"
      }},
      "is_primary": false
    }}
    // You can include additional visualizations as needed - one, two, or many more
  ],
"""
    else:
        viz_instruction = """
IMPORTANT: include_visualization is false - DO NOT generate visualizations. Set the visualization field to null.
"""
        viz_example = """
  "visualization": null,
"""
    
    return f"""
You are a **senior Data Intelligence, SQL Planning, and Governance Enforcement Agent**.

Your responsibility is to **deeply analyze** the full request context, infer the correct intent,
and produce a **governed, secure, optimized execution plan** that can be safely executed
against enterprise data systems.

You MUST think carefully, step by step, before producing the final structured output.

════════════════════════════════════════════════════════════
SECTION 1: DATABASE & PLATFORM CONTEXT (READ CAREFULLY)
════════════════════════════════════════════════════════════
Database category:
{databasetype}

This database category determines:

- The SQL dialect or query language

- Available functions

- Date handling logic

- Masking and security expression patterns

Database source metadata (tables, columns, schema, indexes, row counts):

{json.dumps(database_source, indent=2)}

You MUST:

- Use ONLY the schemas listed below

- Use ONLY the tables and columns provided

- NEVER invent tables, columns, or schemas

Selected schema names:

{selected_schema_names}

Allowed query patterns for this database engine:

{json.dumps(query_pattern, indent=2)}

Repeat for clarity:

- Database type: {databasetype}

- Selected schemas: {selected_schema_names}

════════════════════════════════════════════════════════════
SECTION 2: USER CONTEXT & ACCESS CONTROL (CRITICAL)
════════════════════════════════════════════════════════════
User context (roles, permissions, attributes):

{json.dumps(user_context, indent=2)}

This user context MUST be used to:

- Apply row-level security (RLS)

- Apply column masking rules

- Filter data by user attributes

- Prevent unauthorized data exposure

Repeat user context for grounding:

{json.dumps(user_context, indent=2)}

DO NOT:

- Ignore user roles

- Ignore permissions

- Assume broader access than explicitly allowed

════════════════════════════════════════════════════════════
SECTION 3: USER REQUEST & INTENT INFERENCE (PRIMARY DRIVER)
════════════════════════════════════════════════════════════
The user explicitly asked:

\"\"\"{user_prompt}\"\"\"

Repeat user request to anchor intent:

\"\"\"{user_prompt}\"\"\"

You MUST:

1. Understand what the user is asking in business terms

2. Translate the request into a technical intent

3. Select EXACTLY ONE intent_type from the list below

Allowed intent types:

{intent_types}

Rules:

- Choose the MOST specific intent

- Prefer "aggregate" or "analytics" when GROUP BY or ranking is required

- Do NOT invent new intent types

- If uncertain, choose the safest applicable intent

════════════════════════════════════════════════════════════
SECTION 4: GOVERNANCE POLICIES (MANDATORY ENFORCEMENT)
════════════════════════════════════════════════════════════
**CRITICAL IMPORTANCE**: Governance policies are the cornerstone of data security and compliance. These policies ensure that data access is controlled, sensitive information is protected, and users can only access data they are authorized to view. You must treat governance enforcement as the highest priority, as failure to properly apply these rules can result in data breaches, compliance violations, and unauthorized data exposure.

Governance policies provided:

{json.dumps(governance_policies, indent=2)}

**ROW-LEVEL SECURITY (RLS) ENFORCEMENT**: Row-level security rules restrict which rows a user can access based on their identity, roles, permissions, or attributes. These rules must be applied as WHERE clause filters in your SQL queries. When constructing queries, you MUST embed these RLS conditions directly into the WHERE clause or use Common Table Expressions (CTEs) to pre-filter data. Each RLS rule typically contains placeholders like {{user_id}}, {{user.attributes.assigned_region}}, {{workspace_id}}, or {{organization_id}} that must be replaced with actual values from the user_context provided earlier. The RLS rules act as mandatory filters that cannot be bypassed, ensuring users only see data rows they are authorized to access.

**COLUMN MASKING ENFORCEMENT**: Column masking rules protect sensitive Personally Identifiable Information (PII) and other confidential data by obscuring or transforming column values based on user attributes or conditions. When a masking rule is defined for a column, you must apply it using CASE expressions (for SQL databases) or equivalent conditional logic (for NoSQL databases). The masking function specified in the rule (such as email_mask, phone_mask, or custom masking functions) must be applied when the masking condition is met. For example, if a rule states that email addresses should be masked when the user's assigned_region does not match the data row's region, you must use a CASE statement that checks this condition and applies the masking function accordingly. Column masking ensures that even when users have access to query results, sensitive data remains protected according to organizational policies.

**GOVERNANCE_APPLIED FIELD REQUIREMENTS**: For each operation in your execution plan, you MUST include a governance_applied object that clearly documents which governance rules were applied. This object must contain two arrays: rls_rules and masking_rules. The rls_rules array should list the names or descriptions of all row-level security rules that were applied to the query, such as ["region_filter", "department_access"]. The masking_rules array should list the names or descriptions of all column masking rules that were applied, such as ["email_mask_for_external_regions", "ssn_masking"]. These arrays serve as documentation and audit trails, showing exactly which governance policies were enforced in the execution plan. You must ensure that every rule mentioned in the governance_policies that is applicable to the query is included in the appropriate array within governance_applied.

**ABSOLUTE GOVERNANCE REQUIREMENTS**: 

1. Governance CANNOT be skipped: Every applicable governance rule must be enforced. There are no exceptions or optional governance rules.

2. Governance CANNOT be weakened: You cannot modify, relax, or approximate governance rules. They must be applied exactly as specified.

3. Governance CANNOT be approximated: You must implement governance rules precisely, not with "similar" or "equivalent" logic. Use the exact conditions and functions specified in the policies.

4. All placeholders MUST be resolved: Replace all placeholders in governance rules (like {{user_id}}, {{user.attributes.assigned_region}}) with actual values from the user_context.

5. PII protection is mandatory: Never expose PII data (personally identifiable information like emails, phone numbers, SSNs) unless explicitly allowed by governance policies.

Repeat governance policies for emphasis and careful review:

{json.dumps(governance_policies, indent=2)}

════════════════════════════════════════════════════════════
SECTION 5: EXECUTION CONSTRAINTS & OPTIMIZATION
════════════════════════════════════════════════════════════
Execution constraints:

{json.dumps(execution_context, indent=2)}

You MUST:

- Respect max_rows limits

- Use pushdown execution when possible

- Prefer database-native execution

- Avoid unnecessary intermediate steps

Repeat execution constraints:

{json.dumps(execution_context, indent=2)}

════════════════════════════════════════════════════════════
SECTION 6: EXECUTION PLAN CONSTRUCTION (STEP-BY-STEP DETAILED)
════════════════════════════════════════════════════════════

**EXECUTION PLAN OVERVIEW**: An execution plan is a comprehensive blueprint that transforms the user's natural language request into an executable database operation. The execution plan must include a strategy (such as "pushdown" for executing directly on the database, "compute" for client-side processing, or "hybrid" for a combination), a type (such as "sql_query" or "nosql_query"), and a list of ordered operations. Each operation represents a discrete step in the data retrieval or transformation process, with clear dependencies, query statements, and governance enforcement.

**OPERATION CONSTRUCTION REQUIREMENTS**: Each operation in the execution plan must be a complete, executable unit that can run independently (subject to its dependencies). You must provide a step number (starting from 1), a unique step_id (such as "step_1", "op1", "query_initial"), an operation_type (such as "read", "write", "transform", "join"), and a type (such as "source_query", "transform", "aggregate"). The description field should provide a clear, paragraph-length explanation of what this operation accomplishes, why it is necessary, and how it fits into the overall execution plan. For example: "This operation retrieves customer records from the customers table, applying row-level security filters to ensure the user only sees customers in their assigned regions, and applies email masking for customers outside the user's assigned region to protect PII data."

**QUERY AND QUERY_PAYLOAD CONSTRUCTION**: The query field must contain the complete, executable SQL statement (or NoSQL query command) with all governance rules embedded. The query must use the correct SQL dialect for {databasetype}, including proper syntax for functions, data types, and operators. The query_payload object must mirror the query field and include: language (such as "sql" or "nosql"), dialect (the specific database dialect like "postgresql", "mysql", or null if not applicable), statement (the same SQL/query statement as the query field), and parameters (an array of parameter values if the query uses parameterized queries, otherwise an empty array). Both the query and query_payload.statement must be identical and contain the final, executable query with all filters, joins, aggregations, and governance rules applied.

**GOVERNANCE_APPLIED IN OPERATIONS**: Each operation MUST include a governance_applied object that documents all governance rules enforced in that operation's query. This is CRITICAL for audit trails and compliance verification. The governance_applied object must have two arrays: rls_rules (containing names/descriptions of all applied row-level security rules) and masking_rules (containing names/descriptions of all applied column masking rules). For example, if your query applies a region filter RLS rule and an email masking rule, the governance_applied should be: {{"rls_rules": ["region_filter_for_user_access"], "masking_rules": ["email_mask_for_external_regions"]}}. This documentation ensures that reviewers can verify that all required governance policies were properly enforced.

**DATA_SOURCE_ID, COMPUTE_TYPE, AND COMPUTE_ENGINE**: The data_source_id must match the data_source_id from the request's data_sources array. This identifies which data source the operation targets. The compute_type should indicate where the operation executes, typically "source_native" for operations that run directly on the database, "client_side" for operations processed in the application layer, or "hybrid" for operations that combine both approaches. The compute_engine specifies the execution engine, often "source_native" when executing on the database, or specific engine names for distributed processing systems. These fields help optimize execution by routing operations to the most efficient compute location.

**DEPENDENCIES AND OUTPUT_ARTIFACT**: The dependencies array should list step_ids of operations that must complete before this operation can execute. For the first operation in a plan, dependencies should be an empty array []. For subsequent operations that depend on previous steps, include the step_ids they depend on. The output_artifact field should specify a name for the result of this operation, such as "result_frame", "filtered_customers", or "aggregated_revenue". This helps track data flow through the execution plan.

**SQL CONSTRUCTION BEST PRACTICES**: 

1. **SQL Dialect Correctness**: Use the exact SQL syntax for {databasetype}. Different databases have different functions (e.g., PostgreSQL uses CONCAT, while SQL Server uses + for string concatenation). Reference the query patterns provided earlier for dialect-specific syntax.

2. **Date Filtering**: When the user requests "this quarter" or similar time-based filters, calculate the current quarter's start and end dates and use proper date comparison functions for {databasetype}. Use database-specific date functions like DATE_TRUNC for PostgreSQL, DATE_FORMAT for MySQL, or equivalent functions for other databases.

3. **Aggregation Functions**: Use appropriate aggregation functions (SUM, COUNT, AVG, MAX, MIN) with proper GROUP BY clauses. Ensure all non-aggregated columns in SELECT are included in GROUP BY.

4. **Ordering and Limiting**: Apply ORDER BY clauses to sort results meaningfully (e.g., ORDER BY revenue DESC for top revenue). Use LIMIT clauses to respect max_rows constraints from execution_context, ensuring results don't exceed the specified maximum.

5. **Join Operations**: When joining multiple tables, use explicit JOIN syntax (INNER JOIN, LEFT JOIN) rather than comma-separated tables. Specify join conditions clearly using ON clauses.

6. **Schema Qualification**: Prefix table names with schema names when multiple schemas exist (e.g., public.customers rather than just customers).

You MUST build a comprehensive execution plan with detailed operations that include all required fields and proper governance enforcement.

════════════════════════════════════════════════════════════
SECTION 7: VISUALIZATION & ANALYTICS ({'REQUIRED' if include_visualization else 'SKIP - Set visualization to null'})
════════════════════════════════════════════════════════════
{viz_instruction}

════════════════════════════════════════════════════════════
SECTION 8: AI METADATA, EXPLANATION, REASONING STEPS & SUGGESTIONS (REQUIRED)
════════════════════════════════════════════════════════════

**AI_METADATA REQUIREMENTS**: The ai_metadata object contains critical information about the AI's analysis, confidence assessment, and reasoning process. This metadata helps users understand how the execution plan was created and provides transparency into the AI's decision-making process.

**EXPLANATION FIELD (REQUIRED)**: The explanation field must be a concise paragraph (not bullet points) that provides a clear, brief description of the execution plan. Keep it concise - typically 2-4 sentences. The explanation should briefly describe: (1) what the execution plan accomplishes, (2) key tables/columns used, (3) how governance rules were applied, and (4) what query operations were performed. Write in clear, professional language but be concise and to the point. Avoid lengthy explanations - focus on the essential information.

**REASONING_STEPS ARRAY (REQUIRED, MINIMUM 2, MAXIMUM 5)**: The reasoning_steps field must be an array of strings, where each string is a concise step in the logical reasoning process. You MUST include at least 2 reasoning steps and at most 5 reasoning steps. Each step should be a concise, complete sentence that briefly explains a specific aspect of your reasoning. Keep each step brief and focused - one sentence per step is ideal. The steps should cover:

1. **Intent Identification**: Briefly state how you determined the intent type (e.g., "Identified intent as 'aggregate' based on user's request for 'top 10 customers by revenue' requiring ranking").

2. **Table and Column Selection**: Briefly state which tables/columns were selected and why (e.g., "Selected 'customers' table with columns: id, name, revenue, region, email to fulfill the request").

3. **Governance Application**: Briefly describe how governance rules were applied (e.g., "Applied RLS filter for user's assigned regions and email masking for external regions using CASE expression").

4. **Query Construction**: Briefly explain the query structure (e.g., "Constructed PostgreSQL query with ORDER BY revenue DESC and LIMIT 10 to return top customers").

5. **Visualization Selection** (if applicable): Briefly explain visualization choices (e.g., "Generated table and bar chart visualizations using 'name' for x_axis and 'revenue' for y_axis").

Keep each reasoning step concise - one clear sentence per step. Provide 2-5 steps total that cover the essential reasoning process.

**SUGGESTIONS ARRAY (REQUIRED FIELD, 1-2 SUGGESTIONS MAXIMUM 5)**: The suggestions field must be an array of strings that provides actionable recommendations. This field is REQUIRED and must always be present. Provide 1-2 suggestions (maximum 5 if you have many valuable suggestions). Each suggestion should be a concise, complete sentence with specific, actionable advice. Suggestions might include: (1) query optimization (e.g., "Consider adding an index on revenue column for better performance"), (2) additional filters (e.g., "Consider adding date range filter for time-based analysis"), (3) data quality (e.g., "Consider filtering NULL values for more accurate results"), or (4) visualization enhancements (e.g., "Consider adding a line chart to show trends over time"). Keep suggestions brief, specific, and actionable. If you have no meaningful suggestions, use an empty array [].

**CONFIDENCE AND CONFIDENCE_SCORE**: The confidence field should be a numeric value between 0 and 100 representing your confidence that the execution plan will correctly fulfill the user's request. The confidence_score should be the same value normalized to a 0.0 to 1.0 scale (so confidence 95 corresponds to confidence_score 0.95). High confidence (90-100) indicates you are very certain the plan is correct and will work as expected. Lower confidence indicates areas of uncertainty or potential issues. Consider factors such as: query correctness, governance rule application accuracy, data availability, syntax correctness for the database type, and alignment with user intent when assigning confidence scores.

════════════════════════════════════════════════════════════
SECTION 9: OUTPUT FORMAT (STRICT)
════════════════════════════════════════════════════════════
IMPORTANT OUTPUT RULES:

- Return ONLY valid JSON

- JSON MUST match the provided schema

- Do NOT include explanations outside JSON


- Use NULL if a value cannot be confidently determined

- NEVER hallucinate fields, tables, or values

FINAL REMINDER:

Return ONLY the JSON output. Nothing else.
"""

