from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_async_db
from app.middleware.origin import origin_guard
from app.modules.user.models import User
from app.modules.user.schemas import (
    EmptySuccessResponse,
    Login,
    Registration,
    RoleType,
    UserListSuccessResponse,
    UserSuccessResponse,
)
from app.modules.user.service import UserService
from app.security.cookies import CookieManager
from app.security.dependencies import RequireRoles, current_user
from app.security.rate_limit import limiter
from app.utils.constant import ApiMessages, ApiPaths, AuthenticationPolicy, AuthValues

router = APIRouter()
Db = Annotated[AsyncSession, Depends(get_async_db, scope="function")]


@router.post(
    ApiPaths.REGISTER_PATH,
    response_model=UserSuccessResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(origin_guard)],
)
async def register(data: Registration, db: Db):
    """Register a user and return the public profile."""
    user = await UserService(db).register(data)
    return {"success": True, "message": ApiMessages.REGISTER_SUCCESS_MESSAGE, "data": user}


@router.post(ApiPaths.LOGIN_PATH, response_model=UserSuccessResponse, dependencies=[Depends(origin_guard)])
@limiter.limit(AuthenticationPolicy.LOGIN_RATE_LIMIT)
async def login(request: Request, data: Login, response: Response, db: Db):
    """Sign in and set authentication cookies."""
    user, tokens = await UserService(db).login(str(data.email), data.password)
    CookieManager.set_tokens(response, tokens)
    return {"success": True, "message": ApiMessages.LOGIN_SUCCESS_MESSAGE, "data": user}


@router.post(ApiPaths.REFRESH_PATH, response_model=EmptySuccessResponse, dependencies=[Depends(origin_guard)])
async def refresh(request: Request, response: Response, db: Db):
    """Rotate the refresh token and update authentication cookies."""
    tokens = await UserService(db).rotate(request.cookies.get(AuthValues.REFRESH_COOKIE))
    CookieManager.set_tokens(response, tokens)
    return {"success": True, "message": ApiMessages.REFRESH_SUCCESS_MESSAGE}


@router.post(ApiPaths.LOGOUT_PATH, response_model=EmptySuccessResponse, dependencies=[Depends(origin_guard)])
async def logout(request: Request, response: Response, db: Db):
    """Revoke the refresh token and clear cookies."""
    await UserService(db).revoke(request.cookies.get(AuthValues.REFRESH_COOKIE))
    CookieManager.clear(response)
    return {"success": True, "message": ApiMessages.LOGOUT_SUCCESS_MESSAGE}


@router.get(ApiPaths.PROFILE_PATH, response_model=UserSuccessResponse)
async def me(user: Annotated[User, Depends(current_user)]):
    """Return the authenticated user profile."""
    return {"success": True, "message": ApiMessages.PROFILE_SUCCESS_MESSAGE, "data": user}


@router.get(ApiPaths.USERS_PATH, response_model=UserListSuccessResponse)
async def users(db: Db, admin: Annotated[User, Depends(RequireRoles(RoleType.Admin))]):
    """Return the user list to an administrator."""
    del admin
    return {"success": True, "message": ApiMessages.USERS_SUCCESS_MESSAGE, "data": await UserService(db).list_users()}
