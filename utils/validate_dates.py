import datetime
from datetime import datetime


def is_valid_date_format(date_string: str, format='%d-%m-%y') -> bool:
    try:
        datetime.strptime(date_string, format)
        return True
    except ValueError:
        return False


def is_date_after(start_date: datetime, end_date: datetime) -> bool:
    return end_date > start_date
    