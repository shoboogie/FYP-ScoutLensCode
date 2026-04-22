"""Authentication endpoints: register and login.

Uses an in-memory user store so auth works without PostgreSQL.
For a production deployment, swap to the database-backed service.
"""

from fastapi import APIRouter, HTTPException, status

from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.services.auth_service import (
    create_access_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# In-memory user store — keyed by email
_users: dict[str, dict] = {}
_next_id = 1


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest):
    global _next_id

    if body.email in _users:
        raise HTTPException(status_code=409, detail="Email already registered")

    user_id = _next_id
    _next_id += 1
    _users[body.email] = {
        "id": user_id,
        "email": body.email,
        "hashed_password": hash_password(body.password),
    }

    token = create_access_token(user_id, body.email)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    user = _users.get(body.email)
    if not user or not verify_password(body.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user["id"], user["email"])
    return TokenResponse(access_token=token)
