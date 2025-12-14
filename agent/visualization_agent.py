from pydantic import BaseModel
from typing import List, Dict, Optional
import json

# Import shared database configuration constants
from database_config import get_database_type_name


class VisualizationConfig(BaseModel):
    """Configuration for a visualization."""
    sortable: Optional[bool] = None
    filterable: Optional[bool] = None
    orientation: Optional[str] = None
    color_scheme: Optional[str] = None


class Visualization(BaseModel):
    """A single visualization recommendation."""
    type: str  # table, bar, line, pie, scatter, etc.
    title: str
    x_axis: Optional[str] = None
    y_axis: Optional[str] = None
    config: VisualizationConfig
    is_primary: bool = False


class VisualizationOutput(BaseModel):
    """Output from visualization agent."""
    visualizations: List[Visualization]


def get_visualization_system_instruction(database_type: str) -> str:
    """
    Generate system instruction for visualization agent.
    
    Args:
        database_type: The database type name (e.g., "PostgreSQL", "MongoDB")
    
    Returns:
        str: The system instruction
    """
    system_instruction = f"""
You are a data visualization agent specialized in recommending appropriate visualizations for {database_type} query results.

Your primary responsibilities:
1. Analyze the execution plan and identify the data structure and columns that will be returned
2. Determine the most appropriate visualization types based on:
   - The intent type and query purpose
   - The number and types of columns in the result set
   - Whether the data is aggregated, time-series, categorical, or numerical
   - The relationships between columns
3. Recommend visualizations that best represent the data:
   - Tables for detailed data views
   - Bar charts for categorical comparisons
   - Line charts for time-series data
   - Pie charts for proportional data
   - Scatter plots for relationships
   - And other appropriate chart types
4. Mark one visualization as primary (is_primary: true) - typically a table for detailed view
5. Provide appropriate titles, axis labels, and configuration options

Key Guidelines:
- **Generate multiple visualizations** (1, 2, 3, or more) based on:
  - The complexity of the data and query
  - The number of dimensions and metrics
  - The user's intent and what insights they might need
  - Different perspectives on the same data (detailed vs summary, different chart types)
- Always include at least one **table** visualization for detailed data viewing (mark as primary)
- For analytical queries, consider multiple visualizations:
  - Table for detailed view (primary)
  - Bar/Line chart for comparisons or trends
  - Additional charts if data has multiple dimensions or relationships
- Consider the user's intent when recommending visualizations:
  - Top N queries: table + bar chart
  - Time-series: table + line chart
  - Comparisons: table + bar chart + potentially pie chart
  - Aggregations: table + appropriate chart type
- Provide meaningful titles that describe what the visualization shows
- Set appropriate axis labels (x_axis, y_axis) for charts
- Always include a **config** object with relevant options:
  - For tables: sortable, filterable
  - For charts: orientation, color_scheme
- Mark exactly one visualization as primary (is_primary: true) - typically the table
- The number of visualizations should match the complexity and value of the data

Return a list of visualizations (can be 1, 2, 3, or more depending on the problem, conditions, and data).

Return only valid JSON matching the VisualizationOutput schema.
"""
    
    return system_instruction


