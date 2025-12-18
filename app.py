from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from schemas import RequestModel, ResponseModel
from services import AIService, process_unified
from core.database import get_database_dialect, get_database_language
from dotenv import load_dotenv
import time
import uuid
import os
import traceback
from datetime import datetime
from typing import Dict, Any

# Load environment variables from .env file
load_dotenv()


def normalize_execution_plan(execution_plan: Dict, request_data: Dict) -> Dict:
    """
    Normalize execution plan to match the expected response format.
    Adds language, dialect, and statement fields to query_payload.
    """
    data_source = request_data.get('data_sources', [{}])[0]
    datasource_type = data_source.get('type', 'postgresql')
    
    # Use database_config functions for consistency
    dialect = get_database_dialect(datasource_type)
    language = get_database_language(datasource_type)
    
    # Update each operation's query_payload
    for operation in execution_plan.get('operations', []):
        query_payload = operation.get('query_payload', {})
        query = operation.get('query', '')
        
        # Ensure required fields are present
        if 'language' not in query_payload:
            query_payload['language'] = language
        if 'dialect' not in query_payload:
            query_payload['dialect'] = dialect
        if 'statement' not in query_payload:
            query_payload['statement'] = query
        # Ensure parameters array exists (required in schema)
        if 'parameters' not in query_payload:
            query_payload['parameters'] = []
    
    return execution_plan


app = FastAPI(
    title="RiverGen PSA API",
    description="API for intent classification, governance, planning, visualization, and analysis",
    version="1.0.0"
)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "message": "Request validation failed",
            "errors": exc.errors(),
            "detail": str(exc)
        }
    )


@app.exception_handler(ValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "message": "Validation error",
            "errors": exc.errors(),
            "detail": str(exc)
        }
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError exceptions."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "status": "error",
            "message": "Invalid value provided",
            "detail": str(exc)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": "Internal server error",
            "detail": str(exc),
            "type": type(exc).__name__
        }
    )


