from pydantic import BaseModel
from typing import List, Dict, Optional
import json

# Import shared database configuration constants
from database_config import (
    SQL_TYPE_MAP,
    NON_SQL_TYPE_MAP,
    get_database_type_name
)


class ColumnMaskingRule(BaseModel):
    """Model for column masking rules."""
    column: str
    condition: str
    masking_function: str
    description: Optional[str] = None


class GovernanceOutput(BaseModel):
    """Model for governance output containing row filters and masking rules."""
    row_filters: List[str]
    column_masking_rules: List[ColumnMaskingRule]
    governance_applied: List[str]
    governance_impact: str  # How governance rules will help for the input prompt
    planning_notes: List[str]  # Notes to help with command planning


def get_governance_system_instruction(
    intent_type: str,
    source_category: str,
    database_type: str
) -> str:
    """
    Generate system instruction based on intent type, source category, and database type.
    
    Args:
        intent_type: The intent type (query, write, aggregate, etc.)
        source_category: Either "sql" or "non_sql"
        database_type: The database type name (e.g., "PostgreSQL", "MongoDB")
    
    Returns:
        str: The system instruction tailored to the context
    """
    # Determine operation type based on intent
    if intent_type in ["query", "aggregate", "analytics", "join", "schema_inspection"]:
        operation_type = "read/query operations"
        operation_desc = "reading and querying data"
    elif intent_type in ["write"]:
        operation_type = "write operations (INSERT, UPDATE, DELETE)"
        operation_desc = "modifying data"
    elif intent_type in ["transform", "pipeline"]:
        operation_type = "data transformation operations"
        operation_desc = "transforming and processing data"
    else:
        operation_type = "database operations"
        operation_desc = "performing database operations"
    
    # Database-specific guidance
    if source_category == "sql":
        db_guidance = f"""
- For {database_type} databases, governance rules apply to SQL queries
- Row-level security filters translate to WHERE clause conditions
- Column masking applies to SELECT projections and result sets
- Consider {database_type}-specific syntax and capabilities when applying rules
"""
    else:
        db_guidance = f"""
- For {database_type} databases, governance rules apply to query/find operations
- Row-level security filters translate to query filters or match conditions
- Column masking applies to projection/field selection in results
- Consider {database_type}-specific query syntax and capabilities when applying rules
"""
    
    system_instruction = f"""
You are a data governance agent specialized in applying row-level security (RLS) and column masking rules to {database_type} database operations.

Context:
- Database Type: {database_type}
- Source Category: {source_category}
- Intent Type: {intent_type} ({operation_type})
- Operation: {operation_desc}

Your primary responsibilities:
1. Analyze the user prompt and intent type to determine which governance rules should be applied
2. Review the complete governance_policies object provided in the context
3. Resolve placeholders in governance rules with actual user context values
4. Generate row-level security filters appropriate for {database_type} {operation_type}
5. Generate column masking rules that protect sensitive data (PII, confidential information)
6. Explain how these governance rules will help protect data while allowing legitimate access
7. Provide planning notes that will help in constructing secure {database_type} commands

Key Guidelines:
- DO NOT generate actual {database_type} queries or database commands
- Focus on identifying which governance rules from the provided governance_policies apply
- Resolve placeholders like {{user_id}}, {{user.attributes.*}} with actual values from user context
- For row filters, provide filter conditions appropriate for {database_type} syntax
- For column masking, specify which columns need masking, under what conditions, and what masking function to use
- Consider the intent type ({intent_type}) when determining which rules are relevant
- Explain the governance impact: how these rules protect data while enabling the user's legitimate query needs
- Provide planning notes that will guide the construction of secure, compliant {database_type} commands
{db_guidance}
Return only valid JSON matching the GovernanceOutput schema.
"""
    
    return system_instruction


