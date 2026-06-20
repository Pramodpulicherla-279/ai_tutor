"""JWT validation, sharing the signing secret with the Node platform. In dev
(AUTH_OPTIONAL=true) missing/invalid tokens resolve to a throwaway dev user."""
from dataclasses import dataclass, field

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

bearer = HTTPBearer(auto_error=False)


@dataclass
class User:
    id: str
    roles: list[str] = field(default_factory=list)


_DEV_USER = User(id="dev-user", roles=["student"])


async def current_user(
    cred: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> User:
    if cred is None:
        if settings.AUTH_OPTIONAL:
            return _DEV_USER
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing bearer token")
    try:
        payload = jwt.decode(
            cred.credentials,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALG],
            audience=settings.JWT_AUDIENCE,
        )
    except jwt.PyJWTError as exc:
        if settings.AUTH_OPTIONAL:
            return _DEV_USER
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"invalid token: {exc}")
    return User(id=str(payload.get("sub", "unknown")), roles=payload.get("roles", []))
