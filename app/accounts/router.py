from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.accounts.models import User
from app.accounts.schemas import (
    AccessToken,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    Tokens,
    UserRead,
)
from app.accounts.security import create_token, password_hash, read_token
from app.db import get_db

router = APIRouter(prefix="/accounts", tags=["accounts"])
bearer = HTTPBearer(auto_error=False)
DbSession = Annotated[Session, Depends(get_db)]


def unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    db: DbSession,
) -> User:
    if credentials is None:
        raise unauthorized()
    try:
        user_id = read_token(credentials.credentials, "access")
    except jwt.InvalidTokenError as exc:
        raise unauthorized() from exc
    user = db.get(User, user_id)
    if user is None:
        raise unauthorized()
    return user


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db: DbSession) -> User:
    user = User(
        email=str(data.email).lower(),
        password_hash=password_hash.hash(data.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email já cadastrado") from exc
    db.refresh(user)
    return user


@router.post("/login", response_model=Tokens)
def login(data: LoginRequest, db: DbSession) -> Tokens:
    user = db.scalar(select(User).where(User.email == str(data.email).lower()))
    if user is None or not password_hash.verify(data.password, user.password_hash):
        raise unauthorized()
    return Tokens(
        access_token=create_token(user.id, "access"),
        refresh_token=create_token(user.id, "refresh"),
    )


@router.post("/refresh", response_model=AccessToken)
def refresh(data: RefreshRequest, db: DbSession) -> AccessToken:
    try:
        user_id = read_token(data.refresh_token, "refresh")
    except jwt.InvalidTokenError as exc:
        raise unauthorized() from exc
    if db.get(User, user_id) is None:
        raise unauthorized()
    return AccessToken(access_token=create_token(user_id, "access"))


@router.get("/me", response_model=UserRead)
def me(user: Annotated[User, Depends(get_current_user)]) -> User:
    return user
