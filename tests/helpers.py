import requests


def assert_status_in(resp: requests.Response, expected: set[int], context: str) -> None:
    assert resp.status_code in expected, (
        f"[{context}] expected status in {sorted(expected)}, got {resp.status_code} "
        f"({resp.request.method} {resp.request.path_url})"
    )
