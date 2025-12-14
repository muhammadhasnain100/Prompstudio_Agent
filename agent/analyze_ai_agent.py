from pydantic import BaseModel
from typing import List, Dict, Optional
import json

# Import shared database configuration constants
from database_config import get_database_type_name


class AIMetadata(BaseModel):
    """AI metadata including confidence and reasoning."""
    model: str
    confidence: float  # 0.0 to 1.0
    confidence_score: float  # 0.0 to 1.0 (same as confidence, for compatibility)
    tokens_used: Optional[int] = None
    generation_time_ms: Optional[int] = None
    explanation: str
    reasoning_steps: List[str]


class AnalyzeAIOutput(BaseModel):
    """Output from analyze AI agent."""
    confidence: int  # 0-100 scale
    confidence_score: float  # 0.0-1.0 scale (confidence / 100)
    explanation: str
    reasoning_steps: List[str]
    suggestions: List[str]


def get_analyze_ai_system_instruction(database_type: str) -> str:
    """
    Generate system instruction for analyze AI agent.
    
    Args:
        database_type: The database type name (e.g., "PostgreSQL", "MongoDB")
    
    Returns:
        str: The system instruction
    """
    system_instruction = f"""
You are an AI analysis agent specialized in evaluating execution plans for {database_type} database operations.

Your primary responsibilities:
1. Analyze the execution plan and assess its quality, correctness, and completeness
2. Provide a confidence score (0-100) indicating how confident you are that the plan will:
   - Correctly execute the user's request
   - Apply governance rules properly
   - Generate accurate results
   - Follow best practices for {database_type}
3. Explain your confidence assessment with clear reasoning
4. List the key reasoning steps that led to your assessment
5. Provide actionable suggestions for improvement if confidence is not 100%

Confidence Score Guidelines:
- 90-100: Excellent plan, very confident it will work correctly
- 80-89: Good plan with minor potential issues
- 70-79: Acceptable plan but has some concerns
- 60-69: Plan has notable issues that may cause problems
- Below 60: Plan has significant issues and may not work correctly

Factors to Consider:
1. **Query Correctness**: Does the query syntax match {database_type} standards?
2. **Governance Application**: Are row-level security and column masking rules properly applied?
3. **Intent Alignment**: Does the plan correctly address the user's intent?
4. **Data Access**: Are the correct tables/collections and columns/fields being accessed?
5. **Aggregations**: Are aggregations (if needed) correctly implemented?
6. **Filtering**: Are filters (including governance filters) correctly applied?
7. **Sorting and Limits**: Are sorting and limiting correctly implemented?
8. **Best Practices**: Does the plan follow {database_type} best practices?
9. **Completeness**: Are all necessary steps included?
10. **Dependencies**: Are step dependencies correctly defined?

Return only valid JSON matching the AnalyzeAIOutput schema.
"""
    
    return system_instruction


