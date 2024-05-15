import datetime
from datetime import datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import orm_get_trips, orm_get_trips_from_date, orm_get_user

async def calculate_number_of_days(session: AsyncSession, userid: int) -> int:
    try:
        user_trips = await orm_get_trips(session=session, userid=userid)
    except Exception as e:
        return -1
    
    if len(user_trips) > 0:
        days_abroad = 0
        for trip in user_trips:
            delta = trip.enddate - trip.startdate
            days_abroad += int(delta.days)
        print(days_abroad)
        return days_abroad
    else:
        return 0
    
    
async def calculate_remaining_days(session: AsyncSession, userid: int) -> dict:
    remaining_days_one_year = 0
    remaining_days_two_years = 0
    response = {}
    current_date = datetime.now()
    date_one_year_ago = current_date - relativedelta(years=1)
    date_two_years_ago = current_date - relativedelta(years=2)
    
    try:
        user_trips_one_year = await orm_get_trips_from_date(session=session, userid=userid, target_start_date=date_one_year_ago)
        user_trips_two_years = await orm_get_trips_from_date(session=session, userid=userid, target_start_date=date_two_years_ago)
        user = await orm_get_user(session=session, userid=userid)
    except Exception as e:
        return -1
    
    if (len(user_trips_one_year) or len(user_trips_two_years) > 0) and user:
        total_days_per_year = 0
        total_days_per_two_years = 0
        
        daysperyearlimit = user.daysperyearlimit
        dayspertwoyearslimit = user.dayspertwoyearslimit

        if daysperyearlimit > 0:
            for trip in user_trips_one_year:
                if trip.startdate >= date_one_year_ago:
                    total_days_per_year += (trip.enddate - trip.startdate).days
                else:
                    total_days_per_year += (trip.enddate - date_one_year_ago).days + 1
            remaining_days_one_year = daysperyearlimit - total_days_per_year
        
        if dayspertwoyearslimit > 0:
            for trip in user_trips_two_years:
                if trip.startdate >= date_two_years_ago:
                    total_days_per_two_years += (trip.enddate - trip.startdate).days
                else:
                    total_days_per_two_years += (trip.enddate - date_two_years_ago).days + 1
            remaining_days_two_years = dayspertwoyearslimit - total_days_per_two_years
        
        response = {
            "remaining_days_one_year": remaining_days_one_year,
            "remaining_days_two_years": remaining_days_two_years,
            "daysperyearlimit": daysperyearlimit,
            "dayspertwoyearslimit": dayspertwoyearslimit
            }
        
        return response
    else:
        return 0
