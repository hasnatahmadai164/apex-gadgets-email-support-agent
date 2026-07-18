from email.utils import parseaddr


def extract_email_address(raw_sender: str) -> str:
    _, address = parseaddr(raw_sender)
    return address
