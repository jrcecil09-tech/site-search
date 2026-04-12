"""Authentication router — login, token refresh, registration."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

router = APIRouter()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: str


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    # TODO: validate credentials against DB, return JWT
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest):
    # TODO: create user, hash password, send verification email
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str):
    # TODO: validate refresh token, issue new access token
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.post("/logout")
async def logout():
    # TODO: invalidate refresh token
    return {"message": "Logged out"}
