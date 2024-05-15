from aiogram.fsm.state import State, StatesGroup

class AddChangeUserConfig(StatesGroup):
    add_one_year_limit = State()
    add_two_year_limit = State()
    select_language = State()
    
    user_to_change = None


class AddChangeTrip(StatesGroup):
    select_trip = State()
    add_start_date = State()
    add_end_date = State()
    add_description = State()
    
    trip_to_change = None

    texts = {
        "AddChangeTrip:select_trip": "Select the trip you want to change",
        "AddChangeTrip:add_start_date": "Enter start date",
        "AddChangeTrip:add_end_date": "Enter end date",
        "AddChangeTrip:add_description": "Enter description",
    }


class DeleteTrip(StatesGroup):
    select_trip = State()

    texts = {
        "DeleteTrip:select_trip": "Select the trip you want to remove",
    }


class AdminFeatures(StatesGroup):
    selectOption = State()

    texts = {"AdminFeatures:selectOption": "Select desired option"}
    
