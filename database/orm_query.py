import datetime
from sqlalchemy import and_, func, or_, select, update, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Trip, User

async def orm_add_trip(session: AsyncSession, data: dict):
    obj = Trip(
        userid=data['userid'],
        description=str(data['description']),
        startdate=data['startdate'],
        enddate=data['enddate']
    )

    session.add(obj)
    await session.commit()


async def orm_add_user(session: AsyncSession, data: dict):
    obj = User(
        userid=int(data['userid']),
        language=str(data['language']),
        daysperyearlimit=data['daysperyearlimit'],
        dayspertwoyearslimit=data['dayspertwoyearslimit']
    )

    session.add(obj)
    await session.commit()


async def orm_get_user(session: AsyncSession, userid: int):
    query = select(User).where(User.userid == userid)
    result = await session.execute(query)
    return result.scalar()


async def orm_get_users_count(session: AsyncSession):
    query = select(User)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_trips(session: AsyncSession, userid: int):
    query = select(Trip).where(Trip.userid == userid).order_by(desc(Trip.updated))
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_trips_from_date(session: AsyncSession, userid: int, target_start_date: datetime):
    query = select(Trip).where(Trip.userid == userid).filter(
        or_(
            and_(Trip.startdate >= target_start_date, Trip.startdate <= func.now()),
            and_(Trip.startdate < target_start_date, Trip.enddate >= target_start_date)
        ))
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_trip(session: AsyncSession, trip_id: int):
    query = select(Trip).where(Trip.id == trip_id)
    result = await session.execute(query)
    return result.scalar()


async def orm_update_trip(session: AsyncSession, trip_id: int, data: dict):
    query = update(Trip).where(Trip.id == trip_id).values(
        userid=data['userid'],
        description=str(data['description']),
        startdate=data['startdate'],
        enddate=data['enddate']
        )
    await session.execute(query)
    await session.commit()


async def orm_delete_trip(session: AsyncSession, trip_id: int):
    query = delete(Trip).where(Trip.id == trip_id)
    await session.execute(query)
    await session.commit()
    

async def orm_update_user_settings(session: AsyncSession, userid: int, data: dict):
    query = update(User).where(User.userid == userid).values(
        language=str(data['language']),
        daysperyearlimit=data['daysperyearlimit'],
        dayspertwoyearslimit=data['dayspertwoyearslimit']
    )
    await session.execute(query)
    await session.commit()