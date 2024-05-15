from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import types

from database.orm_query import orm_get_trips

async def trips_to_buttons(callback: types.CallbackQuery, session: AsyncSession, operation: str):
    trips = await orm_get_trips(session, callback.from_user.id)
    trips_buttons = {}
    if len(trips) > 0:
        for trip in trips:
            trips_buttons.update({(str(trip.description) + ": " + trip.startdate.strftime("%d-%m-%y") + " - " + trip.enddate.strftime("%d-%m-%y")):operation + "_" + str(trip.id)})
        return trips_buttons
    else:
        return 0