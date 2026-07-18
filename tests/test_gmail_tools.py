from app.tools.gmail_tools import _extract_body, _extract_header


def test_extract_body_finds_text_plain_in_nested_multipart():
    payload = {
        "mimeType": "multipart/mixed",
        "parts": [
            {
                "mimeType": "multipart/alternative",
                "parts": [
                    {"mimeType": "text/plain", "body": {"data": "SGVsbG8gd29ybGQ"}},
                    {"mimeType": "text/html", "body": {"data": "not-decoded"}},
                ],
            }
        ],
    }

    assert _extract_body(payload) == "Hello world"


def test_extract_header_is_case_insensitive():
    headers = [{"name": "Subject", "value": "Order status"}]

    assert _extract_header(headers, "subject") == "Order status"