def resolve_placeholders(condition: str, user_context: Dict) -> str:
    """
    Resolve placeholders in governance rule conditions with actual user context values.
    
    Args:
        condition: The condition string with placeholders
        user_context: User context dictionary
    
    Returns:
        Resolved condition string
    """
    resolved = condition
    
    # Replace {user_id}
    if "{user_id}" in resolved:
        resolved = resolved.replace("{user_id}", str(user_context.get("user_id", "")))
    
    # Replace {user.attributes.*} patterns
    user_attributes = user_context.get("attributes", {})
    for key, value in user_attributes.items():
        placeholder = f"{{user.attributes.{key}}}"
        if placeholder in resolved:
            # Handle string values - add quotes if needed
            if isinstance(value, str):
                resolved = resolved.replace(placeholder, f"'{value}'")
            else:
                resolved = resolved.replace(placeholder, str(value))
    
    # Replace {workspace_id}
    if "{workspace_id}" in resolved:
        resolved = resolved.replace("{workspace_id}", str(user_context.get("workspace_id", "")))
    
    # Replace {organization_id}
    if "{organization_id}" in resolved:
        resolved = resolved.replace("{organization_id}", str(user_context.get("organization_id", "")))
    
    return resolved


def build_governance_prompt(
    request: Dict,
    intent_result: Dict,
    data_source_index: int = 0
) -> str:
    """
    Build a detailed governance prompt with comprehensive context for the governance agent.
    
    Args:
        request: The request dictionary containing user prompt, context, and data sources
        intent_result: The intent classification result
        data_source_index: Index of the data source to use (default: 0)
    
    Returns:
        str: The detailed governance prompt
    """
    # Extract user context
    user_context = request.get('user_context', {})
    user_attributes = user_context.get('attributes', {})
    user_prompt = request.get('user_prompt', '')
    
    # Extract data source information
    data_source = request['data_sources'][data_source_index]
    datasource_name = data_source.get('name', 'Unknown')
    datasource_type = data_source.get('type', 'Unknown')
    governance_policies = data_source.get('governance_policies', {})
    
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
            
            # Extract column details
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
    user_attrs_str = "\n".join([f"  - {key} = {value}" for key, value in user_attributes.items()])
    if not user_attrs_str:
        user_attrs_str = "  (no attributes defined)"
    
    # Get intent and source information
    intent_type = intent_result.get('intent_type', 'unknown')
    source_category = intent_result.get('source_category', 'unknown')
    
    # Determine proper database type name using shared function
    database_type = get_database_type_name(datasource_type)
    
    # Pass the complete governance_policies object
    governance_prompt = f"""
=== USER REQUEST CONTEXT ===

User Prompt:
"{user_prompt}"

This is the original user request that needs to be executed. The governance rules must be applied to ensure data security and compliance while allowing this query to proceed.

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

=== INTENT CLASSIFICATION ===

Intent Type: {intent_type}
Intent Summary: {intent_result.get('intent_summary', '')}
Source Category: {source_category}
Needs Aggregation: {intent_result.get('needs_aggregation', False)}
Needs Join: {intent_result.get('needs_join', False)}
Needs Time Filter: {intent_result.get('needs_time_filter', False)}
Expected Rows: {intent_result.get('no_rows', 0)}

The intent type ({intent_type}) and source category ({source_category}) help determine which governance rules are relevant and how they should be applied for {database_type} operations.

=== DATA SOURCE INFORMATION ===

Data Source Name: {datasource_name}
Database Type: {database_type}
Source Type: {datasource_type}
Source Category: {source_category}

Available Tables/Collections and Schema Details:
{json.dumps(tables_info, indent=2)}

This detailed schema information helps you understand:
- Which tables/collections and columns/fields are involved in the query
- Which columns/fields contain PII or sensitive data
- Table/collection relationships and structure
- Column/field types and constraints

=== COMPLETE GOVERNANCE POLICIES ===

The complete governance_policies object is provided below. Review all policies and determine which ones apply based on the intent type ({intent_type}), database type ({database_type}), and user context.

{json.dumps(governance_policies, indent=2)}

The governance_policies object contains:
- row_level_security: Rules for restricting row/document access based on conditions
- column_masking: Rules for masking sensitive column/field values
- Any other policy types defined in the object

Note: The governance policies structure may vary in production. Analyze the complete object structure and apply all relevant rules based on:
1. The intent type ({intent_type}) - different rules may apply for read vs write operations
2. The database type ({database_type}) - rules may be database-specific
3. The source category ({source_category}) - SQL vs non-SQL may have different rule formats
4. The user context and attributes - to resolve placeholders and determine applicability

=== YOUR TASK ===

Based on the above context, you need to:

1. **Analyze Governance Policies**: 
   - Review the complete governance_policies object structure
   - Identify all policy types (row_level_security, column_masking, etc.)
   - Understand the rule structure and conditions for {database_type}

2. **Determine Applicable Rules Based on Intent**: 
   - Consider the intent type ({intent_type}) - some rules may only apply to read operations, others to write operations
   - Analyze the user prompt to identify which tables/collections and columns/fields are likely to be accessed
   - Match user attributes and context to rule conditions
   - Consider {database_type}-specific rule applicability

3. **Resolve Placeholders**:
   - Replace {{user_id}} with actual user ID: {user_context.get('user_id', '')}
   - Replace {{user.attributes.*}} with actual attribute values from the user context
   - Replace {{workspace_id}} with: {user_context.get('workspace_id', '')}
   - Replace {{organization_id}} with: {user_context.get('organization_id', '')}
   - Handle any other placeholders found in the governance policies

4. **Generate Row Filters**:
   - Create filter conditions appropriate for {database_type} ({source_category})
   - For SQL databases: WHERE clause conditions
   - For non-SQL databases: query filter/match conditions
   - Ensure filters are specific to the user's context and attributes
   - Make filters applicable to the tables/collections involved in the query

5. **Generate Column Masking Rules**:
   - Identify which columns/fields need masking based on the query, user context, and intent type
   - Specify the masking function to use (e.g., email_mask, partial_mask, hash_mask, redact)
   - Define conditions under which masking should be applied
   - Consider {database_type}-specific masking approaches

6. **Explain Governance Impact**:
   - Describe how these governance rules will help protect sensitive data for this specific query
   - Explain how they enable legitimate access while maintaining security
   - Note any specific protections for PII or confidential information
   - Explain how the rules are tailored for {intent_type} operations on {database_type}

7. **Provide Planning Notes**:
   - List considerations for constructing secure {database_type} commands
   - Note any special handling needed for the governance rules based on intent type ({intent_type})
   - Suggest how to integrate these rules into the query execution plan for {database_type}
   - Include notes about {source_category}-specific implementation considerations

=== OUTPUT REQUIREMENTS ===

Return a JSON object with:
- row_filters: List of filter conditions to apply (formatted for {database_type} {source_category} syntax)
- column_masking_rules: List of masking rules with column, condition, masking_function, and description
- governance_applied: List of descriptions of which governance rules from the policies are being applied
- governance_impact: A detailed explanation of how these rules protect data while enabling the {intent_type} operation
- planning_notes: List of notes that will help in planning and constructing secure {database_type} commands for this {intent_type} operation

Remember: 
- Do NOT generate actual {database_type} queries or commands
- Only provide the governance rules and conditions that should be applied
- Consider the intent type ({intent_type}) and database type ({database_type}) when formatting rules
- The governance_policies structure may vary - analyze the complete object provided
"""
    
    return governance_prompt


def apply_governance(
    service,
    request: Dict,
    intent_result: Dict,
    data_source_index: int = 0
) -> Dict:
    """
    Apply governance rules based on the request and intent.
    
    Args:
        service: AIService instance for generating responses
        request: The request dictionary containing user prompt, context, and data sources
        intent_result: The intent classification result
        data_source_index: Index of the data source to use (default: 0)
    
    Returns:
        Dictionary containing the governance output
    """
    # Extract information for system instruction
    intent_type = intent_result.get('intent_type', 'unknown')
    source_category = intent_result.get('source_category', 'unknown')
    
    # Get database type
    data_source = request['data_sources'][data_source_index]
    datasource_type = data_source.get('type', 'Unknown')
    database_type = get_database_type_name(datasource_type)
    
    # Build dynamic system instruction
    system_instruction = get_governance_system_instruction(
        intent_type, source_category, database_type
    )
    
    # Build prompt
    governance_prompt = build_governance_prompt(
        request, intent_result, data_source_index
    )
    
    # Generate governance result
    governance_result, tokens = service.generate_response(
        system_instruction,
        governance_prompt,
        GovernanceOutput
    )
    
    return governance_result, tokens

