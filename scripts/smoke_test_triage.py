from app.core.schemas import EmailMessage
from app.triage.relevance_classifier import classify_relevance
from app.triage.sensitivity_classifier import classify_sensitivity

SAMPLE_EMAILS = [
    EmailMessage(
        sender="jane@example.com",
        subject="Laptop won't turn on",
        body="I bought the Apex Pro 14 last week and it won't power on anymore. Can you help?",
    ),
    EmailMessage(
        sender="offers@some-marketing-list.com",
        subject="50% off web hosting this week only",
        body="Upgrade your hosting plan today and save big.",
    ),
    EmailMessage(
        sender="angry.customer@example.com",
        subject="This is unacceptable",
        body=(
            "My order never arrived and now I'm out $1200. I've contacted my "
            "lawyer and I'm disputing the charge with my bank."
        ),
    ),
]


def main():
    for email in SAMPLE_EMAILS:
        relevance = classify_relevance(email)
        print(email.subject, "-> relevant:", relevance.is_relevant)
        if relevance.is_relevant:
            sensitivity = classify_sensitivity(email)
            print(email.subject, "-> sensitive:", sensitivity.is_sensitive)


if __name__ == "__main__":
    main()
