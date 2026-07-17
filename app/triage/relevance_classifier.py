from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.llm import build_chat_model
from app.core.schemas import EmailMessage

SYSTEM_PROMPT = (
    "You classify incoming emails for the Apex Gadgets customer support inbox. "
    "Apex Gadgets sells phones and laptops online. An email is relevant if it is "
    "a genuine message from a customer or prospective customer about Apex Gadgets "
    "products, an order, a delivery, a return, a warranty, a technical issue with "
    "a purchased device, or a general question about the store. An email is not "
    "relevant if it is spam, a marketing or vendor pitch, a newsletter, a job "
    "application, an automated notification unrelated to Apex Gadgets, or a "
    "personal message clearly sent to the wrong address. When genuinely unsure, "
    "lean toward marking it relevant, since an irrelevant email is silently "
    "dropped and a missed relevant one is a real customer left unanswered."
)


class RelevanceResult(BaseModel):
    is_relevant: bool = Field(
        description="True if the email concerns Apex Gadgets products, orders, or support"
    )


def classify_relevance(email: EmailMessage, llm=None) -> RelevanceResult:
    structured_llm = llm or build_chat_model(
        get_settings().azure_openai_relevance_deployment
    ).with_structured_output(RelevanceResult)

    user_content = f"From: {email.sender}\nSubject: {email.subject}\n\n{email.body}"
    return structured_llm.invoke(
        [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_content)]
    )
