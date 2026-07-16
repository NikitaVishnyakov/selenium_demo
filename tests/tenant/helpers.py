def assert_not_leaked(id_: str, ids: set[str], context: str) -> None:
    assert id_ not in ids, f"[{context}] expected id {id_!r} to be excluded from caller's list, but it was present"
