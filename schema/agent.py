"""Agent schema definitions for LLM output."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union, Literal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class QueryPayload(BaseModel):
    language: str
    dialect: Optional[str] = None
    statement: str
    parameters: List[Any] = Field(default_factory=list)


class GovernanceApplied(BaseModel):
    rls_rules: List[str] = Field(default_factory=list)
    masking_rules: List[str] = Field(default_factory=list)


class Operation(BaseModel):
    step: int
    step_id: str
    operation_type: str
    type: str
    description: Optional[str] = None
    data_source_id: Optional[int] = None
    compute_type: Optional[str] = None
    compute_engine: Optional[str] = None
    dependencies: List[Union[int, str]] = Field(default_factory=list)
    query: str
    query_payload: QueryPayload
    governance_applied: Optional[GovernanceApplied] = None
    output_artifact: Optional[str] = None


class ExecutionPlan(BaseModel):
    strategy: str
    type: str
    operations: List[Operation] = Field(default_factory=list)


# --- Visualizations: simplified model ---
class Visualization(BaseModel):
    type: str
    title: str
    x_axis: str
    y_axis: str
    config: Dict[str, Any] = Field(default_factory=dict)
    is_primary: bool = False


class AIMetadata(BaseModel):
    confidence: Optional[float] = None
    confidence_score: Optional[float] = None
    explanation: str
    reasoning_steps: List[str]  # Required, must have at least one step
    
    @field_validator('reasoning_steps')
    @classmethod
    def validate_reasoning_steps(cls, v: List[str]) -> List[str]:
        """Ensure reasoning_steps has at least one element."""
        if not v or len(v) == 0:
            raise ValueError('reasoning_steps must contain at least one step')
        return v

class ExecutionAIMetadata(BaseModel):
    model: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    generation_time_ms: Optional[int] = None
    confidence: Optional[float] = None
    confidence_score: Optional[float] = None
    explanation: str
    reasoning_steps: List[str]  # Required, must have at least one step
    
    @field_validator('reasoning_steps')
    @classmethod
    def validate_reasoning_steps(cls, v: List[str]) -> List[str]:
        """Ensure reasoning_steps has at least one element."""
        if not v or len(v) == 0:
            raise ValueError('reasoning_steps must contain at least one step')
        return v

class ExecutionResponseLLM(BaseModel):
    """Schema for LLM output - does not include post-processing fields."""
    intent_type: Optional[str] = None
    intent_summary: Optional[str] = None
    execution_plan: Optional[ExecutionPlan] = None
    visualization: Optional[List[Visualization]] = None  # Can be null if include_visualization is false
    ai_metadata: Optional[AIMetadata] = None
    suggestions: List[str]  # Required, can be empty list but field must be present

    class Config:
        # Helpful for ORM / dict compatibility
        from_attributes = True


class ExecutionResponse(BaseModel):
    """Full response schema with post-processing fields."""
    request_id: str
    execution_id: str
    plan_id: Optional[str] = None
    status: str
    timestamp: datetime
    intent_type: Optional[str] = None
    intent_summary: Optional[str] = None
    execution_plan: Optional[ExecutionPlan] = None
    visualization: Optional[List[Visualization]] = None  # Can be null if include_visualization is false
    ai_metadata: Optional[ExecutionAIMetadata] = None
    suggestions: List[str]  # Required, can be empty list but field must be present

    class Config:
        # Helpful for ORM / dict compatibility
        from_attributes = True

