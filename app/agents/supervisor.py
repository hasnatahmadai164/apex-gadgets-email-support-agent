from functools import lru_cache
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from pydantic import BaseModel

from app.agents.orders_agent import handle_order_request
from app.agents.rag_agent import answer_question
from app.agents.tickets_agent import handle_ticket_request
from app.core.checkpointer import get_checkpointer
from app.core.config import get_settings
from app.core.graph_state import GraphState
from app.core.llm import build_chat_model
from app.core.schemas import EmailMessage
from app.triage.relevance_classifier import classify_relevance
from app.triage.sensitivity_classifier import classify_sensitivity

ROUTE_SYSTEM_PROMPT = (
    "You route an Apex Gadgets customer email to the right handler. Choose rag "
    "for general product or policy questions that don't involve placing an "
    "order or reporting a problem. Choose orders for anything about placing an "
    "order or checking an existing order's status. Choose tickets for "
    "problems, complaints, or requests for help that should be tracked as a "
    "support issue, or for checking an existing ticket's status."
)

MAX_QA_HISTORY_TURNS = 5


class RouteResult(BaseModel):
    route: Literal["rag", "orders", "tickets"]


def classify_route(email: EmailMessage, llm=None) -> RouteResult:
    structured_llm = llm or build_chat_model(
        get_settings().azure_openai_specialist_deployment
    ).with_structured_output(RouteResult)
    user_content = f"From: {email.sender}\nSubject: {email.subject}\n\n{email.body}"
    return structured_llm.invoke(
        [SystemMessage(content=ROUTE_SYSTEM_PROMPT), HumanMessage(content=user_content)]
    )


def relevance_gate_node(state: GraphState) -> dict:
    result = classify_relevance(state["email"])
    return {"is_relevant": result.is_relevant}


def sensitivity_gate_node(state: GraphState) -> dict:
    result = classify_sensitivity(state["email"])
    return {"is_sensitive": result.is_sensitive}


def mark_irrelevant_node(state: GraphState) -> dict:
    return {"category": "irrelevant"}


def mark_needs_review_node(state: GraphState) -> dict:
    return {"category": "needs_review"}


def route_specialist_node(state: GraphState) -> dict:
    if state.get("pending_order") is not None:
        return {"route": "orders"}
    if state.get("pending_ticket") is not None:
        return {"route": "tickets"}

    result = classify_route(state["email"])
    return {"route": result.route}


def rag_node(state: GraphState) -> dict:
    history = state.get("qa_history") or []
    answer = answer_question(state["email"].body, history=history)
    updated_history = (history + [{"question": state["email"].body, "answer": answer}])[
        -MAX_QA_HISTORY_TURNS:
    ]
    return {"reply_text": answer, "category": "handled", "qa_history": updated_history}


def orders_node(state: GraphState, config: dict) -> dict:
    session = config["configurable"]["session"]
    result = handle_order_request(state["email"], state.get("pending_order"), session)
    return {
        "reply_text": result.reply_text,
        "pending_order": result.pending_order,
        "category": "handled",
    }


def tickets_node(state: GraphState, config: dict) -> dict:
    session = config["configurable"]["session"]
    result = handle_ticket_request(state["email"], state.get("pending_ticket"), session)
    return {
        "reply_text": result.reply_text,
        "pending_ticket": result.pending_ticket,
        "category": "handled",
    }


def _route_after_relevance(state: GraphState) -> str:
    return "continue" if state["is_relevant"] else "irrelevant"


def _route_after_sensitivity(state: GraphState) -> str:
    return "needs_review" if state["is_sensitive"] else "continue"


def _dispatch_specialist(state: GraphState) -> str:
    return state["route"]


@lru_cache
def build_supervisor_graph():
    graph = StateGraph(GraphState)
    graph.add_node("relevance_gate", relevance_gate_node)
    graph.add_node("sensitivity_gate", sensitivity_gate_node)
    graph.add_node("mark_irrelevant", mark_irrelevant_node)
    graph.add_node("mark_needs_review", mark_needs_review_node)
    graph.add_node("route_specialist", route_specialist_node)
    graph.add_node("rag", rag_node)
    graph.add_node("orders", orders_node)
    graph.add_node("tickets", tickets_node)

    graph.set_entry_point("relevance_gate")
    graph.add_conditional_edges(
        "relevance_gate",
        _route_after_relevance,
        {"continue": "sensitivity_gate", "irrelevant": "mark_irrelevant"},
    )
    graph.add_conditional_edges(
        "sensitivity_gate",
        _route_after_sensitivity,
        {"continue": "route_specialist", "needs_review": "mark_needs_review"},
    )
    graph.add_conditional_edges(
        "route_specialist",
        _dispatch_specialist,
        {"rag": "rag", "orders": "orders", "tickets": "tickets"},
    )
    graph.add_edge("mark_irrelevant", END)
    graph.add_edge("mark_needs_review", END)
    graph.add_edge("rag", END)
    graph.add_edge("orders", END)
    graph.add_edge("tickets", END)

    return graph.compile(checkpointer=get_checkpointer())


def process_email(email: EmailMessage, session) -> GraphState:
    graph = build_supervisor_graph()
    config = {"configurable": {"thread_id": email.thread_id, "session": session}}
    return graph.invoke({"email": email}, config=config)
