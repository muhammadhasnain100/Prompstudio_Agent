"""Prompt building functions for unified agent processing."""

from typing import Dict, Tuple
import json

# Import shared database configuration constants
from core.database import (
    SQL_INTENT_TYPES,
    NON_SQL_INTENT_TYPES,
    get_database_type_name,
    get_source_category,
    get_database_dialect,
    get_database_language
)


def get_source_category_and_type(data_source_type: str) -> Tuple[str, str]:
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


def build_unified_prompt(
    request: Dict,
    data_source_index: int = 0,
    include_visualization: bool = False
) -> Tuple[str, str]:
    """
    Build a unified prompt that combines all agent tasks into one comprehensive prompt.
    
    Args:
        request: The request dictionary containing user prompt, context, and data sources
        data_source_index: Index of the data source to use (default: 0)
        include_visualization: Whether to include visualization generation (default: False)
    
    Returns:
        tuple: (system_instruction, prompt)
    """
    # Extract information
    user_prompt = request.get('user_prompt', '')
    user_context = request.get('user_context', {})
    data_source = request['data_sources'][data_source_index]
    datasource_name = data_source.get('name', 'Unknown')
    datasource_type = data_source.get('type', 'Unknown')
    execution_context = request.get('execution_context', {})
    
    # Determine source category and database type
    source_category, database_type = get_source_category_and_type(datasource_type)
    dialect = get_database_dialect(datasource_type)
    language = get_database_language(datasource_type)
    
    # Determine available intent types
    if source_category == "sql":
        available_intent_types = SQL_INTENT_TYPES
        intent_type_description = "SQL intent types: " + ", ".join(SQL_INTENT_TYPES)
    else:
        available_intent_types = NON_SQL_INTENT_TYPES
        intent_type_description = "Non-SQL intent types: " + ", ".join(NON_SQL_INTENT_TYPES)
    
    # Extract detailed table information
    tables_info = []
    for schema in data_source.get('schemas', []):
        schema_name = schema.get('schema_name', '')
        for table in schema.get('tables', []):
            table_info = {
                'schema_name': schema_name,
                'table_name': table.get('table_name', ''),
                'table_type': table.get('table_type', 'table'),
                'row_count': table.get('row_count', 0),
                'indexes': table.get('indexes', []),
                'columns': []
            }
            
            for col in table.get('columns', []):
                col_info = {
                    'column_name': col.get('column_name', ''),
                    'column_type': col.get('column_type', ''),
                    'is_nullable': col.get('is_nullable', True),
                    'is_primary_key': col.get('is_primary_key', False),
                    'is_foreign_key': col.get('is_foreign_key', False),
                    'pii': col.get('pii', False),
                    'column_comment': col.get('column_comment', '')
                }
                table_info['columns'].append(col_info)
            
            tables_info.append(table_info)
    
    # Build user attributes string
    user_attributes = user_context.get('attributes', {})
    user_attrs_str = "\n".join([f"  - {key} = {value}" for key, value in user_attributes.items()])
    if not user_attrs_str:
        user_attrs_str = "  (no attributes defined)"
    
    # Format governance policies if present
    governance_policies = data_source.get('governance_policies', {})
    governance_info = json.dumps(governance_policies, indent=2) if governance_policies else "  (no governance policies defined)"
    
    # Build comprehensive system instruction
    system_instruction = f"""
You are an advanced AI agent specialized in processing database queries for {database_type} databases. You need to complete ALL of the following tasks in a single comprehensive analysis:

TASK 1: INTENT CLASSIFICATION
- Analyze the user prompt and determine the intent type from: {intent_type_description}
- Determine if aggregation, joins, or time filters are needed
- Estimate the number of rows expected
- Source Category: {source_category}
- Database Type: {database_type}

TASK 2: GOVERNANCE APPLICATION
- Analyze governance policies and determine which rules apply
- Resolve placeholders ({{user_id}}, {{user.attributes.*}}, etc.) with actual values
- Generate row-level security filters for {database_type} syntax
- Generate column masking rules for sensitive data (PII)
- Explain governance impact and provide planning notes
- Database Type: {database_type}
- Source Category: {source_category}

TASK 3: EXECUTION PLANNING
- Create a detailed execution plan with step-by-step operations
- Generate actual {database_type} queries/commands using {dialect} syntax
- Apply all governance rules (row filters and column masking) to queries
- Define query payloads with filters, projections, sorting, and limits
- Specify compute requirements and dependencies
- Language: {language}
- Dialect: {dialect}

TASK 4: VISUALIZATION RECOMMENDATION{" (REQUIRED)" if include_visualization else " (OPTIONAL - only include if include_visualization is true)"}
- Analyze the execution plan and recommend appropriate visualizations
- Recommend 1-3+ visualizations based on data structure and intent
- Always include a table visualization as primary
- Provide appropriate titles, axis labels, and configuration options

TASK 5: ANALYSIS AND VALIDATION
- Analyze the execution plan for quality, correctness, and completeness
- Provide confidence score (0-100) with explanation
- List reasoning steps
- Provide actionable suggestions for improvement

IMPORTANT: You must return ALL results in a single structured JSON response matching the UnifiedOutput schema. Process everything in one comprehensive analysis.
"""

    # Build comprehensive user prompt
    prompt = f"""
=== USER REQUEST ===

User Prompt: "{user_prompt}"

Request ID: {request.get('request_id', 'N/A')}
Execution ID: {request.get('execution_id', 'N/A')}

=== USER CONTEXT ===

User Identity:
  - User ID: {user_context.get('user_id', 'N/A')}
  - Workspace ID: {user_context.get('workspace_id', 'N/A')}
  - Organization ID: {user_context.get('organization_id', 'N/A')}
  - Roles: {', '.join(user_context.get('roles', []))}
  - Permissions: {', '.join(user_context.get('permissions', []))}

User Attributes:
{user_attrs_str}

These attributes are used to resolve placeholders in governance rules (e.g., {{user.attributes.assigned_region}}, {{user_id}}, {{workspace_id}}, {{organization_id}}).

=== DATA SOURCE INFORMATION ===

Data Source ID: {data_source.get('data_source_id', 0)}
Data Source Name: {datasource_name}
Database Type: {database_type}
Database Dialect: {dialect}
Query Language: {language}
Source Type: {datasource_type}
Source Category: {source_category}

Available Tables/Collections and Schema Details:
{json.dumps(tables_info, indent=2)}

=== GOVERNANCE POLICIES ===

{governance_info}

=== EXECUTION CONTEXT ===

Max Rows: {execution_context.get('max_rows', 1000)}
Timeout: {execution_context.get('timeout_seconds', 30)} seconds

=== YOUR COMPREHENSIVE TASK ===

You need to complete ALL of the following in ONE comprehensive analysis:

1. **INTENT CLASSIFICATION**:
   - Classify the intent type from: {', '.join(available_intent_types)}
   - Determine intent summary, source category, aggregation needs, join needs, time filter needs, and expected rows

2. **GOVERNANCE APPLICATION**:
   - Review governance policies and determine applicable rules
   - Resolve ALL placeholders with actual user context values
   - Generate row filters for {database_type} ({source_category}) syntax
   - Generate column masking rules with conditions and masking functions
   - Explain governance impact and provide planning notes

3. **EXECUTION PLANNING**:
   - Create execution plan with strategy and operations
   - Generate actual {database_type} queries/commands with {dialect} syntax
   - Apply ALL governance rules (row filters and column masking) to the queries
   - Set query_payload with language="{language}", dialect="{dialect}", statement containing the actual query, and parameters (empty array if none)
   - Include proper filters, projections, sorting, and limits
   - For each operation, set governance_applied with rls_rules (array of rule names) and masking_rules (array of masking rule names)

4. **VISUALIZATION RECOMMENDATION{" (REQUIRED)" if include_visualization else " (OPTIONAL)"}**:
   {"- Analyze execution plan and recommend 1-3+ visualizations" if include_visualization else "- Skip visualization if not needed"}
   - Include table as primary visualization
   - Provide appropriate chart types based on data structure and intent

5. **ANALYSIS AND VALIDATION**:
   - Analyze execution plan quality, correctness, and completeness
   - Provide confidence score (0-100) and explanation
   - List reasoning steps
   - Provide suggestions for improvement

Return a complete UnifiedOutput JSON with all results from tasks 1-5.
"""

    return system_instruction, prompt

