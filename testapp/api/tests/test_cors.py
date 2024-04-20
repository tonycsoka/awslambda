import pytest

from trilodocs.api.middleware.cors import get_cors_headers


@pytest.mark.parametrize(
    "headers,expected_origin",
    [
        (
            {"Referer": "https://d391wccgyuzfh3.cloudfront.net/some/path/to/something"},
            "https://d391wccgyuzfh3.cloudfront.net",
        ),
        (
            {"origin": "http://localhost:3001"},
            "http://localhost:3001",
        ),
        (
            {"origin": "https://app.test.trilodocs.com"},
            "https://app.test.trilodocs.com",
        ),
        (
            {"origin": "https://subdomain.app.test.trilodocs.com"},
            "https://subdomain.app.test.trilodocs.com",
        ),
        (
            {"origin": "https://not-allowed.com"},
            "",
        ),
    ],
)
def test_cors_header(headers, expected_origin):
    """
    Given a request with different origin or referer headers,
    When the get_cors_headers function is called,
    Then the allowed origin is verified based on the ALLOWED_ORIGINS list.
    """
    payload = {"headers": headers}
    cors_headers = get_cors_headers(payload)
    assert cors_headers["Access-Control-Allow-Origin"] == expected_origin
