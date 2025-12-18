"""Response schemas for the API."""

from pydantic import BaseModel
from typing import List, Optional
from schemas.agent import ExecutionPlan, Visualization, AIMetadata


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
                "intent_type": "query",
                "intent_summary": "Retrieve top 10 customers by total revenue for Q1 2025, with RLS and masking applied.",
                "execution_plan": {
                    "strategy": "pushdown",
                    "type": "sql_query",
                    "operations": [
                        {
                            "step": 1,
                            "step_id": "step_1",
                            "operation_type": "read",
                            "type": "source_query",
                            "description": "Execute SQL aggregation on Postgres with RLS and masking",
                            "data_source_id": 1,
                            "compute_type": "source_native",
                            "compute_engine": "source_native",
                            "dependencies": [],
                            "query": "SELECT * FROM customers LIMIT 10",
                            "query_payload": {
                                "language": "sql",
                                "dialect": "postgresql",
                                "statement": "SELECT * FROM customers LIMIT 10",
                                "parameters": []
                            },
                            "governance_applied": {
                                "rls_rules": ["region_filter"],
                                "masking_rules": ["email_mask_region"]
                            },
                            "output_artifact": "result_frame"
                        }
                    ]
                },
                "visualization": [
                    {
                        "type": "table",
                        "title": "Top 10 Customers by Revenue (Q1 2025)",
                        "config": {
                            "sortable": True,
                            "filterable": True
                        },
                        "is_primary": True
                    },
                    {
                        "type": "bar",
                        "x_axis": "name",
                        "y_axis": "revenue",
                        "title": "Top 10 Customers by Revenue (Q1 2025)",
                        "config": {
                            "orientation": "vertical",
                            "color_scheme": "default"
                        },
                        "is_primary": False
                    }
                ],
                "ai_metadata": {
                    "model": "rgen_alpha_v2",
                    "confidence": 0.95,
                    "confidence_score": 0.95,
                    "input_tokens_used": 1250,
                    "output_tokens_used": 1250,
                    "generation_time_ms": 2340,
                    "explanation": "Query joins customers and orders tables, filters by quarter, groups by customer, sums revenue, orders descending, limits to 10. Applied RLS filter for user's assigned region and email masking for other regions.",
                    "reasoning_steps": [
                        "Identified tables: customers, orders",
                        "Detected join condition: customer_id",
                        "Applied RLS filter for user 1's assigned regions",
                        "Applied email masking for regions outside user's assigned region",
                        "Added date range filter for Q1 2025",
                        "Aggregated by SUM(amount)",
                        "Limited to top 10"
                    ]
                },
                "suggestions": [
                    "Consider filtering by customer segment for more insights",
                    "You might want to compare with previous quarter"
                ]
            }
        }