def validate_request(request_data: Dict[str, Any]) -> None:
    """
    Validate all parts of the request and raise appropriate exceptions.
    
    Args:
        request_data: The request dictionary
    
    Raises:
        ValueError: For validation errors with specific error messages
    """
    # Validate required fields
    if not request_data.get('request_id'):
        raise ValueError("request_id is required and cannot be empty")
    
    if not request_data.get('execution_id'):
        raise ValueError("execution_id is required and cannot be empty")
    
    if not request_data.get('user_prompt') or not request_data.get('user_prompt', '').strip():
        raise ValueError("user_prompt is required and cannot be empty")
    
    # Validate user_context
    user_context = request_data.get('user_context')
    if not user_context:
        raise ValueError("user_context is required")
    
    if not isinstance(user_context.get('user_id'), int) or user_context.get('user_id') is None:
        raise ValueError("user_context.user_id is required and must be an integer")
    
    if not isinstance(user_context.get('workspace_id'), int) or user_context.get('workspace_id') is None:
        raise ValueError("user_context.workspace_id is required and must be an integer")
    
    if not isinstance(user_context.get('organization_id'), int) or user_context.get('organization_id') is None:
        raise ValueError("user_context.organization_id is required and must be an integer")
    
    # Validate data_sources
    data_sources = request_data.get('data_sources', [])
    if not data_sources or len(data_sources) == 0:
        raise ValueError("At least one data_source is required")
    
    for idx, data_source in enumerate(data_sources):
        if not data_source.get('data_source_id'):
            raise ValueError(f"data_sources[{idx}].data_source_id is required")
        
        if not data_source.get('name') or not data_source.get('name', '').strip():
            raise ValueError(f"data_sources[{idx}].name is required and cannot be empty")
        
        if not data_source.get('type') or not data_source.get('type', '').strip():
            raise ValueError(f"data_sources[{idx}].type is required and cannot be empty")
        
        # Validate schemas
        schemas = data_source.get('schemas', [])
        if not schemas or len(schemas) == 0:
            raise ValueError(f"data_sources[{idx}] must have at least one schema")
        
        for schema_idx, schema in enumerate(schemas):
            if not schema.get('schema_name') or not schema.get('schema_name', '').strip():
                raise ValueError(f"data_sources[{idx}].schemas[{schema_idx}].schema_name is required and cannot be empty")
            
            # Validate tables
            tables = schema.get('tables', [])
            if not tables or len(tables) == 0:
                raise ValueError(f"data_sources[{idx}].schemas[{schema_idx}] must have at least one table")
            
            for table_idx, table in enumerate(tables):
                if not table.get('table_name') or not table.get('table_name', '').strip():
                    raise ValueError(f"data_sources[{idx}].schemas[{schema_idx}].tables[{table_idx}].table_name is required and cannot be empty")
                
                # Validate columns
                columns = table.get('columns', [])
                if not columns or len(columns) == 0:
                    raise ValueError(f"data_sources[{idx}].schemas[{schema_idx}].tables[{table_idx}] must have at least one column")
                
                for col_idx, column in enumerate(columns):
                    if not column.get('column_name') or not column.get('column_name', '').strip():
                        raise ValueError(f"data_sources[{idx}].schemas[{schema_idx}].tables[{table_idx}].columns[{col_idx}].column_name is required and cannot be empty")
    
    # Validate model (using Groq model names - more flexible validation)
    model = request_data.get('ai_model', 'rgen_alpha_v2')
    # Allow legacy model names and Groq model names
    legacy_models = ["gemini-2.5-flash-lite", "gemini-2.5-flash"]
    allowed_prefixes = ["openai/", "llama-", "mixtral-"]
    if model not in legacy_models and not any(model.startswith(prefix) for prefix in allowed_prefixes):
        # More lenient - just warn but allow (for flexibility with future Groq models)
        pass
    
    # Validate temperature
    temperature = request_data.get('temperature', 0.1)
    if not isinstance(temperature, (int, float)) or temperature < 0.0 or temperature > 2.0:
        raise ValueError(f"temperature must be a number between 0.0 and 2.0, got {temperature}")
    
    # Validate execution_context if provided
    exec_context = request_data.get('execution_context')
    if exec_context:
        if not isinstance(exec_context.get('max_rows'), int) or exec_context.get('max_rows', 0) <= 0:
            raise ValueError("execution_context.max_rows must be a positive integer")
        
        if not isinstance(exec_context.get('timeout_seconds'), int) or exec_context.get('timeout_seconds', 0) <= 0:
            raise ValueError("execution_context.timeout_seconds must be a positive integer")