def build_analyze_ai_prompt(
    request: Dict,
    intent_result: Dict,
    governance_result: Dict,
    execution_plan: Dict
) -> str:
    """
    Build the analyze AI prompt with all necessary context.
    
    Args:
        request: The request dictionary
        intent_result: The intent classification result
        governance_result: The governance application result
        execution_plan: The execution plan result
    
    Returns:
        str: The detailed analyze AI prompt
    """
    user_prompt = request.get('user_prompt', '')
    intent_type = intent_result.get('intent_type', 'unknown')
    intent_summary = intent_result.get('intent_summary', '')
    
    analyze_prompt = f"""
=== USER REQUEST ===

User Prompt: "{user_prompt}"

=== INTENT CLASSIFICATION ===

Intent Type: {intent_type}
Intent Summary: {intent_summary}
Source Category: {intent_result.get('source_category', 'unknown')}
Needs Aggregation: {intent_result.get('needs_aggregation', False)}
Needs Join: {intent_result.get('needs_join', False)}
Needs Time Filter: {intent_result.get('needs_time_filter', False)}
Expected Rows: {intent_result.get('no_rows', 0)}

=== GOVERNANCE RULES ===

Row Filters:
{json.dumps(governance_result.get('row_filters', []), indent=2)}

Column Masking Rules:
{json.dumps(governance_result.get('column_masking_rules', []), indent=2)}

Governance Applied:
{json.dumps(governance_result.get('governance_applied', []), indent=2)}

=== EXECUTION PLAN ===

Strategy: {execution_plan.get('strategy', 'unknown')}
Plan Type: {execution_plan.get('type', 'unknown')}

Operations:
{json.dumps(execution_plan.get('operations', []), indent=2)}

=== YOUR TASK ===

Analyze the execution plan and provide:

1. **Confidence Score (0-100)**: How confident are you that this plan will correctly execute the user's request?
   - Consider query correctness, governance application, intent alignment, and best practices
   - Provide both a 0-100 integer score and a 0.0-1.0 float score

2. **Explanation**: A clear explanation of your confidence assessment, including:
   - What the plan does well
   - Any potential issues or concerns
   - How governance rules are applied
   - Overall assessment of plan quality

3. **Reasoning Steps**: List the key steps in your analysis:
   - What you checked (e.g., "Verified query syntax", "Checked governance rules")
   - What you found (e.g., "All row filters applied correctly", "Missing time filter")
   - Your conclusions (e.g., "Plan correctly implements user intent")

4. **Suggestions**: Provide actionable suggestions for improvement:
   - If confidence is high: Suggest optimizations or enhancements
   - If confidence is lower: Suggest fixes or improvements
   - Consider performance, security, correctness, and best practices

Be thorough and honest in your assessment. If there are issues, clearly identify them and suggest fixes.
"""
    
    return analyze_prompt


def analyze_execution_plan(
    service,
    request: Dict,
    intent_result: Dict,
    governance_result: Dict,
    execution_plan: Dict,
    tokens_used: Optional[int] = None,
    generation_time_ms: Optional[int] = None
) -> Dict:
    """
    Analyze the execution plan and provide confidence score, reasoning, and suggestions.
    
    Args:
        service: AIService instance for generating responses
        request: The request dictionary
        intent_result: The intent classification result
        governance_result: The governance application result
        execution_plan: The execution plan result
        tokens_used: Total tokens used so far (optional)
        generation_time_ms: Total generation time in ms (optional)
    
    Returns:
        Dictionary containing AI metadata with confidence, explanation, reasoning, and suggestions
    """
    # Get database type
    data_source = request['data_sources'][0]
    datasource_type = data_source.get('type', 'Unknown')
    database_type = get_database_type_name(datasource_type)
    
    # Build system instruction
    system_instruction = get_analyze_ai_system_instruction(database_type)
    
    # Build prompt
    analyze_prompt = build_analyze_ai_prompt(
        request, intent_result, governance_result, execution_plan
    )
    
    # Generate analysis
    analyze_output, tokens = service.generate_response(
        system_instruction,
        analyze_prompt,
        AnalyzeAIOutput
    )
    
    # Get confidence values
    confidence_100 = analyze_output.get('confidence', 0)  # 0-100
    confidence_01 = analyze_output.get('confidence_score', 0.0)  # 0.0-1.0
    
    # Build AI metadata
    ai_metadata = {
        "model": request.get('ai_model', 'rgen_alpha_v2'),
        "confidence": confidence_01,  # 0.0-1.0 for compatibility
        "confidence_score": confidence_01,  # 0.0-1.0
        "tokens_used": tokens_used,
        "generation_time_ms": generation_time_ms,
        "explanation": analyze_output.get('explanation', ''),
        "reasoning_steps": analyze_output.get('reasoning_steps', [])
    }
    
    return {
        "ai_metadata": ai_metadata,
        "suggestions": analyze_output.get('suggestions', [])
    }, tokens

