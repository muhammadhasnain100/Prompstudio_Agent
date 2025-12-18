from groq import Groq
from pydantic import BaseModel
import json
import time
from typing import Optional, Tuple, Any, Dict


def _clean_response(data: Any) -> Any:
    """
    Clean up response data to handle common LLM formatting issues.
    
    Args:
        data: The parsed JSON response
    
    Returns:
        Cleaned data structure
    """
    if isinstance(data, dict):
        cleaned = {}
        for key, value in data.items():
            # Handle governance field specifically
            if key == 'governance' and isinstance(value, dict):
                governance_cleaned = {}
                # Ensure required fields have defaults
                governance_cleaned['row_filters'] = value.get('row_filters', [])
                governance_cleaned['column_masking_rules'] = value.get('column_masking_rules', [])
                governance_cleaned['governance_applied'] = value.get('governance_applied', [])
                governance_cleaned['governance_impact'] = value.get('governance_impact', '')
                governance_cleaned['planning_notes'] = value.get('planning_notes', [])
                # Clean nested structures
                for gkey, gvalue in governance_cleaned.items():
                    if isinstance(gvalue, (dict, list)):
                        governance_cleaned[gkey] = _clean_response(gvalue)
                cleaned[key] = governance_cleaned
            # Handle analysis field specifically
            elif key == 'analysis' and isinstance(value, dict):
                analysis_cleaned = {}
                for akey, avalue in value.items():
                    if akey == 'reasoning_steps' and isinstance(avalue, list):
                        flattened = []
                        for item in avalue:
                            if isinstance(item, str):
                                flattened.append(item)
                            elif isinstance(item, list):
                                # Flatten nested lists
                                flattened.extend([str(i) for i in item if i])
                            else:
                                flattened.append(str(item))
                        analysis_cleaned[akey] = flattened
                    elif akey == 'suggestions':
                        if not avalue or (isinstance(avalue, list) and len(avalue) == 0):
                            analysis_cleaned[akey] = []
                        else:
                            analysis_cleaned[akey] = avalue
                    else:
                        analysis_cleaned[akey] = _clean_response(avalue)
                cleaned[key] = analysis_cleaned
            # Handle reasoning_steps that might be nested lists (at top level or in other places)
            elif key == 'reasoning_steps' and isinstance(value, list):
                flattened = []
                for item in value:
                    if isinstance(item, str):
                        flattened.append(item)
                    elif isinstance(item, list):
                        # Flatten nested lists
                        flattened.extend([str(i) for i in item if i])
                    else:
                        flattened.append(str(item))
                cleaned[key] = flattened
            # Handle suggestions that might be missing
            elif key == 'suggestions' and (not value or (isinstance(value, list) and len(value) == 0)):
                cleaned[key] = []
            # Handle query field in operations
            elif key == 'operations' and isinstance(value, list):
                cleaned_ops = []
                for op in value:
                    if isinstance(op, dict):
                        # If query is missing, try to get it from query_payload.statement
                        if 'query' not in op or not op.get('query'):
                            if 'query_payload' in op and isinstance(op['query_payload'], dict):
                                if 'statement' in op['query_payload']:
                                    op['query'] = op['query_payload']['statement']
                                else:
                                    op['query'] = ""
                        # Recursively clean nested structures
                        op = _clean_response(op)
                    cleaned_ops.append(op)
                cleaned[key] = cleaned_ops
            else:
                cleaned[key] = _clean_response(value)
        return cleaned
    elif isinstance(data, list):
        return [_clean_response(item) for item in data]
    else:
        return data