def process_request(request_data: Dict[str, Any], api_key: str) -> Dict[str, Any]:
    """
    Process the request through unified agent in a single LLM API call.
    
    Args:
        request_data: The request dictionary
        api_key: API key for the AI service (Groq)
    
    Returns:
        Dictionary containing the complete response
    
    Raises:
        ValueError: If validation fails or model is not supported
        HTTPException: For processing errors
    """
    # Validate entire request first
    validate_request(request_data)
    
    start_time = time.time()
    
    # Validate API key
    if not api_key or api_key.strip() == "":
        raise ValueError("API key is required")
    
    # Get and map model to Groq format
    model = request_data.get('ai_model', 'rgen_alpha_v2')
    # Map model names to Groq models
    model_mapping = {
        "rgen_alpha_v2": "openai/gpt-oss-20b",  # Map rgen_alpha_v2 to Groq model
        "gemini-2.5-flash-lite": "openai/gpt-oss-20b",
        "gemini-2.5-flash": "openai/gpt-oss-20b"
    }
    if model in model_mapping:
        model = model_mapping[model]
    
    # Initialize AI Service
    try:
        service = AIService(api_key=api_key, model=model)
    except Exception as e:
        raise ValueError(f"Failed to initialize AI service: {str(e)}")
    
    # Generate plan_id
    plan_id = f"plan-{uuid.uuid4().hex[:8]}"
    
    # Single unified call to process everything
    try:
        # Validate data source exists
        if not request_data.get('data_sources') or len(request_data.get('data_sources', [])) == 0:
            raise ValueError("No data sources provided")
        
        # Get visualization flag
        include_visualization = request_data.get('include_visualization', False)
        
        # Make single unified API call
        unified_result, token_info = process_unified(
            service,
            request_data,
            data_source_index=0,
            include_visualization=include_visualization
        )
        
        # Extract results from unified output
        intent_result = unified_result.get('intent', {})
        governance_result = unified_result.get('governance', {})
        execution_plan = unified_result.get('execution_plan', {})
        visualization_output = unified_result.get('visualization')
        analyze_result = unified_result.get('analysis', {})
        
        # Validate unified result
        if not intent_result:
            raise ValueError("Unified processing returned empty intent result")
        
        if not intent_result.get('intent_type'):
            raise ValueError("Intent classification failed: intent_type is missing")
        
        if not intent_result.get('source_category'):
            raise ValueError("Intent classification failed: source_category is missing")
        
        if not governance_result:
            raise ValueError("Unified processing returned empty governance result")
        
        if not execution_plan:
            raise ValueError("Unified processing returned empty execution plan")
        
        if not execution_plan.get('operations') or len(execution_plan.get('operations', [])) == 0:
            raise ValueError("Execution plan must contain at least one operation")
        
        if not analyze_result:
            raise ValueError("Unified processing returned empty analysis result")
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "error",
                "message": "Unified processing validation failed",
                "detail": str(e)
            }
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        print(f"Unified processing error: {error_type}: {error_msg}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Unified processing failed",
                "error": error_msg,
                "type": error_type
            }
        )
    
    # Normalize execution plan query_payload to match expected format
    try:
        execution_plan = normalize_execution_plan(execution_plan, request_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to normalize execution plan: {str(e)}"
        )
    
    # Normalize governance_applied to match expected format
    try:
        for operation in execution_plan.get('operations', []):
            if not operation.get('governance_applied'):
                raise ValueError(f"Operation {operation.get('step_id', 'unknown')} is missing governance_applied")
            
            gov_applied = operation.get('governance_applied', {})
            # Ensure rls_rules and masking_rules are present (required fields)
            # If they come from LLM as row_filters/column_masking, convert them
            if 'rls_rules' not in gov_applied or not gov_applied.get('rls_rules'):
                if 'row_filters' in gov_applied:
                    # Convert row_filters to rls_rules (use filter descriptions or generate names)
                    row_filters = gov_applied.get('row_filters', [])
                    gov_applied['rls_rules'] = [
                        f"rls_rule_{i+1}" if isinstance(f, str) else str(f)
                        for i, f in enumerate(row_filters)
                    ] if row_filters else []
                else:
                    gov_applied['rls_rules'] = []
            
            if 'masking_rules' not in gov_applied or not gov_applied.get('masking_rules'):
                if 'column_masking' in gov_applied:
                    # Convert column_masking list to masking_rules strings
                    column_masking = gov_applied.get('column_masking', [])
                    if isinstance(column_masking, list) and len(column_masking) > 0:
                        # Extract masking rule names/descriptions
                        masking_rules = []
                        for mask in column_masking:
                            if isinstance(mask, dict):
                                column = mask.get('column', 'unknown')
                                func = mask.get('masking_function', 'mask')
                                masking_rules.append(f"{column}_{func}")
                            else:
                                masking_rules.append(str(mask))
                        gov_applied['masking_rules'] = masking_rules
                    else:
                        gov_applied['masking_rules'] = []
                else:
                    gov_applied['masking_rules'] = []
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to normalize governance rules: {str(e)}"
        )
    
    # Final generation time
    final_generation_time_ms = int((time.time() - start_time) * 1000)
    
    # Extract token information
    prompt_tokens = token_info.get('prompt_tokens', 0) if isinstance(token_info, dict) else 0
    completion_tokens = token_info.get('completion_tokens', 0) if isinstance(token_info, dict) else 0
    total_tokens = token_info.get('total_tokens', 0) if isinstance(token_info, dict) else (token_info if isinstance(token_info, int) else 0)
    
    # Map to input_tokens_used and output_tokens_used (primary fields)
    input_tokens_used = prompt_tokens if prompt_tokens > 0 else total_tokens
    output_tokens_used = completion_tokens if completion_tokens > 0 else 0
    
    # Build AI metadata from analysis result
    ai_metadata = {
        "model": model,
        "confidence": analyze_result.get('confidence_score', 0.0) / 100.0 if analyze_result.get('confidence_score', 0) > 1 else analyze_result.get('confidence_score', 0.0),
        "confidence_score": analyze_result.get('confidence_score', 0.0) / 100.0 if analyze_result.get('confidence_score', 0) > 1 else analyze_result.get('confidence_score', 0.0),
        "input_tokens_used": input_tokens_used,
        "output_tokens_used": output_tokens_used,
        "generation_time_ms": final_generation_time_ms,
        "explanation": analyze_result.get('explanation', ''),
        "reasoning_steps": analyze_result.get('reasoning_steps', []),
        # Backward compatibility fields
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "tokens_used": total_tokens
    }
    
    # Build final response with validation
    try:
        # Validate required fields for response
        if not intent_result.get('intent_type'):
            raise ValueError("intent_type is missing from intent result")
        
        if not intent_result.get('intent_summary'):
            raise ValueError("intent_summary is missing from intent result")
        
        final_output = {
            "request_id": request_data.get('request_id', ''),
            "execution_id": request_data.get('execution_id', ''),
            "plan_id": plan_id,
            "status": "success",
            "timestamp": request_data.get('timestamp') or datetime.utcnow().isoformat() + "Z",
            "intent_type": intent_result.get('intent_type', ''),
            "intent_summary": intent_result.get('intent_summary', ''),
            "execution_plan": execution_plan,
            "ai_metadata": ai_metadata,
            "suggestions": analyze_result.get('suggestions', [])
        }
        
        # Only include visualization if requested and available
        if include_visualization and visualization_output:
            visualizations = visualization_output.get('visualizations', [])
            if visualizations:
                final_output["visualization"] = visualizations
        
        return final_output
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to build response: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error building response: {str(e)}"
        )


