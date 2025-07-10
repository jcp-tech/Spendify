"""
Receipt Classifier Agent Pipeline

This module defines the root agent for the receipt classification application.
It uses a sequential agent with an initial receipt classifier followed by a refinement loop.
"""

from google.adk.agents import LoopAgent, SequentialAgent

from .subagents.classifier_init import initial_classifier
from .subagents.classification_grouper import grouping_classification
from .subagents.classification_reviewer import validate_classification
from .subagents.classification_refiner import refine_classifier
from .subagents.classification_response import response_agent

# SEQUENTIAL AGENT
  # INITIAL CLASSIFIER AGENT
  # LOOP AGENT
    # VALIDATION AGENT (reviewer)
    # CORRECTION AGENT (refiner)
    # RESPONSE AGENT (final response)

refinement_loop = LoopAgent(
    name="RefineClassificationLoop",
    max_iterations=2,
    sub_agents=[
        validate_classification,
        refine_classifier,
    ],
    description="Iteratively reviews and refines a receipt classification until the Classification Totals match with Given Totals",
)

# Create the Sequential Pipeline
root_agent = SequentialAgent(
    name="ReceiptClassificationPipeline",
    sub_agents=[
        initial_classifier,  # Step 1: Generate initial classification
        grouping_classification,  # Step 2: Group items by category, price, and quantity
        refinement_loop,  # Step 3: Review and refine in a loop
        response_agent,  # Step 4: Final response agent to respond with the final classification | To Save in Firebase
    ],
    description="Generates and refines a receipt classification through an iterative review process",
)
