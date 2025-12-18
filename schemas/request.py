"""Request schemas for the API."""

from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Optional, Any


# Request Models
class UserAttribute(BaseModel):
    """User attribute key-value pairs."""
    pass


class UserContext(BaseModel):
    """User context information."""
    user_id: int
    workspace_id: int
    organization_id: int
    roles: List[str] = []
    permissions: List[str] = []
    attributes: Dict[str, Any] = {}


class Column(BaseModel):
    """Database column definition."""
    column_name: str
    column_type: str
    is_nullable: Optional[bool] = True
    is_primary_key: Optional[bool] = False
    is_foreign_key: Optional[bool] = False
    column_comment: Optional[str] = None
    pii: Optional[bool] = False


class Table(BaseModel):
    """Database table definition."""
    table_name: str
    table_type: Optional[str] = "table"
    row_count: Optional[int] = 0
    indexes: Optional[List[str]] = []
    columns: List[Column] = []


class Schema(BaseModel):
    """Database schema definition."""
    schema_name: str
    tables: List[Table] = []


class GovernanceRule(BaseModel):
    """Governance rule definition."""
    condition: Optional[str] = None
    description: Optional[str] = None
    column: Optional[str] = None
    masking_function: Optional[str] = None


class RowLevelSecurity(BaseModel):
    """Row-level security configuration."""
    enabled: bool = False
    rules: List[GovernanceRule] = []


class ColumnMasking(BaseModel):
    """Column masking configuration."""
    enabled: bool = False
    rules: List[GovernanceRule] = []


class GovernancePolicies(BaseModel):
    """Governance policies configuration."""
    row_level_security: Optional[RowLevelSecurity] = None
    column_masking: Optional[ColumnMasking] = None


class DataSource(BaseModel):
    """Data source definition."""
    data_source_id: int
    name: str
    type: str
    schemas: List[Schema] = []
    governance_policies: Optional[GovernancePolicies] = None


class ExecutionContext(BaseModel):
    """Execution context configuration."""
    max_rows: int = 1000
    timeout_seconds: int = 30


class RequestModel(BaseModel):
    """Main request model for the API."""
    request_id: str
    execution_id: str
    timestamp: Optional[str] = None
    user_context: UserContext
    user_prompt: str
    data_sources: List[DataSource]
    selected_schema_names: Optional[List[str]] = []
    execution_context: Optional[ExecutionContext] = None
    ai_model: Optional[str] = Field(
        default="rgen_alpha_v2",
        description="AI model to use. Default is 'rgen_alpha_v2'. Also supports Groq models like 'openai/gpt-oss-20b' and legacy names 'gemini-2.5-flash-lite' and 'gemini-2.5-flash'."
    )
    temperature: Optional[float] = Field(default=0.1, ge=0.0, le=2.0)
    include_visualization: Optional[bool] = False
    
    @field_validator('ai_model')
    @classmethod
    def validate_ai_model(cls, v):
        """Validate that ai_model is a valid Groq model or legacy model name."""
        if not v:
            return "openai/gpt-oss-20b"
        
        # Legacy model names
        legacy_models = ["gemini-2.5-flash-lite", "gemini-2.5-flash"]
        if v in legacy_models:
            return v
        
        # Groq model name patterns
        groq_prefixes = ["openai/", "llama-", "mixtral-"]
        if any(v.startswith(prefix) for prefix in groq_prefixes):
            return v
        
        # Allow any string starting with common patterns (more flexible)
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "req-12345",
                "execution_id": "exec-67890",
                "timestamp": "2025-01-15T10:00:00Z",
                "user_context": {
                    "user_id": 1,
                    "workspace_id": 5,
                    "organization_id": 10,
                    "roles": ["analyst", "sales"],
                    "permissions": ["read:customers", "read:orders"],
                    "attributes": {
                        "assigned_region": "US-WEST",
                        "department": "Sales"
                    }
                },
                "user_prompt": "Show me top 10 customers by revenue this quarter",
                "data_sources": [
                    {
                        "data_source_id": 1,
                        "name": "PostgreSQL Production",
                        "type": "postgresql",
                        "schemas": [
                            {
                                "schema_name": "public",
                                "tables": [
                                    {
                                        "table_name": "customers",
                                        "table_type": "table",
                                        "row_count": 45000,
                                        "indexes": ["idx_region", "idx_segment"],
                                        "columns": [
                                            {
                                                "column_name": "id",
                                                "column_type": "integer",
                                                "is_nullable": False,
                                                "is_primary_key": True,
                                                "is_foreign_key": False,
                                                "column_comment": "Customer ID"
                                            },
                                            {
                                                "column_name": "name",
                                                "column_type": "varchar(255)",
                                                "is_nullable": False
                                            },
                                            {
                                                "column_name": "revenue",
                                                "column_type": "decimal(10,2)",
                                                "is_nullable": True
                                            },
                                            {
                                                "column_name": "region",
                                                "column_type": "varchar(50)",
                                                "is_nullable": True
                                            },
                                            {
                                                "column_name": "email",
                                                "column_type": "varchar(255)",
                                                "is_nullable": False,
                                                "pii": True
                                            }
                                        ]
                                    }
                                ]
                            }
                        ],
                        "governance_policies": {
                            "row_level_security": {
                                "enabled": True,
                                "rules": [
                                    {
                                        "condition": "region IN (SELECT region FROM user_access WHERE user_id = {user_id})",
                                        "description": "Users can only see customers in their assigned regions"
                                    }
                                ]
                            },
                            "column_masking": {
                                "enabled": True,
                                "rules": [
                                    {
                                        "column": "email",
                                        "condition": "region != {user.attributes.assigned_region}",
                                        "masking_function": "email_mask",
                                        "description": "Mask emails for users outside assigned region"
                                    }
                                ]
                            }
                        }
                    }
                ],
                "selected_schema_names": ["public"],
                "execution_context": {
                    "max_rows": 1000,
                    "timeout_seconds": 30
                },
                "ai_model": "rgen_alpha_v2",
                "temperature": 0.1,
                "include_visualization": True
            }
        }