@app.post("/analyze", response_model=ResponseModel)
async def analyze(request: RequestModel):
    """
    Main endpoint for intent classification, governance, planning, visualization, and analysis.
    
    This endpoint processes a user request through a unified AI agent in a single LLM API call:
    1. Intent Classification - Determines the user's intent
    2. Governance Application - Applies security and masking rules
    3. Execution Planning - Creates executable database commands
    4. Visualization Generation - Recommends visualizations (if requested)
    5. AI Analysis - Provides confidence scores and suggestions
    
    All results are generated from a single Groq API call for efficiency.
    
    **Model Validation:**
    - `ai_model` default is "rgen_alpha_v2" (mapped to Groq "openai/gpt-oss-20b")
    - Also supports Groq models like "openai/gpt-oss-20b"
    - Legacy model names "gemini-2.5-flash-lite" and "gemini-2.5-flash" are automatically mapped to "openai/gpt-oss-20b"
    
    **Request Validation:**
    - All required fields are validated
    - Data sources, schemas, tables, and columns are validated
    - User context is validated
    - Appropriate exceptions are raised for any validation failures
    
    Returns a complete response with execution plan, visualizations, and analysis.
    """
    try:
        # Get API key from environment variable (Groq API key)
        api_key = os.getenv("GROQ_API_KEY")
        
        if not api_key or api_key.strip() == "":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="API key is required. Please set GROQ_API_KEY in your .env file or environment variables."
            )
        
        # Convert Pydantic model to dict (Pydantic already validated the structure)
        request_data = request.model_dump()
        
        # Process the request (includes comprehensive validation)
        response_data = process_request(request_data, api_key)
        
        # Validate and return response
        try:
            return ResponseModel(**response_data)
        except ValidationError as e:
            # If response validation fails, return raw response with warning
            response_data["status"] = "partial_success"
            response_data["validation_warning"] = "Response validation failed, returning raw data"
            response_data["validation_errors"] = [err.get("msg") for err in e.errors()]
            return JSONResponse(content=response_data)
        
    except HTTPException:
        # Re-raise HTTP exceptions (they already have proper status codes)
        raise
    except ValueError as e:
        # Value errors are validation/bad request errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "error",
                "message": "Request validation failed",
                "detail": str(e)
            }
        )
    except Exception as e:
        # Log the full traceback for debugging
        error_detail = {
            "status": "error",
            "message": "Error processing request",
            "error": str(e),
            "type": type(e).__name__
        }
        print(f"Error processing request: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail
        )




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

