from functools import lru_cache
from typing import TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.llm import build_chat_model
from app.tools.pinecone_tools import retrieve_chunks

MAX_RETRIES = 2

CONTEXTUALIZE_SYSTEM_PROMPT = (
    "You rewrite a customer's question into a standalone question that makes "
    "sense without seeing the earlier conversation, using the conversation "
    "history provided. If the question already stands on its own, or there is "
    "no history, return it unchanged. Only rewrite it, do not answer it."
)

GRADE_SYSTEM_PROMPT = (
    "You judge whether retrieved knowledge base content is enough to answer a "
    "customer's question about Apex Gadgets products, orders, or policies. Mark "
    "it sufficient only if the content directly addresses the question. When "
    "genuinely unsure, mark it not sufficient, since a rewritten search is cheap "
    "and a wrong or incomplete answer sent to a customer is not."
)

REWRITE_SYSTEM_PROMPT = (
    "You rewrite a search query so it retrieves more relevant results from a "
    "product and policy knowledge base for Apex Gadgets. Keep the same intent as "
    "the original question, but use different or more specific wording, since "
    "the previous query did not retrieve enough useful content."
)

ANSWER_SYSTEM_PROMPT = (
    "You are answering a customer support email for Apex Gadgets, an online "
    "store selling phones and laptops. Answer the customer's question using "
    "only the knowledge base content provided below. If the content does not "
    "fully answer the question, say so honestly rather than guessing. Write in "
    "a friendly, concise tone suitable for a direct email reply, with no "
    "markdown formatting."
)


class RagState(TypedDict):
    query: str
    original_query: str
    retrieved_chunks: list[str]
    is_sufficient: bool
    retry_count: int
    answer: str
    history: list[dict]


class ContextualizeResult(BaseModel):
    standalone_question: str = Field(
        description="The question rewritten to stand alone, using conversation history"
    )


class GradeResult(BaseModel):
    is_sufficient: bool = Field(
        description="True if the retrieved chunks contain enough information to answer the question"
    )


class RewriteResult(BaseModel):
    rewritten_query: str = Field(
        description="A rewritten search query more likely to retrieve relevant chunks"
    )


def _format_history(history: list[dict]) -> str:
    return "\n".join(f"Q: {turn['question']}\nA: {turn['answer']}" for turn in history)


def contextualize_node(state: RagState) -> dict:
    history = state.get("history") or []
    if not history:
        return {}

    llm = build_chat_model(
        get_settings().azure_openai_specialist_deployment
    ).with_structured_output(ContextualizeResult)
    result = llm.invoke(
        [
            SystemMessage(content=CONTEXTUALIZE_SYSTEM_PROMPT),
            HumanMessage(
                content=f"Conversation history:\n{_format_history(history)}\n\nNew question: {state['original_query']}"
            ),
        ]
    )
    return {"query": result.standalone_question, "original_query": result.standalone_question}


def retrieve_node(state: RagState) -> dict:
    return {"retrieved_chunks": retrieve_chunks(state["query"])}


def grade_node(state: RagState) -> dict:
    llm = build_chat_model(get_settings().azure_openai_specialist_deployment).with_structured_output(
        GradeResult
    )
    context = "\n\n".join(state["retrieved_chunks"]) or "No results were retrieved."
    result = llm.invoke(
        [
            SystemMessage(content=GRADE_SYSTEM_PROMPT),
            HumanMessage(content=f"Question: {state['original_query']}\n\nRetrieved content:\n{context}"),
        ]
    )
    return {"is_sufficient": result.is_sufficient}


def rewrite_node(state: RagState) -> dict:
    llm = build_chat_model(get_settings().azure_openai_specialist_deployment).with_structured_output(
        RewriteResult
    )
    result = llm.invoke(
        [
            SystemMessage(content=REWRITE_SYSTEM_PROMPT),
            HumanMessage(
                content=f"Original question: {state['original_query']}\nPrevious search query: {state['query']}"
            ),
        ]
    )
    return {"query": result.rewritten_query, "retry_count": state["retry_count"] + 1}


def answer_node(state: RagState) -> dict:
    llm = build_chat_model(get_settings().azure_openai_specialist_deployment)
    context = "\n\n".join(state["retrieved_chunks"]) or "No relevant information was found."
    history = state.get("history") or []
    history_text = _format_history(history) if history else "No earlier messages in this conversation."
    response = llm.invoke(
        [
            SystemMessage(content=ANSWER_SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"Earlier conversation:\n{history_text}\n\n"
                    f"Question: {state['original_query']}\n\n"
                    f"Knowledge base content:\n{context}"
                )
            ),
        ]
    )
    return {"answer": response.content}


def _should_retry(state: RagState) -> str:
    if state["is_sufficient"] or state["retry_count"] >= MAX_RETRIES:
        return "answer"
    return "rewrite"


@lru_cache
def build_rag_graph():
    graph = StateGraph(RagState)
    graph.add_node("contextualize", contextualize_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("grade", grade_node)
    graph.add_node("rewrite", rewrite_node)
    graph.add_node("answer", answer_node)

    graph.set_entry_point("contextualize")
    graph.add_edge("contextualize", "retrieve")
    graph.add_edge("retrieve", "grade")
    graph.add_conditional_edges("grade", _should_retry, {"answer": "answer", "rewrite": "rewrite"})
    graph.add_edge("rewrite", "retrieve")
    graph.add_edge("answer", END)

    return graph.compile()


def answer_question(question: str, history: list[dict] | None = None) -> str:
    result = build_rag_graph().invoke(
        {
            "query": question,
            "original_query": question,
            "retrieved_chunks": [],
            "is_sufficient": False,
            "retry_count": 0,
            "answer": "",
            "history": history or [],
        }
    )
    return result["answer"]
