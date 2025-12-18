"""Agent output schemas for unified processing."""

from pydantic import BaseModel, field_validator, model_validator
from typing import List, Dict, Optional, Literal, Any


# Intent Output Model
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


# Governance Output Models
class ColumnMaskingRule(BaseModel):
    """Model for column masking rules."""
    column: str
    condition: str
    masking_function: str
    description: Optional[str] = None


class GovernanceOutput(BaseModel):
    """Model for governance output containing row filters and masking rules."""
    row_filters: List[str] = []
    column_masking_rules: List[ColumnMaskingRule] = []
    governance_applied: List[str] = []
    governance_impact: str = ""
    planning_notes: List[str] = []


# Planning Output Models
class QueryParameter(BaseModel):
    """A single query parameter."""
    name: str
    value: str


class QueryPayload(BaseModel):
    """Payload for query operations."""
    language: Optional[str] = None
    dialect: Optional[str] = None
    statement: Optional[str] = None
    parameters: Optional[List[QueryParameter]] = []
    # Additional optional fields for backward compatibility
    query_type: Optional[str] = None
    filters: Optional[List[str]] = []
    projections: Optional[List[str]] = []
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
    rls_rules: List[str] = []
    masking_rules: List[str] = []
    row_filters: List[str] = []  # Backward compatibility
    column_masking: List[ColumnMaskingInfo] = []  # Backward compatibility
    applied_rules: List[str] = []  # Backward compatibility


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
    dependencies: List[str] = []
    query: Optional[str] = ""
    query_payload: QueryPayload
    governance_applied: GovernanceApplied
    output_artifact: str
    
    @model_validator(mode='after')
    def set_query_from_payload(self):
        """Set query from query_payload.statement if query is empty."""
        if not self.query or self.query == "":
            if self.query_payload and self.query_payload.statement:
                self.query = self.query_payload.statement
        return self


class ExecutionPlan(BaseModel):
    """Complete execution plan with strategy and operations."""
    strategy: str
    type: str
    operations: List[CommandStep]


# Visualization Output Models
class VisualizationConfig(BaseModel):
    """Configuration for a visualization."""
    sortable: Optional[bool] = None
    filterable: Optional[bool] = None
    orientation: Optional[str] = None
    color_scheme: Optional[str] = None


class Visualization(BaseModel):
    """A single visualization recommendation."""
    type: str
    title: str
    x_axis: Optional[str] = None
    y_axis: Optional[str] = None
    config: VisualizationConfig
    is_primary: bool = False


class VisualizationOutput(BaseModel):
    """Output from visualization agent."""
    visualizations: List[Visualization]


# Analysis Output Models
class AIMetadata(BaseModel):
    """AI metadata including confidence and reasoning."""
    model: str
    confidence: float
    confidence_score: float
    input_tokens_used: Optional[int] = None
    output_tokens_used: Optional[int] = None
    generation_time_ms: Optional[int] = None
    explanation: str
    reasoning_steps: List[str]
    # Backward compatibility fields
    prompt_tokens: Optional[int] = None  # Maps to input_tokens_used
    completion_tokens: Optional[int] = None  # Maps to output_tokens_used
    total_tokens: Optional[int] = None
    tokens_used: Optional[int] = None


class AnalyzeAIOutput(BaseModel):
    """Output from analyze AI agent."""
    confidence: int
    confidence_score: float
    explanation: str
    reasoning_steps: List[str] = []
    suggestions: List[str] = []
    
    @field_validator('reasoning_steps', mode='before')
    @classmethod
    def flatten_reasoning_steps(cls, v: Any) -> List[str]:
        """Flatten nested lists in reasoning_steps."""
        if not v:
            return []
        if isinstance(v, str):
            return [v]
        if isinstance(v, list):
            result = []
            for item in v:
                if isinstance(item, str):
                    result.append(item)
                elif isinstance(item, list):
                    # Flatten nested lists
                    result.extend([str(i) for i in item if i])
                else:
                    result.append(str(item))
            return result
        return [str(v)]


# Unified Output Model
class UnifiedOutput(BaseModel):
    """Unified output model combining all agent outputs."""
    intent: IntentOutput
    governance: GovernanceOutput
    execution_plan: ExecutionPlan
    visualization: Optional[VisualizationOutput] = None
    analysis: AnalyzeAIOutput

