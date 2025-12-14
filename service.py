from google import genai
from google.genai import types
from pydantic import BaseModel
import json
import time
from typing import Optional, Tuple


class AIService:
    """
    Service class for AI model interactions.
    Handles communication with the AI model for generating responses.
    """
    
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash-lite"):
        """
        Initialize the AI Service.
        
        Args:
            api_key: API key for the AI model
            model: Model name to use (default: "gemini-2.5-flash-lite")
        """
        self.api_key = api_key
        self.model = model
        self.client = genai.Client(api_key=api_key)
    
    def generate_response(
        self, 
        system_instruction: str, 
        prompt: str, 
        output_schema: BaseModel,
        print_tokens: bool = True,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ) -> Tuple[dict, int]:
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
            Tuple of (response_dict, token_count)
        
        Raises:
            Exception: If all retry attempts fail
        """
        last_exception = None
        
        for attempt in range(1, max_retries + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="application/json",
                        response_schema=output_schema,
                    ),
                    contents=prompt,
                )
                
                token_count = response.usage_metadata.total_token_count
                if print_tokens:
                    print(f"Token usage: {token_count}")
                
                return json.loads(response.text), token_count
                
            except Exception as e:
                last_exception = e
                error_type = type(e).__name__
                error_msg = str(e)
                
                # Check if this is a retryable error
                is_retryable = self._is_retryable_error(e)
                
                if not is_retryable or attempt >= max_retries:
                    # Don't retry non-retryable errors or if we've exhausted retries
                    if attempt >= max_retries:
                        print(f"Gemini API call failed after {max_retries} attempts. Last error: {error_type}: {error_msg}")
                    raise
                
                # Calculate exponential backoff delay
                delay = retry_delay * (2 ** (attempt - 1))
                print(f"Gemini API call failed (attempt {attempt}/{max_retries}): {error_type}: {error_msg}")
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
        self.client = genai.Client(api_key=self.api_key)
    
    def set_api_key(self, api_key: str):
        """
        Update the API key.
        
        Args:
            api_key: New API key
        """
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)

