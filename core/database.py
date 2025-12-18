"""
Database configuration constants shared across the application.
Contains database type mappings, intent types, dialects, query syntax examples, and related constants.
"""

from typing import List, Dict, Optional

# Intent type definitions
SQL_INTENT_TYPES: List[str] = [
    "query",              # SELECT / READ
    "write",              # INSERT / UPDATE / DELETE
    "transform",          # CREATE TABLE AS / VIEW / MATERIALIZATION
    "join",               # Multi-table joins
    "aggregate",          # GROUP BY / SUM / COUNT
    "analytics",          # Window functions / complex analytics
    "schema_inspection",  # DESCRIBE / SHOW / METADATA
    "pipeline",           # Multi-step SQL workflows
    "governance",         # RLS / masking application
    "explain",            # EXPLAIN / EXPLAIN ANALYZE
]

NON_SQL_INTENT_TYPES: List[str] = [
    "query",              # FIND / GET / SEARCH
    "write",              # INSERT / PUT / UPDATE
    "aggregate",          # GROUP / COUNT / MAP-REDUCE
    "index",              # CREATE / UPDATE INDEX
    "document_transform", # Reshape documents
    "search",             # Full-text / vector search
    "pipeline",           # Multi-stage NoSQL pipeline
    "stream",             # Change streams / CDC
    "governance",         # Field masking / access rules
    "schema_inspection",  # Collection / index metadata
]

# Database type sets for categorization
SQL_TYPES = {"postgresql", "mysql", "mariadb", "sqlserver", "oracle"}
CLOUD_WAREHOUSE_TYPES = {"snowflake", "bigquery", "redshift", "synapse", "databricks"}
NOSQL_TYPES = {"mongodb", "cassandra", "redis", "dynamodb", "elasticsearch"}

# All SQL-based types (including cloud warehouses)
ALL_SQL_TYPES = SQL_TYPES | CLOUD_WAREHOUSE_TYPES

# Database type mappings (lowercase to proper name)
SQL_TYPE_MAP: Dict[str, str] = {
    "postgresql": "PostgreSQL",
    "mysql": "MySQL",
    "mariadb": "MariaDB",
    "sqlserver": "SQL Server",
    "oracle": "Oracle"
}

CLOUD_WAREHOUSE_TYPE_MAP: Dict[str, str] = {
    "snowflake": "Snowflake",
    "bigquery": "BigQuery",
    "redshift": "Redshift",
    "synapse": "Synapse",
    "databricks": "Databricks"
}

NON_SQL_TYPE_MAP: Dict[str, str] = {
    "mongodb": "MongoDB",
    "cassandra": "Cassandra",
    "redis": "Redis",
    "dynamodb": "DynamoDB",
    "elasticsearch": "Elasticsearch"
}

# Database dialect mappings
SQL_DIALECT_MAP: Dict[str, str] = {
    "postgresql": "postgresql",
    "mysql": "mysql",
    "mariadb": "mariadb",
    "sqlserver": "sqlserver",
    "oracle": "oracle"
}

CLOUD_WAREHOUSE_DIALECT_MAP: Dict[str, str] = {
    "snowflake": "snowflake",
    "bigquery": "bigquery",
    "redshift": "redshift",
    "synapse": "sqlserver",  # Synapse uses SQL Server dialect
    "databricks": "databricks"
}

NON_SQL_DIALECT_MAP: Dict[str, str] = {
    "mongodb": "mongodb",
    "cassandra": "cql",
    "redis": "redis",
    "dynamodb": "dynamodb",
    "elasticsearch": "elasticsearch"
}

# Database-specific query syntax examples and patterns
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


def get_database_type_name(data_source_type: str) -> str:
    """
    Get the proper database type name from a data source type string.
    
    Args:
        data_source_type: The data source type (e.g., "postgresql", "mongodb", "snowflake")
    
    Returns:
        str: The proper database type name (e.g., "PostgreSQL", "MongoDB", "Snowflake")
    """
    source_type = data_source_type.lower()
    
    if source_type in SQL_TYPE_MAP:
        return SQL_TYPE_MAP[source_type]
    elif source_type in CLOUD_WAREHOUSE_TYPE_MAP:
        return CLOUD_WAREHOUSE_TYPE_MAP[source_type]
    elif source_type in NON_SQL_TYPE_MAP:
        return NON_SQL_TYPE_MAP[source_type]
    else:
        return data_source_type.capitalize()


def get_source_category(data_source_type: str) -> str:
    """
    Determine source category (sql or non_sql) from data source type.
    Cloud warehouses are treated as SQL databases.
    
    Args:
        data_source_type: The data source type (e.g., "postgresql", "mongodb", "snowflake")
    
    Returns:
        str: Either "sql" or "non_sql"
    """
    source_type = data_source_type.lower()
    
    if source_type in SQL_TYPES or source_type in CLOUD_WAREHOUSE_TYPES:
        return "sql"
    elif source_type in NOSQL_TYPES:
        return "non_sql"
    else:
        raise ValueError(f"Unsupported data source type: {source_type}")


