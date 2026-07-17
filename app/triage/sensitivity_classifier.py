from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.llm import build_chat_model
from app.core.schemas import EmailMessage

SYSTEM_PROMPT = (
    "You decide whether an email already judged relevant to Apex Gadgets needs "
    "review by a human before any automated reply is sent. Mark it sensitive if "
    "it contains a legal threat, mentions a lawyer, threatens a chargeback or "
    "dispute, involves a payment or refund disagreement, expresses strong anger "
    "or demands escalation to a manager, or is written in a way that makes you "
    "genuinely unsure how to safely respond. Mark it not sensitive if it is an "
    "ordinary product question, order request, or support issue a straightforward "
    "automated reply can handle. When genuinely unsure, mark it sensitive, since "
    "an unnecessary human review costs far less than an automated system "
    "mishandling a high-stakes situation."
)


class SensitivityResult(BaseModel):
    is_sensitive: bool = Field(
        description="True if the email needs human review before any reply is sent"
    )


def classify_sensitivity(email: EmailMessage, llm=None) -> SensitivityResult:
    structured_llm = llm or build_chat_model(
        get_settings().azure_openai_sensitivity_deployment
    ).with_structured_output(SensitivityResult)

    user_content = f"From: {email.sender}\nSubject: {email.subject}\n\n{email.body}"
    return structured_llm.invoke(
        [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_content)]
    )