def build_visualization_prompt(
    request: Dict,
    intent_result: Dict,
    execution_plan: Dict
) -> str:
    """
    Build the visualization prompt with all necessary context.
    
    Args:
        request: The request dictionary
        intent_result: The intent classification result
        execution_plan: The execution plan result
    
    Returns:
        str: The detailed visualization prompt
    """
    user_prompt = request.get('user_prompt', '')
    intent_type = intent_result.get('intent_type', 'unknown')
    intent_summary = intent_result.get('intent_summary', '')
    
    # Extract operations and their projections
    operations = execution_plan.get('operations', [])
    
    # Build operations summary
    operations_summary = []
    for op in operations:
        op_info = {
            'step_id': op.get('step_id', ''),
            'description': op.get('description', ''),
            'projections': op.get('query_payload', {}).get('projections', []),
            'output_artifact': op.get('output_artifact', '')
        }
        operations_summary.append(op_info)
    
    visualization_prompt = f"""
=== USER REQUEST ===

User Prompt: "{user_prompt}"

=== INTENT CLASSIFICATION ===

Intent Type: {intent_type}
Intent Summary: {intent_summary}

=== EXECUTION PLAN ===

Strategy: {execution_plan.get('strategy', 'unknown')}
Plan Type: {execution_plan.get('type', 'unknown')}

Operations:
{json.dumps(operations_summary, indent=2)}

=== YOUR TASK ===

Analyze the execution plan and recommend appropriate visualizations for the query results.

Consider:
1. **Data Structure**: What columns/fields will be returned in the result set?
2. **Data Types**: Are the columns numerical, categorical, temporal, or text?
3. **Intent**: What is the user trying to accomplish? (e.g., compare values, see trends, view details)
4. **Aggregations**: Are there aggregations (SUM, COUNT, AVG) that suggest specific chart types?
5. **Sorting**: Is the data sorted (e.g., top N, ordered by value)?
6. **Relationships**: Are there relationships between columns that would benefit from specific visualizations?

Recommend **multiple visualizations** (1, 2, 3, or more) that:
- Help users understand the data effectively from different perspectives
- Match the intent and purpose of the query
- Provide both detailed (table) and summary (chart) views
- Are appropriate for the data structure and types
- Offer complementary insights (e.g., table for details, chart for patterns)

**Number of Visualizations Guidelines:**
- **Simple queries** (single metric, few rows): 1-2 visualizations (table + optional chart)
- **Analytical queries** (aggregations, comparisons): 2-3 visualizations (table + 1-2 charts)
- **Complex queries** (multiple dimensions, relationships): 3+ visualizations (table + multiple chart types)
- Always include at least a table for detailed viewing

**Visualization Types to Consider:**
- **table**: For detailed data viewing with all columns (ALWAYS include as primary)
- **bar**: For comparing categorical values (vertical or horizontal) - great for top N, comparisons
- **line**: For time-series or sequential data - shows trends over time
- **pie**: For showing proportions or percentages - useful for distribution analysis
- **scatter**: For showing relationships between two numerical variables
- **area**: For cumulative values over time
- **heatmap**: For showing correlations or patterns in matrix data

**For each visualization, provide:**
- type: The visualization type (required)
- title: A descriptive title (required)
- x_axis: X-axis field name (for charts, optional for tables)
- y_axis: Y-axis field name (for charts, optional for tables)
- config: Configuration object (REQUIRED) with:
  - For tables: sortable (bool), filterable (bool)
  - For charts: orientation ("vertical" or "horizontal"), color_scheme (string like "default", "neon", etc.)
- is_primary: true for exactly one visualization (the table), false for all others

**Examples:**
- Top 10 customers: table (primary) + bar chart
- Revenue by region: table (primary) + bar chart + pie chart
- Time series data: table (primary) + line chart
- Simple query: table (primary) only

Return a list of recommended visualizations based on the problem complexity, data structure, and user intent.
"""
    
    return visualization_prompt


def create_visualizations(
    service,
    request: Dict,
    intent_result: Dict,
    execution_plan: Dict
) -> List[Dict]:
    """
    Create visualization recommendations based on execution plan.
    
    Args:
        service: AIService instance for generating responses
        request: The request dictionary
        intent_result: The intent classification result
        execution_plan: The execution plan result
    
    Returns:
        List of visualization dictionaries
    """
    # Get database type
    data_source = request['data_sources'][0]
    datasource_type = data_source.get('type', 'Unknown')
    database_type = get_database_type_name(datasource_type)
    
    # Build system instruction
    system_instruction = get_visualization_system_instruction(database_type)
    
    # Build prompt
    visualization_prompt = build_visualization_prompt(
        request, intent_result, execution_plan
    )
    
    # Generate visualizations
    visualization_output, tokens = service.generate_response(
        system_instruction,
        visualization_prompt,
        VisualizationOutput
    )
    
    return visualization_output.get('visualizations', []), tokens

