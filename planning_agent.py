from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import json

# Import shared database configuration constants
from database_config import (
    get_database_type_name,
    get_source_category,
    get_database_dialect,
    get_database_query_guidance,
    get_database_language
)


class QueryParameter(BaseModel):
    """A single query parameter."""
    name: str
    value: str

class QueryPayload(BaseModel):
    """Payload for query operations."""
    query_type: str
    parameters: List[QueryParameter] = []
    filters: List[str] = []
    projections: List[str] = []
    sort_field: Optional[str] = None
    sort_order: Optional[str] = None
    limit: Optional[int] = None
    offset: Optional[int] = None


class ColumnMaskingInfo(BaseModel):
    """Information about a single column masking rule."""
    column: str
    condition: str
    masking_function: str

class GovernanceApplied(BaseModel):
    """Information about applied governance rules."""
    row_filters: List[str] = []
    column_masking: List[ColumnMaskingInfo] = []
    applied_rules: List[str] = []


class CommandStep(BaseModel):
    """A single step in the execution plan."""
    step: int
    step_id: str
    operation_type: str
    type: str
    description: str
    data_source_id: int
    compute_type: str
    compute_engine: str
    dependencies: List[str]
    query: str
    query_payload: QueryPayload
    governance_applied: GovernanceApplied
    output_artifact: str


class ExecutionPlan(BaseModel):
    """Complete execution plan with strategy and operations."""
    strategy: str
    type: str
    operations: List[CommandStep]


def get_planning_system_instruction(
    intent_type: str,
    source_category: str,
    database_type: str,
    data_source_type: str
) -> str:
    """
    Generate system instruction for planning agent based on database type and intent.
    
    Args:
        intent_type: The intent type (query, write, aggregate, etc.)
        source_category: Either "sql" or "non_sql"
        database_type: The database type name (e.g., "PostgreSQL", "MongoDB")
        data_source_type: The raw data source type (e.g., "postgresql", "mongodb")
    
    Returns:
        str: The system instruction tailored to the context
    """
    # Determine operation type based on intent
    if intent_type in ["query", "aggregate", "analytics", "join", "schema_inspection"]:
        operation_type = "read/query operations"
    elif intent_type in ["write"]:
        operation_type = "write operations"
    elif intent_type in ["transform", "pipeline"]:
        operation_type = "data transformation operations"
    else:
        operation_type = "database operations"
    
    # Get database-specific query guidance
    query_guidance = get_database_query_guidance(data_source_type, source_category)
    dialect = get_database_dialect(data_source_type)
    language = get_database_language(data_source_type)
    
    system_instruction = f"""
You are an execution planning agent specialized in creating detailed execution plans for {database_type} database operations.

Context:
- Database Type: {database_type}
- Database Dialect: {dialect}
- Query Language: {language}
- Source Category: {source_category}
- Intent Type: {intent_type} ({operation_type})

Your primary responsibilities:
1. Analyze the user prompt, intent classification, and governance rules
2. Create a comprehensive execution plan with step-by-step operations
3. Generate actual {database_type} queries/commands that implement the user's request
4. Apply governance rules (row-level security and column masking) to the queries
5. Define proper query payloads with filters, projections, sorting, and limits
6. Specify compute requirements and dependencies between steps
7. Create a strategy that optimizes for {database_type} performance and security

Key Guidelines:
- Generate actual {database_type} queries/commands using {dialect} syntax
- Break down complex operations into logical steps with clear dependencies
- Apply all governance rules (row filters and column masking) to the queries
- Use proper {database_type} syntax, functions, and best practices
- Include proper error handling and optimization considerations
- Specify compute_type (e.g., "query", "aggregation", "join", "write")
- Specify compute_engine matching the database type ({database_type})
- Create unique step_id for each operation
- Define output_artifact names for intermediate and final results

{query_guidance}

Return only valid JSON matching the ExecutionPlan schema.
"""
    
    return system_instruction


