"""FastAPI application for the analyze endpoint."""

import os
import uuid
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator, model_validator
from dotenv import load_dotenv

from schema.agent import ExecutionResponse, ExecutionResponseLLM
from schema.prompts import getdatabase, get_system_prompt, prepare_prompt
from services.ai import AIService, AIServiceError
from middleware import RateLimitMiddleware, SecurityHeadersMiddleware
from utils import (
    retry_on_failure, generate_cache_key, get_cached_response, 
    cache_response, setup_logging
)

# Setup logging
setup_logging(os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI(
    title="RiverGen PSA API",
    description="API for intelligent SQL planning, governance enforcement, and execution plan generation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS configuration - Allow localhost by default
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    max_age=3600,
)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Add rate limiting middleware (60 requests per minute per IP)
rate_limit_per_minute = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
app.add_middleware(RateLimitMiddleware, requests_per_minute=rate_limit_per_minute)


# Request Models
class UserAttribute(BaseModel):
    """User attribute key-value pairs."""
    pass


class UserContext(BaseModel):
    """User context information."""
    user_id: int
    workspace_id: int
    organization_id: int
    roles: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    attributes: Dict[str, Any] = Field(default_factory=dict)


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
    indexes: Optional[List[str]] = Field(default_factory=list)
    columns: List[Column] = Field(default_factory=list)


class Schema(BaseModel):
    """Database schema definition."""
    schema_name: str
    tables: List[Table] = Field(default_factory=list)


class GovernanceRule(BaseModel):
    """Governance rule definition."""
    condition: Optional[str] = None
    description: Optional[str] = None
    column: Optional[str] = None
    masking_function: Optional[str] = None


class RowLevelSecurity(BaseModel):
    """Row-level security configuration."""
    enabled: bool = False
    rules: List[GovernanceRule] = Field(default_factory=list)


class ColumnMasking(BaseModel):
    """Column masking configuration."""
    enabled: bool = False
    rules: List[GovernanceRule] = Field(default_factory=list)


class GovernancePolicies(BaseModel):
    """Governance policies configuration."""
    row_level_security: Optional[RowLevelSecurity] = None
    column_masking: Optional[ColumnMasking] = None


class DataSource(BaseModel):
    """Data source definition."""
    data_source_id: int
    name: str
    type: str
    schemas: List[Schema] = Field(default_factory=list)
    governance_policies: Optional[GovernancePolicies] = None


class ExecutionContext(BaseModel):
    """Execution context configuration."""
    max_rows: int = Field(default=1000, ge=1, le=100000)
    timeout_seconds: int = Field(default=30, ge=1, le=3600)


class RequestModel(BaseModel):
    """Main request model for the API."""
    request_id: str
    execution_id: str
    timestamp: Optional[str] = None
    user_context: UserContext
    user_prompt: str = Field(..., min_length=1, description="User's natural language query")
    data_sources: List[DataSource] = Field(..., min_length=1, description="List of data sources")
    selected_schema_names: Optional[List[str]] = Field(default_factory=list)
    execution_context: Optional[ExecutionContext] = None
    ai_model: Optional[str] = Field(
        default="meta-llama/llama-4-scout-17b-16e-instruct",
        description="AI model to use. Must be 'meta-llama/llama-4-scout-17b-16e-instruct'"
    )
    temperature: Optional[float] = Field(default=0.1, ge=0.0, le=2.0)
    include_visualization: Optional[bool] = False

    @field_validator('ai_model')
    @classmethod
    def validate_ai_model(cls, v):
        """Validate that ai_model is 'meta-llama/llama-4-scout-17b-16e-instruct'."""
        if not v:
            return "meta-llama/llama-4-scout-17b-16e-instruct"
        
        # Check if the model is the required scout model
        if v != "meta-llama/llama-4-scout-17b-16e-instruct":
            raise ValueError(
                f"Invalid model '{v}'. Only 'meta-llama/llama-4-scout-17b-16e-instruct' is allowed."
            )
        
        return v

    @model_validator(mode='after')
    def validate_data_source_types(self):
        """Validate that all data source types are from supported categories (SQL, NoSQL, or Cloud Warehouse)."""
        # These must match exactly the types defined in prompts.py
        SQL_TYPES = {"postgresql", "mysql", "mariadb", "sqlserver", "oracle"}
        CLOUD_WAREHOUSE_TYPES = {"snowflake", "bigquery", "redshift", "synapse", "databricks"}
        NOSQL_TYPES = {"mongodb", "cassandra", "redis", "dynamodb", "elasticsearch"}
        
        SUPPORTED_TYPES = SQL_TYPES | CLOUD_WAREHOUSE_TYPES | NOSQL_TYPES
        
        invalid_types = []
        for data_source in self.data_sources:
            source_type = data_source.type.lower().strip()
            if source_type not in SUPPORTED_TYPES:
                invalid_types.append(f"'{data_source.type}' (data_source_id: {data_source.data_source_id})")
        
        if invalid_types:
            raise ValueError(
                f"Unsupported data source type(s): {', '.join(invalid_types)}. "
                f"Supported types are: SQL databases ({', '.join(sorted(SQL_TYPES))}), "
                f"Cloud Warehouses ({', '.join(sorted(CLOUD_WAREHOUSE_TYPES))}), "
                f"and NoSQL databases ({', '.join(sorted(NOSQL_TYPES))})"
            )
        
        return self


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError exceptions."""
    logger.warning(f"Validation error: {str(exc)} - Path: {request.url.path}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "status": "error",
            "message": str(exc),
            "error_type": "validation_error",
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(status.HTTP_429_TOO_MANY_REQUESTS)
async def rate_limit_handler(request: Request, exc: HTTPException):
    """Handle rate limit exceptions."""
    logger.warning(f"Rate limit exceeded for IP: {request.client.host if request.client else 'unknown'}")
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "status": "error",
            "message": exc.detail,
            "error_type": "rate_limit_exceeded",
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    error_id = str(uuid.uuid4())
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {str(exc)} - "
        f"Path: {request.url.path} - Error ID: {error_id}",
        exc_info=True
    )
    
    # Don't expose internal error details in production
    error_message = str(exc) if os.getenv("ENVIRONMENT", "development") == "development" else "An internal error occurred"
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": error_message,
            "error_type": "internal_error",
            "error_id": error_id,
            "timestamp": datetime.now().isoformat()
        }
    )


@app.post("/analyze", response_model=ExecutionResponse)
async def analyze(request: RequestModel, http_request: Request):
    """
    Main endpoint for analyzing user requests and generating execution plans.
    
    This endpoint processes a user request through AI agents to:
    1. Classify user intent
    2. Apply governance rules (RLS and column masking)
    3. Generate execution plans with actual database queries
    4. Recommend visualizations (if requested)
    5. Provide AI analysis with confidence scores
    
    **Request Validation:**
    - All data source types must be from supported categories (SQL, NoSQL, or Cloud Warehouse)
    - AI model is validated
    - All required fields are validated using Pydantic
    
    **Response:**
    - Returns a complete ExecutionResponse with execution plan, visualizations, and metadata
    - Includes request_id, execution_id, status, and timestamp (added in post-processing)
    """
    request_start_time = time.time()
    client_ip = http_request.client.host if http_request.client else "unknown"
    
    try:
        logger.info(
            f"Analyze request received - Request ID: {request.request_id}, "
            f"IP: {client_ip}, Prompt: {request.user_prompt[:100]}..."
        )
        
        # Get API key from environment variable
        api_key = os.getenv("GROQ_API_KEY")
        
        if not api_key or api_key.strip() == "":
            logger.error("GROQ_API_KEY not found in environment variables")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="API configuration error. Please contact administrator."
            )
        
        # Convert Pydantic model to dict
        request_dict = request.model_dump()
        
        # Check cache first (if caching is enabled)
        use_cache = os.getenv("ENABLE_CACHE", "true").lower() == "true"
        cache_key = None
        cached_response = None
        
        if use_cache:
            cache_key = generate_cache_key(request_dict)
            cached_response = get_cached_response(cache_key)
            if cached_response:
                logger.info(f"Cache hit for request: {request.request_id}")
                # Update timestamp and IDs for cached response
                cached_response['request_id'] = request_dict['request_id']
                cached_response['execution_id'] = request_dict['execution_id']
                cached_response['timestamp'] = datetime.now()
                return ExecutionResponse.model_validate(cached_response)
        
        # Get database information for the first data source
        try:
            databasetype, query_pattern, intent_types = await getdatabase(
                request_dict['data_sources'][0]['type']
            )
            logger.debug(f"Database type determined: {databasetype} for request: {request.request_id}")
        except Exception as e:
            logger.error(f"Failed to determine database type for request {request.request_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid database type: {str(e)}"
            )
        
        # Get prompts
        include_visualization = request_dict.get("include_visualization", False)
        try:
            system_prompt = await get_system_prompt()
            user_prompt = await prepare_prompt(
                databasetype=databasetype,
                database_source=request_dict["data_sources"][0],
                intent_types=intent_types,
                query_pattern=query_pattern,
                user_context=request_dict["user_context"],
                user_prompt=request_dict["user_prompt"],
                governance_policies=request_dict["data_sources"][0].get("governance_policies", {}),
                execution_context=request_dict.get("execution_context", {}),
                selected_schema_names=request_dict.get("selected_schema_names", []),
                include_visualization=include_visualization
            )
            logger.debug(f"Prompts prepared successfully for request: {request.request_id}")
        except Exception as e:
            logger.error(f"Failed to prepare prompts for request {request.request_id}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to prepare prompts"
                )
            
        # Initialize AI service
        try:
            ai_service = AIService(
                api_key=api_key,
                model=request_dict.get("ai_model", "meta-llama/llama-4-scout-17b-16e-instruct")
            )
        except AIServiceError as e:
            logger.error(f"Failed to initialize AI service: {str(e)}")
            raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="AI service initialization failed"
            )
        
        # Generate response using LLM schema (without post-processing fields)
        # Retry logic is handled inside AIService.generate_response
        # This is async and can handle multiple concurrent requests
        try:
            logger.debug(f"Calling LLM service for request: {request.request_id}")
            llm_response_dict, token_info = await ai_service.generate_response(
                system_instruction=system_prompt,
                prompt=user_prompt,
                output_schema=ExecutionResponseLLM,
                max_completion_tokens=4096,
                timeout=int(request_dict.get("execution_context", {}).get("timeout_seconds", 120))
            )
            logger.debug(f"LLM service completed for request: {request.request_id}")
        except AIServiceError as e:
            logger.error(f"LLM generation failed after retries: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service temporarily unavailable. Please try again later."
            )
        
        # Set visualization to null if include_visualization is false
        if not include_visualization:
            llm_response_dict['visualization'] = None
        
        # Build full response with post-processing fields at the top
        # Generate unique plan_id if not provided by LLM
        plan_id = llm_response_dict.get('plan_id') or f"plan-{uuid.uuid4().hex[:12]}"
        
        response_dict = {
            'request_id': request_dict.get('request_id', ''),
            'execution_id': request_dict.get('execution_id', ''),
            'plan_id': plan_id,
            'status': 'success',
            'timestamp': datetime.now(),
            **llm_response_dict  # Add all LLM response fields
        }
        
        # Add ai_metadata fields that are not in the LLM schema
        if not response_dict.get('ai_metadata'):
            response_dict['ai_metadata'] = {}
        
        # Add post-processing fields to ai_metadata
        response_dict['ai_metadata']['model'] = request_dict.get('ai_model', 'meta-llama/llama-4-scout-17b-16e-instruct')
        response_dict['ai_metadata']['input_tokens'] = token_info.get('prompt_tokens', 0)
        response_dict['ai_metadata']['output_tokens'] = token_info.get('completion_tokens', 0)
        response_dict['ai_metadata']['generation_time_ms'] = token_info.get('generation_time_ms', 0)
        
        # Validate and return response using ExecutionResponse model
        try:
            response = ExecutionResponse.model_validate(response_dict)
            logger.debug(f"Response validated successfully for request: {request.request_id}")
        except Exception as e:
            logger.error(
                f"Response validation failed for request {request.request_id}: {str(e)}",
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Response validation failed: {str(e)}"
            )
        
        # Cache the response if caching is enabled
        if use_cache and cache_key:
            try:
                cache_response(cache_key, response_dict)
                logger.debug(f"Cached response for request: {request.request_id} (key: {cache_key[:16]}...)")
            except Exception as e:
                logger.warning(f"Failed to cache response for request {request.request_id}: {str(e)}")
        
        # Log successful request with performance metrics
        request_time_ms = int((time.time() - request_start_time) * 1000)
        logger.info(
            f"✓ Analyze request completed - Request ID: {request.request_id}, "
            f"IP: {client_ip}, Time: {request_time_ms}ms, "
            f"Tokens: {token_info.get('prompt_tokens', 0)}+{token_info.get('completion_tokens', 0)}"
        )
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions (already handled)
        raise
    except ValueError as e:
        # Validation errors
        logger.warning(f"Validation error for request {request.request_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Unexpected errors
        request_time_ms = int((time.time() - request_start_time) * 1000)
        error_id = str(uuid.uuid4())
        logger.error(
            f"Unexpected error processing request {request.request_id} "
            f"(Error ID: {error_id}, Time: {request_time_ms}ms): {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing request. Error ID: {error_id}"
        )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "rivergen-psa"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

