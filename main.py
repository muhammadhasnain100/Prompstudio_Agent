# from service.service import AIService
# from agent.intent_agent import classify_intent
# from agent.governance_agent import apply_governance
# from agent.planning_agent import create_execution_plan
# from agent.visualization_agent import create_visualizations
# from agent.analyze_ai_agent import analyze_execution_plan
# from dotenv import load_dotenv
# import json
# import time
# import uuid
# import os

# # Load environment variables from .env file
# load_dotenv()


# # Sample request data
# request = {
#   "request_id": "req-12345",
#   "execution_id": "exec-67890",
#   "timestamp": "2025-01-15T10:00:00Z",
#   "user_context": {
#     "user_id": 1,
#     "workspace_id": 5,
#     "organization_id": 10,
#     "roles": ["analyst", "sales"],
#     "permissions": ["read:customers", "read:orders"],
#     "attributes": {
#       "assigned_region": "US-WEST",
#       "department": "Sales"
#     }
#   },
#   "user_prompt": "Show me top 10 customers by revenue this quarter",
#   "data_sources": [
#     {
#       "data_source_id": 1,
#       "name": "PostgreSQL Production",
#       "type": "postgresql",
#       "schemas": [
#         {
#           "schema_name": "public",
#           "tables": [
#             {
#               "table_name": "customers",
#               "table_type": "table",
#               "row_count": 45000,
#               "indexes": ["idx_region", "idx_segment"],
#               "columns": [
#                 {
#                   "column_name": "id",
#                   "column_type": "integer",
#                   "is_nullable": False,
#                   "is_primary_key": True,
#                   "is_foreign_key": False,
#                   "column_comment": "Customer ID"
#                 },
#                 {
#                   "column_name": "name",
#                   "column_type": "varchar(255)",
#                   "is_nullable": False,
#                   "is_primary_key": False,
#                   "is_foreign_key": False
#                 },
#                 {
#                   "column_name": "revenue",
#                   "column_type": "decimal(10,2)",
#                   "is_nullable": True,
#                   "is_primary_key": False,
#                   "is_foreign_key": False
#                 },
#                 {
#                   "column_name": "region",
#                   "column_type": "varchar(50)",
#                   "is_nullable": True
#                 },
#                 {
#                   "column_name": "email",
#                   "column_type": "varchar(255)",
#                   "is_nullable": False,
#                   "pii": True
#                 }
#               ]
#             }
#           ]
#         }
#       ],
#       "governance_policies": {
#         "row_level_security": {
#           "enabled": True,
#           "rules": [
#             {
#               "condition": "region IN (SELECT region FROM user_access WHERE user_id = {user_id})",
#               "description": "Users can only see customers in their assigned regions"
#             }
#           ]
#         },
#         "column_masking": {
#           "enabled": True,
#           "rules": [
#             {
#               "column": "email",
#               "condition": "region != {user.attributes.assigned_region}",
#               "masking_function": "email_mask",
#               "description": "Mask emails for users outside assigned region"
#             }
#           ]
#         }
#       }
#     }
#   ],
#   "selected_schema_names": ["public"],
#   "execution_context": {
#     "max_rows": 1000,
#     "timeout_seconds": 30
#   },
#   "ai_model": "rgen_alpha_v2",
#   "temperature": 0.1,
#   "include_visualization": True
# }


# def main():
#     """
#     Main function that combines all agents: intent, governance, planning, visualization, and analysis.
#     """
#     start_time = time.time()
#     total_tokens = 0
    
#     # Initialize AI Service
#     api_key = os.getenv("GEMINI_API_KEY")
#     if not api_key or api_key.strip() == "":
#         raise ValueError("GEMINI_API_KEY is required. Please set it in your .env file or environment variables.")
    
#     model = "gemini-2.5-flash-lite"
#     service = AIService(api_key=api_key, model=model)
    
#     # Generate plan_id
#     plan_id = f"plan-{uuid.uuid4().hex[:8]}"
    
#     print("=" * 80)
#     print("INTENT CLASSIFICATION")
#     print("=" * 80)
    
#     # Step 1: Classify Intent
#     intent_result, tokens = classify_intent(service, request)
#     total_tokens += tokens
    
#     print("\nIntent Result:")
#     print(json.dumps(intent_result, indent=2))
    
#     print("\n" + "=" * 80)
#     print("GOVERNANCE APPLICATION")
#     print("=" * 80)
    
#     # Step 2: Apply Governance
#     governance_result, tokens = apply_governance(service, request, intent_result)
#     total_tokens += tokens
    
#     print("\nGovernance Result:")
#     print(json.dumps(governance_result, indent=2))
    
#     print("\n" + "=" * 80)
#     print("EXECUTION PLANNING")
#     print("=" * 80)
    
#     # Step 3: Create Execution Plan
#     execution_plan, tokens = create_execution_plan(service, request, intent_result, governance_result)
#     total_tokens += tokens
    
#     print("\nExecution Plan:")
#     print(json.dumps(execution_plan, indent=2))
    
#     # Step 4: Create Visualizations (if requested)
#     visualizations = []
#     if request.get('include_visualization', False):
#         print("\n" + "=" * 80)
#         print("VISUALIZATION GENERATION")
#         print("=" * 80)
        
#         visualizations, tokens = create_visualizations(service, request, intent_result, execution_plan)
#         total_tokens += tokens
        
#         print("\nVisualizations:")
#         print(json.dumps(visualizations, indent=2))
    
#     # Step 5: Analyze Execution Plan
#     print("\n" + "=" * 80)
#     print("AI ANALYSIS")
#     print("=" * 80)
    
#     # Calculate generation time before analysis (includes all previous steps)
#     generation_time_ms = int((time.time() - start_time) * 1000)
    
#     analyze_result, tokens = analyze_execution_plan(
#         service, request, intent_result, governance_result, execution_plan,
#         tokens_used=total_tokens,
#         generation_time_ms=generation_time_ms
#     )
#     total_tokens += tokens
    
#     # Final generation time (includes analysis step)
#     final_generation_time_ms = int((time.time() - start_time) * 1000)
    
#     print("\nAnalysis Result:")
#     print(json.dumps(analyze_result, indent=2))
    
#     print("\n" + "=" * 80)
#     print("FINAL OUTPUT")
#     print("=" * 80)
    
#     # Update ai_metadata with final token count and time
#     ai_metadata = analyze_result.get('ai_metadata', {})
#     ai_metadata['tokens_used'] = total_tokens
#     ai_metadata['generation_time_ms'] = final_generation_time_ms
    
#     # Build final response in the requested format
#     final_output = {
#         "request_id": request.get('request_id', ''),
#         "execution_id": request.get('execution_id', ''),
#         "plan_id": plan_id,
#         "status": "success",
#         "timestamp": request.get('timestamp', ''),
#         "intent_type": intent_result.get('intent_type', ''),
#         "intent_summary": intent_result.get('intent_summary', ''),
#         "execution_plan": execution_plan,
#         "ai_metadata": ai_metadata,
#         "suggestions": analyze_result.get('suggestions', [])
#     }
    
#     # Only include visualization if requested
#     if request.get('include_visualization', False):
#         final_output["visualization"] = visualizations
    
#     print("\nFinal Response:")
#     print(json.dumps(final_output, indent=2))
    
#     return final_output


# if __name__ == "__main__":
#     main()