class AIService:
    """
    Service class for AI model interactions using Groq.
    Handles communication with the AI model for generating responses.
    """
    
    def __init__(self, api_key: str, model: str = "openai/gpt-oss-20b"):
        """
        Initialize the AI Service.
        
        Args:
            api_key: API key for the Groq API
            model: Model name to use (default: "openai/gpt-oss-20b")
        """
        self.api_key = api_key
        self.model = model
        self.client = Groq(api_key=api_key)
    
    def generate_response(
        self, 
        system_instruction: str, 
        prompt: str, 
        output_schema: BaseModel,
        print_tokens: bool = True,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ) -> Tuple[dict, Dict[str, int]]:
        """
        Generate a response from the AI model with retry logic.
        
        Args:
            system_instruction: System instruction for the AI model
            prompt: User prompt/query
            output_schema: Pydantic model defining the expected output schema
            print_tokens: Whether to print token usage (default: True)
            max_retries: Maximum number of retry attempts (default: 3, total attempts = 3)
            retry_delay: Initial delay between retries in seconds (default: 1.0)
        
        Returns:
            Tuple of (response_dict, token_info_dict) where token_info contains:
                - prompt_tokens: Number of tokens in the prompt
                - completion_tokens: Number of tokens in the completion
                - total_tokens: Total tokens used
        
        Raises:
            Exception: If all retry attempts fail
        """
        last_exception = None
        
        for attempt in range(1, max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": output_schema.__class__.__name__.lower(),
                            "schema": output_schema.model_json_schema()
                        }
                    }
                )
                
                # Parse the response
                response_content = response.choices[0].message.content
                
                # Extract token information from Groq response
                if hasattr(response, 'usage') and response.usage:
                    prompt_tokens = response.usage.prompt_tokens if hasattr(response.usage, 'prompt_tokens') else 0
                    completion_tokens = response.usage.completion_tokens if hasattr(response.usage, 'completion_tokens') else 0
                    total_tokens = response.usage.total_tokens if hasattr(response.usage, 'total_tokens') else 0
                else:
                    prompt_tokens = 0
                    completion_tokens = 0
                    total_tokens = 0
                
                if print_tokens:
                    print(f"Prompt tokens: {prompt_tokens}")
                    print(f"Completion tokens: {completion_tokens}")
                    print(f"Total tokens: {total_tokens}")
                
                # Parse JSON response
                parsed_response = json.loads(response_content)
                
                # Clean up the response to handle common LLM formatting issues
                parsed_response = _clean_response(parsed_response)
                
                # Validate with Pydantic model
                validated_response = output_schema.model_validate(parsed_response)
                
                # Return response dict and token information
                token_info = {
                    'prompt_tokens': prompt_tokens,
                    'completion_tokens': completion_tokens,
                    'total_tokens': total_tokens
                }
                
                return validated_response.model_dump(), token_info
                
            except Exception as e:
                last_exception = e
                error_type = type(e).__name__
                error_msg = str(e)
                
                # Check if this is a retryable error
                is_retryable = self._is_retryable_error(e)
                
                if not is_retryable or attempt >= max_retries:
                    # Don't retry non-retryable errors or if we've exhausted retries
                    if attempt >= max_retries:
                        print(f"Groq API call failed after {max_retries} attempts. Last error: {error_type}: {error_msg}")
                    raise
                
                # Calculate exponential backoff delay
                delay = retry_delay * (2 ** (attempt - 1))
                print(f"Groq API call failed (attempt {attempt}/{max_retries}): {error_type}: {error_msg}")
                print(f"Retrying in {delay:.2f} seconds...")
                time.sleep(delay)
        
        # This should never be reached, but just in case
        if last_exception:
            raise last_exception
        raise Exception("Failed to generate response after retries")
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """
        Determine if an error is retryable.
        
        Args:
            error: The exception that occurred
        
        Returns:
            bool: True if the error is retryable, False otherwise
        """
        error_type = type(error).__name__
        error_msg = str(error).lower()
        
        # Retryable errors (network issues, rate limits, temporary failures)
        retryable_errors = [
            "rate limite",
            "quota",
            "429",
            "503",
            "502",
            "500",
            "timeout",
            "connection",
            "network",
            "temporary",
            "unavailable",
            "service unavailable",
            "internal error",
            "deadline exceeded",
            "resource exhausted"
        ]
        
        # Non-retryable errors (authentication, invalid request, etc.)
        non_retryable_errors = [
            "401",
            "403",
            "400",
            "invalid",
            "authentication",
            "authorization",
            "forbidden",
            "unauthorized",
            "bad request",
            "not found",
            "404"
        ]
        
        # Check for non-retryable errors first
        for non_retryable in non_retryable_errors:
            if non_retryable in error_msg:
                return False
        
        # Check for retryable errors
        for retryable in retryable_errors:
            if retryable in error_msg:
                return True
        
        # Default: retry unknown errors (they might be temporary)
        return True
    
    def set_model(self, model: str):
        """
        Update the model to use.
        
        Args:
            model: New model name
        """
        self.model = model
    
    def set_api_key(self, api_key: str):
        """
        Update the API key.
        
        Args:
            api_key: New API key
        """
        self.api_key = api_key
        self.client = Groq(api_key=api_key)

