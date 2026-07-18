from app.agents.rag_agent import answer_question

SAMPLE_QUESTIONS = [
    "What is your return policy?",
    "Does the Apex Pro 14 support fast charging?",
    "Do you offer international shipping?",
]


def main():
    for question in SAMPLE_QUESTIONS:
        print("Q:", question)
        print("A:", answer_question(question))
        print()


if __name__ == "__main__":
    main()
