from __future__ import annotations

from langgraph.graph import END, StateGraph

from backend.agents.civil_defense import civil_defense_node
from backend.agents.disaster_prediction import disaster_prediction_node
from backend.agents.emergency_response import emergency_response_node
from backend.agents.environmental_data import ingest_environmental_data
from backend.agents.forecasting import forecast_rainfall
from backend.agents.human_gatekeeper import approval_route, human_gatekeeper_node
from backend.agents.memory_update import memory_update_node
from backend.agents.news_monitor import news_monitor_node
from backend.agents.notification_sender import send_alert_node
from backend.agents.public_works import public_works_node
from backend.agents.reflection import reflection_node
from backend.agents.router import route_from_department, routing_node
from backend.agents.severity_assessor import severity_assessor_node
from backend.graphs.state import DisasterState


def build_graph():
    graph = StateGraph(DisasterState)
    graph.add_node("data_collection", ingest_environmental_data)
    graph.add_node("forecast", forecast_rainfall)
    graph.add_node("disaster_prediction", disaster_prediction_node)
    graph.add_node("news_monitor", news_monitor_node)
    graph.add_node("severity_assessor", severity_assessor_node)
    graph.add_node("router", routing_node)
    graph.add_node("public_works_agent", public_works_node)
    graph.add_node("civil_defense_agent", civil_defense_node)
    graph.add_node("emergency_response_agent", emergency_response_node)
    graph.add_node("human_gatekeeper", human_gatekeeper_node)
    graph.add_node("send_alert", send_alert_node)
    graph.add_node("reflection", reflection_node)
    graph.add_node("memory_update", memory_update_node)

    graph.set_entry_point("data_collection")
    graph.add_edge("data_collection", "forecast")
    graph.add_edge("forecast", "disaster_prediction")
    graph.add_edge("forecast", "news_monitor")
    graph.add_edge("disaster_prediction", "severity_assessor")
    graph.add_edge("news_monitor", "severity_assessor")
    graph.add_edge("severity_assessor", "router")
    graph.add_conditional_edges(
        "router",
        route_from_department,
        {
            "public_works": "public_works_agent",
            "civil_defense": "civil_defense_agent",
            "emergency_response": "emergency_response_agent",
            "none": END,
        },
    )
    graph.add_edge("public_works_agent", "human_gatekeeper")
    graph.add_edge("civil_defense_agent", "human_gatekeeper")
    graph.add_edge("emergency_response_agent", "human_gatekeeper")
    graph.add_conditional_edges(
        "human_gatekeeper",
        approval_route,
        {
            "approved": "send_alert",
            "rejected": "reflection",
        },
    )
    graph.add_edge("send_alert", END)
    graph.add_edge("reflection", "memory_update")
    graph.add_conditional_edges(
        "memory_update",
        route_from_department,
        {
            "public_works": "public_works_agent",
            "civil_defense": "civil_defense_agent",
            "emergency_response": "emergency_response_agent",
            "none": END,
        },
    )

    return graph.compile()
