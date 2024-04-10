from trilodocs.api.middleware.cors import get_cors_headers


def test_cors_header_defaults_to_referer():
    """Given a request that is not considered a cross-origin request by Cloudfront,
    When the request does not contain an 'origin' header,
    Then the allowed origin is verified by using the value in the 'Referer' header."""
    payload = {
        "headers": {
            "Referer": "https://d391wccgyuzfh3.cloudfront.net/some/path/to/something"
        }
    }
    cors_headers = get_cors_headers(payload)
    assert (
        cors_headers["Access-Control-Allow-Origin"]
        == "https://d391wccgyuzfh3.cloudfront.net"
    )
