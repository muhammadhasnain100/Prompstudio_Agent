from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Optional, Any, Literal
from datetime import datetime


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
    ai_model: Optional[Literal["gemini-2.5-flash-lite", "gemini-2.5-flash"]] = Field(
        default="gemini-2.5-flash-lite",
        description="AI model to use. Must be 'gemini-2.5-flash-lite' or 'gemini-2.5-flash'"
    )
    temperature: Optional[float] = Field(default=0.1, ge=0.0, le=2.0)
    include_visualization: Optional[bool] = False
    
    @field_validator('ai_model')
    @classmethod
    def validate_ai_model(cls, v):
        """Validate that ai_model is one of the allowed values."""
        allowed_models = ["gemini-2.5-flash-lite", "gemini-2.5-flash"]
        if v not in allowed_models:
            raise ValueError(f"ai_model must be one of {allowed_models}, got '{v}'")
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
                "ai_model": "gemini-2.5-flash-lite",
                "temperature": 0.1,
                "include_visualization": True
            }
        }


# Response Models
class QueryParameter(BaseModel):
    """Query parameter."""
    name: str
    value: str


class QueryPayload(BaseModel):
    """Query payload."""
    language: Optional[str] = None
    dialect: Optional[str] = None
    statement: Optional[str] = None
    query_type: Optional[str] = None
    parameters: Optional[List[QueryParameter]] = []
    filters: Optional[List[str]] = []
    projections: Optional[List[str]] = []
    sort_field: Optional[str] = None
    sort_order: Optional[str] = None
    limit: Optional[int] = None
    offset: Optional[int] = None


class ColumnMaskingInfo(BaseModel):
    """Column masking information."""
    column: str
    condition: str
    masking_function: str


class GovernanceApplied(BaseModel):
    """Applied governance rules."""
    rls_rules: Optional[List[str]] = []
    masking_rules: Optional[List[str]] = []
    row_filters: Optional[List[str]] = []
    column_masking: Optional[List[ColumnMaskingInfo]] = []
    applied_rules: Optional[List[str]] = []


class CommandStep(BaseModel):
    """Command step in execution plan."""
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
    """Execution plan."""
    strategy: str
    type: str
    operations: List[CommandStep]


class VisualizationConfig(BaseModel):
    """Visualization configuration."""
    sortable: Optional[bool] = None
    filterable: Optional[bool] = None
    orientation: Optional[str] = None
    color_scheme: Optional[str] = None


class Visualization(BaseModel):
    """Visualization definition."""
    type: str
    title: str
    x_axis: Optional[str] = None
    y_axis: Optional[str] = None
    config: VisualizationConfig
    is_primary: bool = False


class AIMetadata(BaseModel):
    """AI metadata."""
    model: str
    confidence: float
    confidence_score: float
    tokens_used: Optional[int] = None
    generation_time_ms: Optional[int] = None
    explanation: str
    reasoning_steps: List[str]


class ResponseModel(BaseModel):
    """Main response model for the API."""
    request_id: str
    execution_id: str
    plan_id: str
    status: str
    timestamp: str
    intent_type: str
    intent_summary: str
    execution_plan: ExecutionPlan
    visualization: Optional[List[Visualization]] = None
    ai_metadata: AIMetadata
    suggestions: List[str] = []

    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "req-12345",
                "execution_id": "exec-67890",
                "plan_id": "plan-abc123",
                "status": "success",
                "timestamp": "2025-01-15T10:00:02Z",
                "intent_type": "analytics",
                "intent_summary": "Show top 10 customers by revenue this quarter",
                "execution_plan": {
                    "strategy": "single_query",
                    "type": "query",
                    "operations": []
                },
                "visualization": [
                    {
                        "type": "table",
                        "title": "Top 10 Customers by Revenue",
                        "config": {
                            "sortable": True,
                            "filterable": True
                        },
                        "is_primary": True
                    }
                ],
                "ai_metadata": {
                    "model": "rgen_alpha_v2",
                    "confidence": 0.95,
                    "confidence_score": 0.95,
                    "tokens_used": 1250,
                    "generation_time_ms": 2340,
                    "explanation": "Query correctly implements user intent",
                    "reasoning_steps": ["Step 1", "Step 2"]
                },
                "suggestions": []
            }
        }

