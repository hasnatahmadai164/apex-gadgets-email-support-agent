from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.llm import build_chat_model
from app.core.schemas import EmailMessage

CONFIRMATION_SYSTEM_PROMPT = (
    "You decide whether a customer's reply confirms a previously proposed action "
    "at Apex Gadgets. Mark it confirmed only if the reply clearly agrees to "
    "proceed as summarized, such as saying yes, confirming, or approving it. "
    "Mark it not confirmed if the reply asks for changes, cancels, or does not "
    "clearly agree."
)


class ConfirmationResult(BaseModel):
    is_confirmed: bool


def classify_confirmation(email: EmailMessage, pending_summary: dict, llm=None) -> ConfirmationResult:
    structured_llm = llm or build_chat_model(
        get_settings().azure_openai_specialist_deployment
    ).with_structured_output(ConfirmationResult)
    summary = ", ".join(f"{key}: {value}" for key, value in pending_summary.items())
    user_content = (
        f"Proposed action: {summary}\n\n"
        f"Customer reply:\nFrom: {email.sender}\nSubject: {email.subject}\n\n{email.body}"
    )
    return structured_llm.invoke(
        [SystemMessage(content=CONFIRMATION_SYSTEM_PROMPT), HumanMessage(content=user_content)]
    )