def get_database_dialect(data_source_type: str) -> str:
    """
    Get the database dialect from a data source type.
    
    Args:
        data_source_type: The data source type (e.g., "postgresql", "mongodb", "snowflake")
    
    Returns:
        str: The database dialect (e.g., "postgresql", "mongodb", "snowflake", "cql")
    """
    source_type = data_source_type.lower()
    
    if source_type in SQL_DIALECT_MAP:
        return SQL_DIALECT_MAP[source_type]
    elif source_type in CLOUD_WAREHOUSE_DIALECT_MAP:
        return CLOUD_WAREHOUSE_DIALECT_MAP[source_type]
    elif source_type in NON_SQL_DIALECT_MAP:
        return NON_SQL_DIALECT_MAP[source_type]
    else:
        return source_type


def get_database_query_guidance(data_source_type: str, source_category: str) -> str:
    """
    Get database-specific query syntax guidance for planning prompts.
    
    Args:
        data_source_type: The data source type (e.g., "postgresql", "mongodb")
        source_category: Either "sql" or "non_sql"
    
    Returns:
        str: Detailed query syntax guidance for the database type
    """
    source_type = data_source_type.lower()
    database_name = get_database_type_name(source_type)
    
    if source_category == "sql":
        # Check SQL databases first
        if source_type in SQL_QUERY_PATTERNS:
            patterns = SQL_QUERY_PATTERNS[source_type]
            return f"""
{database_name} SQL Query Syntax Examples:

1. Basic Query:
   {patterns['query']}

2. Aggregation:
   {patterns['aggregate']}

3. Joins:
   {patterns['join']}

4. Column Masking:
   {patterns['masking']}

5. String Functions: {patterns['string_functions']}
6. Date Functions: {patterns['date_functions']}

Key {database_name} Features:
- Use proper {database_name} syntax and functions
- Apply WHERE clauses for row-level security filters
- Use CASE statements or {database_name}-specific functions for column masking
- Follow {database_name} naming conventions (schema.table, quoted identifiers if needed)
- Consider {database_name}-specific optimizations (indexes, query hints if applicable)
"""
        # Check cloud warehouses
        elif source_type in CLOUD_WAREHOUSE_QUERY_PATTERNS:
            patterns = CLOUD_WAREHOUSE_QUERY_PATTERNS[source_type]
            warehouse_specific = patterns.get('warehouse_functions', '')
            
            # Build warehouse-specific section
            warehouse_section = ''
            if warehouse_specific:
                warehouse_section = f"7. Warehouse-Specific Functions: {warehouse_specific}\n\n"
            
            return f"""
{database_name} SQL Query Syntax Examples:

1. Basic Query:
   {patterns['query']}

2. Aggregation:
   {patterns['aggregate']}

3. Joins:
   {patterns['join']}

4. Column Masking:
   {patterns['masking']}

5. String Functions: {patterns['string_functions']}
6. Date Functions: {patterns['date_functions']}
{warehouse_section}Key {database_name} Features:
- Use proper {database_name} SQL syntax and functions
- Apply WHERE clauses for row-level security filters
- Use CASE statements or {database_name}-specific functions for column masking
- Follow {database_name} naming conventions (database.schema.table, quoted identifiers if needed)
- Leverage {database_name} warehouse features for analytics and performance
- Consider {database_name}-specific optimizations (clustering, partitioning, materialized views)
"""
    elif source_category == "non_sql" and source_type in NON_SQL_QUERY_PATTERNS:
        patterns = NON_SQL_QUERY_PATTERNS[source_type]
        guidance = f"""
{database_name} Query Syntax Examples:

1. Basic Query:
   {patterns['query']}

2. Filtering:
   {patterns.get('filter', 'N/A')}

3. Projection/Field Selection:
   {patterns.get('projection', 'N/A')}

4. Aggregation:
   {patterns.get('aggregate', 'N/A')}

5. Column Masking:
   {patterns.get('masking', 'N/A')}
"""
        if 'operators' in patterns:
            guidance += f"\n6. Available Operators: {patterns['operators']}\n"
        if 'note' in patterns:
            guidance += f"\nImportant Note: {patterns['note']}\n"
        
        guidance += f"""
Key {database_name} Features:
- Use {database_name}-specific query syntax and operators
- Apply query filters for row-level security
- Use projection/field selection for column masking
- Follow {database_name} query patterns and best practices
- Consider {database_name}-specific optimizations and limitations
"""
        return guidance
    else:
        # Fallback guidance
        if source_category == "sql":
            return f"""
{database_name} SQL Database:
- Generate standard SQL queries with proper syntax
- Use WHERE clauses for filtering and row-level security
- Use CASE statements for column masking
- Follow SQL standard with {database_name}-specific extensions
"""
        else:
            return f"""
{database_name} Non-SQL Database:
- Generate {database_name}-specific query commands
- Use appropriate query syntax for filtering
- Use projection/field selection for column masking
- Follow {database_name} query patterns and conventions
"""


def get_database_language(data_source_type: str) -> str:
    """
    Get the query language name for a data source type.
    Cloud warehouses use SQL.
    
    Args:
        data_source_type: The data source type (e.g., "postgresql", "mongodb", "snowflake")
    
    Returns:
        str: The query language ("sql" or "nosql")
    """
    source_type = data_source_type.lower()
    
    if source_type in SQL_TYPES or source_type in CLOUD_WAREHOUSE_TYPES:
        return "sql"
    elif source_type in NOSQL_TYPES:
        return "nosql"
    else:
        return "unknown"

