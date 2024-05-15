import csv
import os
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import orm_get_trips

temp_dir = os.getenv('TEMP_DIR', '/var/lib/telegram-bot')
filename = "exported_trips.csv"

async def export_trips_to_csv(session: AsyncSession, userid: int) -> str:
    trips = await orm_get_trips(session, userid)
    
    output_item = os.path.join(temp_dir, filename)
    
    with open(output_item, 'w', newline='') as csvfile:
        
        fieldnames = ['id', 'description', 'start_date', 'end_date']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        
        for trip in trips:
            writer.writerow({
                'id': trip.id,
                'description': trip.description,
                'start_date': trip.startdate, 
                'end_date': trip.enddate
            })
    
    csvfile.close()    
        
    return output_item