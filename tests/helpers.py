class StubLLM:
    def __init__(self, result):
        self.result = result
        self.received_messages = None

    def invoke(self, messages):
        self.received_messages = messages
        return self.result
