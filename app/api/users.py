from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_session
from app.models import User
from app.schemas import UserCreate, UserRead, UserWithJobs

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate, session: AsyncSession = Depends(get_session)):
    user = User(email=user_data.email)
    session.add(user)
    try:
        await session.commit()
    except IntegrityError as err:
        # унікальність email гарантує БД (UNIQUE), а не попередній SELECT —
        # так немає гонки між двома одночасними запитами
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        ) from err
    await session.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserRead, status_code=status.HTTP_200_OK)
async def get_user(user_id: int, session: AsyncSession = Depends(get_session)):
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.get("", response_model=list[UserWithJobs], status_code=status.HTTP_200_OK)
async def list_users(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    query = (
        select(User)
        .options(selectinload(User.jobs))
        .order_by(User.id)
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(query)
    return result.scalars().all()