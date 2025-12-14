from pydantic import BaseModel
from typing import List, Dict, Literal
import json

# Import shared database configuration constants
from database_config import (
    SQL_INTENT_TYPES,
    NON_SQL_INTENT_TYPES,
    SQL_TYPES,
    NOSQL_TYPES,
    SQL_TYPE_MAP,
    NON_SQL_TYPE_MAP,
    get_database_type_name,
    get_source_category
)


class IntentOutput(BaseModel):
    """Model for intent classification output."""
    intent_type: Literal[
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
        "index",
        "document_transform",
        "search",
        "stream"
    ]
    intent_summary: str
    source_category: Literal["sql", "non_sql"]
    needs_aggregation: bool
    needs_join: bool
    needs_time_filter: bool
    no_rows: int


def get_source_category_and_type(data_source_type: str) -> tuple:
    """
    Determine source category and database type name from data source type.
    
    Args:
        data_source_type: The data source type (e.g., "postgresql", "mongodb")
    
    Returns:
        tuple: (source_category, database_type_name)
    """
    source_category = get_source_category(data_source_type)
    database_type_name = get_database_type_name(data_source_type)
    
    return source_category, database_type_name


def build_intent_prompt(request: Dict, source_category: str, sql_type: str) -> tuple:
    """
    Build the intent classification prompt based on datasource type and SQL type.
    
    Args:
        request: The request dictionary containing user prompt, context, and data sources
        source_category: Either "sql" or "non_sql"
        sql_type: The specific database type (e.g., "PostgreSQL", "MySQL", "MongoDB")
    
    Returns:
        tuple: (system_instruction, prompt)
    """
    # Determine available intent types based on source category
    if source_category == "sql":
        available_intent_types = SQL_INTENT_TYPES
        intent_type_description = "SQL intent types: " + ", ".join(SQL_INTENT_TYPES)
    else:
        available_intent_types = NON_SQL_INTENT_TYPES
        intent_type_description = "Non-SQL intent types: " + ", ".join(NON_SQL_INTENT_TYPES)
    
    # Build system instruction
    intent_system_instruction = f"""
    You are an intent classification agent specialized in analyzing user queries for {sql_type} databases.
    Your task is to identify the user's intent based on their prompt, schema context, available tables/collections, and execution context.
    
    Database Type: {sql_type}
    Source Category: {source_category}
    Available Intent Types: {intent_type_description}
    
    Analyze the user prompt carefully and determine:
    1. The primary intent type from the available types for {sql_type}
    2. Whether aggregation is needed (GROUP BY, aggregate functions, or aggregation pipelines)
    3. Whether joins are required (SQL JOINs, $lookup in MongoDB, or multi-collection queries)
    4. Whether time-based filtering is needed (date ranges, temporal queries, TTL considerations)
    5. Estimated number of rows/documents to return
    
    Consider {sql_type}-specific capabilities and limitations when classifying the intent.
    Return only valid JSON matching the IntentOutput schema.
    """
    
    # Build the prompt with proper placeholders and datasource information
    data_source = request['data_sources'][0]
    datasource_name = data_source.get('name', 'Unknown')
    datasource_type = data_source.get('type', 'Unknown')
    
    # Format governance policies if present
    governance_info = ""
    if 'governance_policies' in data_source:
        governance_info = f"""
    Governance Policies:
    {json.dumps(data_source['governance_policies'], indent=2)}
        """
    
    intent_prompt = f"""
    User Prompt:
    {request['user_prompt']}

    Data Source Information:
    - Data Source Name: {datasource_name}
    - Data Source Type: {datasource_type}
    - Database Type: {sql_type}
    - Source Category: {source_category}

    User Context:
    - User ID: {request['user_context'].get('user_id')}
    - Workspace ID: {request['user_context'].get('workspace_id')}
    - Organization ID: {request['user_context'].get('organization_id')}
    - Roles: {request['user_context'].get('roles', [])}
    - Permissions: {request['user_context'].get('permissions', [])}
    - Attributes: {json.dumps(request['user_context'].get('attributes', {}), indent=2)}
    {governance_info}
    Available Tables/Collections and Schemas:
    {json.dumps(request['data_sources'][0]['schemas'], indent=2)}

    Execution Context:
    - Max Rows: {request['execution_context'].get('max_rows', 1000)}
    - Timeout: {request['execution_context'].get('timeout_seconds', 30)} seconds

    Based on the above information and {sql_type}-specific capabilities, analyze the user's intent and return the intent classification.
    Make sure to select the intent_type from the available {source_category} intent types: {', '.join(available_intent_types)}
    Consider the database-specific features and syntax when determining the intent.
    """
    
    return intent_system_instruction, intent_prompt


def classify_intent(service, request: Dict, data_source_index: int = 0) -> Dict:
    """
    Classify user intent based on the request.
    
    Args:
        service: AIService instance for generating responses
        request: The request dictionary containing user prompt, context, and data sources
        data_source_index: Index of the data source to use (default: 0)
    
    Returns:
        Dictionary containing the intent classification result
    """
    # Determine source type and category
    source_type = request["data_sources"][data_source_index]["type"]
    source_category, sql_type = get_source_category_and_type(source_type)
    
    # Build the prompt with datasource type and SQL type
    intent_system_instruction, intent_prompt = build_intent_prompt(request, source_category, sql_type)
    
    # Generate intent classification
    intent_result, tokens = service.generate_response(
        intent_system_instruction,
        intent_prompt,
        IntentOutput
    )
    
    return intent_result, tokens
