from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from api_models import RequestModel, ResponseModel
from service.service import AIService
from agent.intent_agent import classify_intent
from agent.governance_agent import apply_governance
from agent.planning_agent import create_execution_plan
from agent.visualization_agent import create_visualizations
from agent.analyze_ai_agent import analyze_execution_plan
from database_config import get_database_dialect, get_database_language
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
        
        # Add language, dialect, and statement if not present
        if 'language' not in query_payload:
            query_payload['language'] = language
        if 'dialect' not in query_payload:
            query_payload['dialect'] = dialect
        if 'statement' not in query_payload:
            query_payload['statement'] = query
    
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
    
    # Validate model
    model = request_data.get('ai_model', 'gemini-2.5-flash-lite')
    allowed_models = ["gemini-2.5-flash-lite", "gemini-2.5-flash"]
    if model not in allowed_models:
        raise ValueError(f"Invalid ai_model: '{model}'. Must be one of {allowed_models}")
    
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
    Process the request through all agents and return the response.
    
    Args:
        request_data: The request dictionary
        api_key: API key for the AI service
    
    Returns:
        Dictionary containing the complete response
    
    Raises:
        ValueError: If validation fails or model is not supported
        HTTPException: For processing errors
    """
    # Validate entire request first
    validate_request(request_data)
    
    start_time = time.time()
    total_tokens = 0
    
    # Validate API key
    if not api_key or api_key.strip() == "":
        raise ValueError("API key is required")
    
    # Get and validate model
    model = request_data.get('ai_model', 'gemini-2.5-flash-lite')
    allowed_models = ["gemini-2.5-flash-lite", "gemini-2.5-flash"]
    if model not in allowed_models:
        raise ValueError(f"Unsupported model: {model}. Must be one of {allowed_models}")
    
    # Initialize AI Service
    try:
        service = AIService(api_key=api_key, model=model)
    except Exception as e:
        raise ValueError(f"Failed to initialize AI service: {str(e)}")
    
    # Generate plan_id
    plan_id = f"plan-{uuid.uuid4().hex[:8]}"
    
    # Step 1: Classify Intent
    try:
        # Validate data source exists before intent classification
        if not request_data.get('data_sources') or len(request_data.get('data_sources', [])) == 0:
            raise ValueError("No data sources provided for intent classification")
        
        intent_result, tokens = classify_intent(service, request_data)
        
        # Validate intent result
        if not intent_result:
            raise ValueError("Intent classification returned empty result")
        
        if not intent_result.get('intent_type'):
            raise ValueError("Intent classification failed: intent_type is missing")
        
        if not intent_result.get('source_category'):
            raise ValueError("Intent classification failed: source_category is missing")
        
        total_tokens += tokens
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "error",
                "message": "Intent classification validation failed",
                "detail": str(e)
            }
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        print(f"Intent classification error: {error_type}: {error_msg}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Intent classification failed",
                "error": error_msg,
                "type": error_type
            }
        )
    
    # Step 2: Apply Governance
    try:
        # Validate intent result before governance
        if not intent_result:
            raise ValueError("Intent result is required for governance application")
        
        governance_result, tokens = apply_governance(service, request_data, intent_result)
        
        # Validate governance result
        if not governance_result:
            raise ValueError("Governance application returned empty result")
        
        total_tokens += tokens
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "error",
                "message": "Governance application validation failed",
                "detail": str(e)
            }
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        print(f"Governance application error: {error_type}: {error_msg}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Governance application failed",
                "error": error_msg,
                "type": error_type
            }
        )
    
    # Step 3: Create Execution Plan
    try:
        # Validate inputs before planning
        if not intent_result:
            raise ValueError("Intent result is required for execution planning")
        
        if not governance_result:
            raise ValueError("Governance result is required for execution planning")
        
        execution_plan, tokens = create_execution_plan(service, request_data, intent_result, governance_result)
        
        # Validate execution plan
        if not execution_plan:
            raise ValueError("Execution planning returned empty result")
        
        if not execution_plan.get('operations') or len(execution_plan.get('operations', [])) == 0:
            raise ValueError("Execution plan must contain at least one operation")
        
        total_tokens += tokens
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "error",
                "message": "Execution planning validation failed",
                "detail": str(e)
            }
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        print(f"Execution planning error: {error_type}: {error_msg}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Execution planning failed",
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
            # Add rls_rules and masking_rules if not present
            if 'rls_rules' not in gov_applied and 'row_filters' in gov_applied:
                gov_applied['rls_rules'] = [f"rule_{i+1}" for i in range(len(gov_applied.get('row_filters', [])))]
            if 'masking_rules' not in gov_applied and 'column_masking' in gov_applied:
                gov_applied['masking_rules'] = [f"mask_{i+1}" for i in range(len(gov_applied.get('column_masking', [])))]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to normalize governance rules: {str(e)}"
        )
    
    # Step 4: Create Visualizations (if requested)
    visualizations = []
    if request_data.get('include_visualization', False):
        try:
            visualizations, tokens = create_visualizations(service, request_data, intent_result, execution_plan)
            total_tokens += tokens
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            # Visualization is optional, log but don't fail the entire request
            error_type = type(e).__name__
            error_msg = str(e)
            print(f"Warning: Visualization generation failed: {error_type}: {error_msg}")
            print(traceback.format_exc())
            visualizations = []
    
    # Step 5: Analyze Execution Plan
    generation_time_ms = int((time.time() - start_time) * 1000)
    
    try:
        # Validate inputs before analysis
        if not execution_plan:
            raise ValueError("Execution plan is required for AI analysis")
        
        analyze_result, tokens = analyze_execution_plan(
            service, request_data, intent_result, governance_result, execution_plan,
            tokens_used=total_tokens,
            generation_time_ms=generation_time_ms
        )
        
        # Validate analysis result
        if not analyze_result:
            raise ValueError("AI analysis returned empty result")
        
        if not analyze_result.get('ai_metadata'):
            raise ValueError("AI analysis result is missing ai_metadata")
        
        total_tokens += tokens
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "error",
                "message": "AI analysis validation failed",
                "detail": str(e)
            }
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        print(f"AI analysis error: {error_type}: {error_msg}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "AI analysis failed",
                "error": error_msg,
                "type": error_type
            }
        )
    
    # Final generation time
    final_generation_time_ms = int((time.time() - start_time) * 1000)
    
    # Update ai_metadata with final token count and time
    ai_metadata = analyze_result.get('ai_metadata', {})
    ai_metadata['tokens_used'] = total_tokens
    ai_metadata['generation_time_ms'] = final_generation_time_ms
    
    # Build final response with validation
    try:
        # Validate required fields for response
        if not intent_result.get('intent_type'):
            raise ValueError("intent_type is missing from intent result")
        
        if not intent_result.get('intent_summary'):
            raise ValueError("intent_summary is missing from intent result")
        
        if not ai_metadata.get('confidence') is None:
            if not isinstance(ai_metadata.get('confidence'), (int, float)):
                raise ValueError("ai_metadata.confidence must be a number")
        
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
        
        # Only include visualization if requested
        if request_data.get('include_visualization', False) and visualizations:
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
    
    This endpoint processes a user request through multiple AI agents:
    1. Intent Classification - Determines the user's intent
    2. Governance Application - Applies security and masking rules
    3. Execution Planning - Creates executable database commands
    4. Visualization Generation - Recommends visualizations (if requested)
    5. AI Analysis - Provides confidence scores and suggestions
    
    **Model Validation:**
    - `ai_model` must be either "gemini-2.5-flash-lite" or "gemini-2.5-flash"
    - Default is "gemini-2.5-flash-lite"
    
    **Request Validation:**
    - All required fields are validated
    - Data sources, schemas, tables, and columns are validated
    - User context is validated
    - Appropriate exceptions are raised for any validation failures
    
    Returns a complete response with execution plan, visualizations, and analysis.
    """
    try:
        # Get API key from environment variable
        api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key or api_key.strip() == "":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="API key is required. Please set GEMINI_API_KEY in your .env file or environment variables."
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

