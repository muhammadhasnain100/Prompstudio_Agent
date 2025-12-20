"""AI Service for LLM interactions with retry logic and async support."""

import os
import time
import asyncio
import logging
from typing import Dict, Any, Optional, Type
from concurrent.futures import ThreadPoolExecutor
from groq import Groq
from pydantic import BaseModel
from utils import retry_on_failure

logger = logging.getLogger(__name__)

# Thread pool executor for running sync Groq calls in async context
_executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="ai_service")


class AIServiceError(Exception):
    """Custom exception for AI service errors."""
    pass


class AIService:
    """Service for interacting with Groq LLM API with retry logic and error handling."""
    
    def __init__(self, api_key: str, model: str = "meta-llama/llama-4-scout-17b-16e-instruct"):
        """
        Initialize the AI service.
        
        Args:
            api_key: Groq API key
            model: Model name to use
        """
        if not api_key:
            raise AIServiceError("API key is required")
        
        self.client = Groq(api_key=api_key)
        self.model = model
        logger.info(f"AI Service initialized with model: {model}")
    
    def _generate_response_sync(
        self,
        system_instruction: str,
        prompt: str,
        output_schema: Type[BaseModel],
        max_completion_tokens: int = 4096,
        timeout: int = 120
    ) -> tuple[Dict[str, Any], Dict[str, int]]:
        """
        Generate a response from the LLM with retry logic.
        
        Args:
            system_instruction: System prompt/instruction
            prompt: User prompt
            output_schema: Pydantic model for output validation
            max_completion_tokens: Maximum tokens for completion
            timeout: Request timeout in seconds
        
        Returns:
            Tuple of (response_dict, token_info)
        
        Raises:
            AIServiceError: If generation fails after retries
        """
        start_time = time.time()
        
        try:
            # Get JSON schema from Pydantic model
            schema = output_schema.model_json_schema()
            # Remove any strict validation that might cause issues
            schema.pop('additionalProperties', None)
            
            logger.debug(f"Calling LLM API with model: {self.model}")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt},
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": output_schema.__class__.__name__.lower(),
                        "schema": schema,
                        "strict": False
                    }
                },
                max_completion_tokens=max_completion_tokens,
                timeout=timeout,
            )
            
            generation_time_ms = int((time.time() - start_time) * 1000)
            
            # Parse the response
            response_content = response.choices[0].message.content
            
            # Extract token information
            if hasattr(response, 'usage') and response.usage:
                prompt_tokens = response.usage.prompt_tokens if hasattr(response.usage, 'prompt_tokens') else 0
                completion_tokens = response.usage.completion_tokens if hasattr(response.usage, 'completion_tokens') else 0
            else:
                prompt_tokens = 0
                completion_tokens = 0
            
            token_info = {
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'generation_time_ms': generation_time_ms
            }
            
            # Validate and parse JSON response
            import json
            try:
                response_dict = json.loads(response_content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {str(e)}")
                raise AIServiceError(f"Invalid JSON response from LLM: {str(e)}")
            
            # Validate response against schema - fail if validation fails
            try:
                validated_response = output_schema.model_validate(response_dict)
                response_dict = validated_response.model_dump()
            except Exception as e:
                logger.error(
                    f"Schema validation failed: {str(e)} - "
                    f"Response keys: {list(response_dict.keys()) if response_dict else 'None'}"
                )
                raise AIServiceError(f"Schema validation failed: {str(e)}")
            
            logger.info(
                f"LLM response generated successfully in {generation_time_ms}ms. "
                f"Tokens: {prompt_tokens} prompt + {completion_tokens} completion"
            )
            
            return response_dict, token_info
            
        except Exception as e:
            generation_time_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"Failed to generate LLM response after {generation_time_ms}ms: {str(e)}",
                exc_info=True
            )
            raise AIServiceError(f"LLM API call failed: {str(e)}") from e
    
    @retry_on_failure(
        max_retries=3,
        delay=1.0,
        backoff_factor=2.0,
        exceptions=(Exception,),
        logger_instance=logger
    )
    async def generate_response(
        self,
        system_instruction: str,
        prompt: str,
        output_schema: Type[BaseModel],
        max_completion_tokens: int = 4096,
        timeout: int = 120
    ) -> tuple[Dict[str, Any], Dict[str, int]]:
        """
        Generate a response from the LLM with retry logic (async).
        
        Args:
            system_instruction: System prompt/instruction
            prompt: User prompt
            output_schema: Pydantic model for output validation
            max_completion_tokens: Maximum tokens for completion
            timeout: Request timeout in seconds
        
        Returns:
            Tuple of (response_dict, token_info)
        
        Raises:
            AIServiceError: If generation fails after retries
        """
        loop = asyncio.get_event_loop()
        try:
            # Run sync Groq call in thread pool to avoid blocking
            result = await loop.run_in_executor(
                _executor,
                self._generate_response_sync,
                system_instruction,
                prompt,
                output_schema,
                max_completion_tokens,
                timeout
            )
            return result
        except Exception as e:
            logger.error(f"Async LLM generation failed: {str(e)}", exc_info=True)
            raise AIServiceError(f"Async LLM API call failed: {str(e)}") from e