def build_planning_prompt(
    request: Dict,
    intent_result: Dict,
    governance_result: Dict,
    data_source_index: int = 0
) -> str:
    """
    Build the planning prompt with all necessary context.
    
    Args:
        request: The request dictionary containing user prompt, context, and data sources
        intent_result: The intent classification result
        governance_result: The governance application result
        data_source_index: Index of the data source to use (default: 0)
    
    Returns:
        str: The detailed planning prompt
    """
    # Extract information
    user_prompt = request.get('user_prompt', '')
    user_context = request.get('user_context', {})
    data_source = request['data_sources'][data_source_index]
    datasource_name = data_source.get('name', 'Unknown')
    datasource_type = data_source.get('type', 'Unknown')
    execution_context = request.get('execution_context', {})
    
    # Get database type and related information
    database_type = get_database_type_name(datasource_type)
    source_category = intent_result.get('source_category', 'unknown')
    intent_type = intent_result.get('intent_type', 'unknown')
    dialect = get_database_dialect(datasource_type)
    language = get_database_language(datasource_type)
    
    # Extract detailed table/collection information with column types
    tables_info = []
    for schema in data_source.get('schemas', []):
        schema_name = schema.get('schema_name', '')
        for table in schema.get('tables', []):
            columns_detail = []
            for col in table.get('columns', []):
                col_info = {
                    'column_name': col.get('column_name', ''),
                    'column_type': col.get('column_type', 'unknown'),
                    'is_pii': col.get('is_pii', False),
                    'is_nullable': col.get('is_nullable', True)
                }
                columns_detail.append(col_info)
            
            table_info = {
                'schema_name': schema_name,
                'table_name': table.get('table_name', ''),
                'table_type': table.get('table_type', 'table'),
                'columns': columns_detail
            }
            tables_info.append(table_info)
    
    planning_prompt = f"""
=== USER REQUEST ===

User Prompt: "{user_prompt}"

Request ID: {request.get('request_id', 'N/A')}
Execution ID: {request.get('execution_id', 'N/A')}

=== INTENT CLASSIFICATION ===

Intent Type: {intent_type}
Intent Summary: {intent_result.get('intent_summary', '')}
Source Category: {source_category}
Needs Aggregation: {intent_result.get('needs_aggregation', False)}
Needs Join: {intent_result.get('needs_join', False)}
Needs Time Filter: {intent_result.get('needs_time_filter', False)}
Expected Rows: {intent_result.get('no_rows', 0)}

=== DATA SOURCE INFORMATION ===

Data Source ID: {data_source.get('data_source_id', 0)}
Data Source Name: {datasource_name}
Database Type: {database_type}
Database Dialect: {dialect}
Query Language: {language}
Source Type: {datasource_type}
Source Category: {source_category}

Available Tables/Collections (with column details):
{json.dumps(tables_info, indent=2)}

=== GOVERNANCE RULES ===

Row Filters to Apply:
{json.dumps(governance_result.get('row_filters', []), indent=2)}

Column Masking Rules:
{json.dumps(governance_result.get('column_masking_rules', []), indent=2)}

Governance Applied:
{json.dumps(governance_result.get('governance_applied', []), indent=2)}

Governance Impact:
{governance_result.get('governance_impact', '')}

Planning Notes:
{json.dumps(governance_result.get('planning_notes', []), indent=2)}

=== EXECUTION CONTEXT ===

Max Rows: {execution_context.get('max_rows', 1000)}
Timeout: {execution_context.get('timeout_seconds', 30)} seconds

=== USER CONTEXT ===

User ID: {user_context.get('user_id')}
Workspace ID: {user_context.get('workspace_id')}
Organization ID: {user_context.get('organization_id')}
Roles: {', '.join(user_context.get('roles', []))}
Permissions: {', '.join(user_context.get('permissions', []))}

=== YOUR TASK ===

Create a detailed execution plan for executing the user's request on {database_type}.

Requirements:
1. **Strategy**: Define the overall execution strategy (e.g., "single_query", "multi_step_aggregation", "join_with_governance", "pipeline")

2. **Type**: Specify the plan type (e.g., "query", "write", "transform", "pipeline")

3. **Operations**: Create one or more CommandStep objects with:
   - step: Sequential step number (1, 2, 3, ...)
   - step_id: Unique identifier (e.g., "step_1_query", "step_2_aggregate")
   - operation_type: Type of operation (e.g., "query", "aggregate", "join", "write", "transform")
   - type: Same as operation_type or more specific
   - description: Clear description of what this step does
   - data_source_id: The data source ID ({data_source.get('data_source_id', 0)})
   - compute_type: Type of computation (e.g., "query", "aggregation", "join", "write")
   - compute_engine: The database engine ({database_type})
   - dependencies: List of step_ids this step depends on (empty for first step)
   - query: The actual {database_type} query/command with governance rules applied
     - query_payload: QueryPayload object with:
     - query_type: Type of query (e.g., "select", "aggregate", "find", "update")
     - parameters: List of QueryParameter objects with name and value fields
     - filters: List of filter conditions (including governance row filters)
     - projections: List of columns/fields to select (with masking applied)
     - sort_field: Field name to sort by (if sorting needed)
     - sort_order: Sort order ("asc" or "desc")
     - limit: Limit on results
     - offset: Offset for pagination if needed
   - governance_applied: GovernanceApplied object with:
     - row_filters: List of row filters applied
     - column_masking: List of ColumnMaskingInfo objects with column, condition, and masking_function
     - applied_rules: List of descriptions of applied rules
   - output_artifact: Name for the output (e.g., "result_set_1", "aggregated_data", "final_results")

4. **Query Generation**:
   - Generate actual {database_type} queries/commands using {dialect} syntax
   - Apply all row-level security filters from governance rules
   - Apply all column masking rules from governance rules
   - Use proper {database_type} syntax and best practices
   - For SQL databases: Include all necessary clauses (SELECT, FROM, WHERE, GROUP BY, ORDER BY, LIMIT)
   - For non-SQL databases: Use appropriate query syntax for {database_type}:
     * MongoDB: Use find() or aggregate() with proper filter and projection syntax
     * Cassandra: Use CQL SELECT with partition key and clustering key requirements
     * Redis: Use appropriate key-based operations or SCAN with patterns
     * DynamoDB: Use Query or Scan with KeyConditionExpression and FilterExpression
     * Elasticsearch: Use JSON query DSL with proper query structure
   - Reference the database-specific query patterns provided in the system instruction

5. **Query Payload**:
   - Set language field to "{language}"
   - Set dialect field to "{dialect}"
   - Set statement field to the actual {database_type} query/command
   - Include all parameters, filters, projections, sorting, and limits in the query_payload

6. **Optimization**:
   - Consider the intent type ({intent_type}) when structuring the plan
   - Break complex operations into logical steps if needed
   - Ensure dependencies are correctly specified
   - Optimize for {database_type} performance using {dialect}-specific best practices

Return a complete ExecutionPlan with all steps needed to execute the user's request while applying all governance rules.
"""
    
    return planning_prompt


def create_execution_plan(
    service,
    request: Dict,
    intent_result: Dict,
    governance_result: Dict,
    data_source_index: int = 0
) -> Dict:
    """
    Create an execution plan based on request, intent, and governance results.
    
    Args:
        service: AIService instance for generating responses
        request: The request dictionary containing user prompt, context, and data sources
        intent_result: The intent classification result
        governance_result: The governance application result
        data_source_index: Index of the data source to use (default: 0)
    
    Returns:
        Dictionary containing the execution plan
    """
    # Get database information
    data_source = request['data_sources'][data_source_index]
    datasource_type = data_source.get('type', 'Unknown')
    database_type = get_database_type_name(datasource_type)
    source_category = intent_result.get('source_category', 'unknown')
    intent_type = intent_result.get('intent_type', 'unknown')
    
    # Build system instruction with database-specific details
    system_instruction = get_planning_system_instruction(
        intent_type, source_category, database_type, datasource_type
    )
    
    # Build prompt
    planning_prompt = build_planning_prompt(
        request, intent_result, governance_result, data_source_index
    )
    
    # Generate execution plan
    execution_plan, tokens = service.generate_response(
        system_instruction,
        planning_prompt,
        ExecutionPlan
    )
    
    return execution_plan, tokens

