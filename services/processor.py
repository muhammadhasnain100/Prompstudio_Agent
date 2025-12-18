"""Unified agent that processes all tasks in a single LLM API call."""

from typing import Dict, Tuple
from schemas.agent import UnifiedOutput
from core.prompts import build_unified_prompt
from services.ai import AIService


def process_unified(
    service: AIService,
    request: Dict,
    data_source_index: int = 0,
    include_visualization: bool = False
) -> Tuple[Dict, Dict[str, int]]:
    """
    Process the request through all agents in a single unified call.
    
    Args:
        service: AIService instance for generating responses
        request: The request dictionary containing user prompt, context, and data sources
        data_source_index: Index of the data source to use (default: 0)
        include_visualization: Whether to include visualization generation (default: False)
    
    Returns:
        Tuple of (unified_result_dict, token_info_dict) where token_info contains:
            - prompt_tokens: Number of tokens in the prompt
            - completion_tokens: Number of tokens in the completion
            - total_tokens: Total tokens used
    """
    # Build unified prompt
    system_instruction, prompt = build_unified_prompt(
        request, data_source_index, include_visualization
    )
    
    # Generate unified response
    unified_result, token_info = service.generate_response(
        system_instruction,
        prompt,
        UnifiedOutput,
        print_tokens=False
    )
    
    return unified_result, token_info
