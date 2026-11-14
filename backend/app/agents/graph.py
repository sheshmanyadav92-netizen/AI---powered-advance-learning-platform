"""LangGraph StateGraph orchestration connecting all five agents with shared LearnerState.
"""
from typing import Dict, Any
from langgraph.graph import StateGraph, START, END
from .state import LearnerState
from .skill_analysis import skill_analysis_node
from .career_matching import career_matching_node
from .recommendation import recommendation_node
from .progress_tracking import progress_tracking_node
from .mentor import mentor_node

def route_event(state: LearnerState) -> str:
    """Conditional entry routing based on last_event."""
    event = state.get("last_event", "profile_update")
    if event in ("new_assessment", "resource_completed"):
        return "progress_tracking"
    elif event == "goal_change":
        return "career_matching"
    else:
        return "skill_analysis"

def post_progress_routing(state: LearnerState) -> str:
    """Routes after progress tracking based on event type."""
    event = state.get("last_event", "")
    if event == "new_assessment":
        # New assessment updates Q_s and proficiency
        return "skill_analysis"
    return "recommendation"

def build_learner_graph():
    builder = StateGraph(LearnerState)

    # Register the 5 agent nodes
    builder.add_node("skill_analysis", skill_analysis_node)
    builder.add_node("career_matching", career_matching_node)
    builder.add_node("recommendation", recommendation_node)
    builder.add_node("progress_tracking", progress_tracking_node)
    builder.add_node("mentor", mentor_node)

    # Dynamic entry point based on event
    builder.add_conditional_edges(
        START,
        route_event,
        {
            "progress_tracking": "progress_tracking",
            "career_matching": "career_matching",
            "skill_analysis": "skill_analysis"
        }
    )

    # After progress tracking:
    builder.add_conditional_edges(
        "progress_tracking",
        post_progress_routing,
        {
            "skill_analysis": "skill_analysis",
            "recommendation": "recommendation"
        }
    )

    # Skill analysis feeds into career matching
    builder.add_edge("skill_analysis", "career_matching")

    # Career matching feeds into recommendation
    builder.add_edge("career_matching", "recommendation")

    # Recommendation feeds into mentor
    builder.add_edge("recommendation", "mentor")

    # Mentor concludes the orchestration
    builder.add_edge("mentor", END)

    return builder.compile()

# Singleton compiled graph
orchestrator_graph = build_learner_graph()

def run_agent_workflow(initial_state: LearnerState) -> LearnerState:
    """Invokes the multi-agent graph with the specified state."""
    return orchestrator_graph.invoke(initial_state)

