revoked_tokens: set[str] = set()


def revoke_token(token: str) -> None:
    revoked_tokens.add(token)


def is_token_revoked(token: str) -> bool:
    return token in revoked_tokens