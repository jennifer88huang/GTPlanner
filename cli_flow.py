from pocketflow import Flow, AsyncFlow
from nodes import (
    AsyncInputProcessingNode,
    AsyncRequirementsAnalysisNode,
    AsyncDesignOptimizationNode,
    AsyncDocumentationGenerationNode,
    AsyncFeedbackProcessingNode
)

def create_requirement_engine_flow():
    """
    Create and return the requirements generation engine flow.
    
    This flow orchestrates the process of:
    1. Processing user input
    2. Analyzing requirements
    3. Suggesting design optimizations
    4. Generating technical documentation
    5. Processing user feedback
    
    With a feedback loop that can return to the requirements analysis step.
    
    Returns:
        AsyncFlow: The configured flow
    """
    # Define async nodes
    input_node = AsyncInputProcessingNode()
    analysis_node = AsyncRequirementsAnalysisNode()
    optimization_node = AsyncDesignOptimizationNode()
    doc_gen_node = AsyncDocumentationGenerationNode()
    feedback_node = AsyncFeedbackProcessingNode()
    
    # Connect in sequence
    input_node >> analysis_node >> optimization_node >> doc_gen_node >> feedback_node
    
    # Define branching from feedback node
    feedback_node - "new_iteration" >> analysis_node  # Loop back for another iteration
    # "complete" action terminates the flow naturally
    
    # Create the main async flow
    return AsyncFlow(start=input_node)

# Create the flow for use in main.py
requirement_engine_flow = create_requirement_engine_flow() 