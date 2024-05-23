import os
from aiogram import F, types, Router, methods
from aiogram.filters import CommandStart, Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram_i18n import I18nContext, LazyProxy
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from aiogram_calendar import SimpleCalendarCallback
from aiogram.filters.callback_data import CallbackData

from common.bot_commands import MENU_ITEMS, INITIAL_MENU_ITEMS
from keyboards.inline_calendar import MySimpleCalendar
from database.orm_query import orm_add_trip, orm_add_user, orm_delete_trip, orm_get_trip, orm_get_trips, orm_get_user, orm_update_trip, orm_update_user_settings
from filters.chat_types import ChatTypeFilter
from keyboards.inline_keyboard import build_dynamic_inline_keyboard, build_inline_callback_keyboard
from states.user_states import AddChangeTrip, AddChangeUserConfig, DeleteTrip
from utils.dates_calculations import calculate_number_of_days, calculate_remaining_days
from utils.trips_to_buttons import trips_to_buttons
from utils.trips_to_csv import export_trips_to_csv
from utils.validate_dates import is_valid_date_format, is_date_after

INITIAL_KEYBOARD = build_inline_callback_keyboard(
    buttons={
        LazyProxy("Add a trip"): f"add"
    }
)

MENU_KEYBOARD = build_inline_callback_keyboard(
    buttons={
        LazyProxy("Show me my days abroad"): f"count",
        LazyProxy("Add a trip"): f"add",
        LazyProxy("Change a trip"): f"trip_change",
        LazyProxy("Remove a trip"): f"trip_delete",
        LazyProxy("Export my trips"):f"export",
        LazyProxy("My settings"): f"my_settings"
    }
)

MENU_LANGUAGE = build_inline_callback_keyboard(
    buttons={
        "English": f"lang_en",
        "Русский": f"lang_ru"
    }
)

WARNING_SIGN = "⚠️ "
ALL_GOOD_SIGN = "✅ "
QUESTION_MARK  = "❔"
EXCLAMATION_MARK = "‼️"
ENTER_DATA = "✏️"

user_handlers_router = Router()
user_handlers_router.message.filter(ChatTypeFilter(["private"]))


#Handler for Start button
@user_handlers_router.message(or_f(Command("start"), (F.text.lower() == "start")))
@user_handlers_router.message(CommandStart())
async def start_cmd(message: types.Message, state: FSMContext, session: AsyncSession, i18n: I18nContext) -> None:
    try:
        user_in_db = await orm_get_user(session, message.from_user.id)
    except Exception as e:
        user_in_db = ""

    await message.bot.delete_my_commands(scope=types.BotCommandScopeChat(chat_id=message.chat.id))
    await message.bot.set_my_commands(commands=INITIAL_MENU_ITEMS, scope=types.BotCommandScopeChat(chat_id=message.chat.id))
    
    if user_in_db:
        await i18n.set_locale(user_in_db.language)
        await message.bot.set_my_commands(commands=MENU_ITEMS, scope=types.BotCommandScopeChat(chat_id=message.chat.id))
        msg = await message.answer(i18n.get("I am your days abroad counter bot"), reply_markup=MENU_KEYBOARD)
        await state.update_data(previous_message_id=msg.message_id)
    else:
        await message.bot.delete_my_commands(scope=types.BotCommandScopeChat(chat_id=message.chat.id))
        await message.bot.set_my_commands(commands=INITIAL_MENU_ITEMS, scope=types.BotCommandScopeChat(chat_id=message.chat.id))
        await state.set_state(AddChangeUserConfig.add_one_year_limit)
        await message.answer(i18n.get("I am your days abroad counter bot"))
        await message.answer(ENTER_DATA + i18n.get("Enter your annual days abroad limit. If you want to add a limit for two years, send 0"))


async def switch_language(message: types.Message, state: FSMContext, i18n: I18nContext, session: AsyncSession, locale_code: str, update_db: bool) -> None:
    await i18n.set_locale(locale_code)
    
    if update_db:
        try:
            user_in_db = await orm_get_user(session, message.from_user.id)
            
            obj = {
                "userid": user_in_db.userid,
                "language":locale_code,
                "daysperyearlimit":user_in_db.daysperyearlimit,
                "dayspertwoyearslimit":user_in_db.dayspertwoyearslimit
            }
            
            await orm_update_user_settings(session=session, userid=user_in_db.userid, data=obj)
                
        except Exception as e:
            await message.answer(EXCLAMATION_MARK + i18n.get("Sorry, I'm on maintenance. Please try again later"))

        data = await state.get_data()
        previous_message_id = data.get('previous_message_id')

        if previous_message_id:
            try:
                await message.bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=previous_message_id, reply_markup=None)
            except Exception as e:
                print(f"Failed to delete reply markup: {e}")
        
        current_state = await state.get_state()
        if current_state is None:
            await state.clear()
        if AddChangeUserConfig.user_to_change:
            AddChangeUserConfig.user_to_change = None
            
        if AddChangeTrip.trip_to_change:
            AddChangeTrip.trip_to_change = None
        
        if locale_code == "en":
            msg = await message.answer("Language switched to: " + locale_code, reply_markup=MENU_KEYBOARD)
        else:
            msg = await message.answer("Язык переключен на : " + locale_code, reply_markup=MENU_KEYBOARD)
        
        await state.update_data(previous_message_id=msg.message_id)


@user_handlers_router.message(Command("en"))
async def switch_to_en(message: types.Message, state: FSMContext, session: AsyncSession, i18n: I18nContext) -> None:
    await switch_language(message, state, i18n, session, "en", True)


@user_handlers_router.message(Command("ru"))
async def switch_to_en(message: types.Message, state: FSMContext, session: AsyncSession, i18n: I18nContext) -> None:
    await switch_language(message, state, i18n, session, "ru", True)


#Handler for Count days
@user_handlers_router.callback_query(StateFilter(None), F.data.startswith("count"))
async def count_days_callback(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession, i18n: I18nContext) -> None:
    await callback.message.delete_reply_markup()
    
    days_abroad = await calculate_number_of_days(session=session, userid=callback.from_user.id)
    total_days = await calculate_remaining_days(session=session, userid=callback.from_user.id)
    
    #This is totally weird
    if days_abroad != -1 and not total_days["error"]:
        if total_days == 0 or days_abroad == 0:
            await callback.message.answer(QUESTION_MARK + (i18n.get("Number of days abroad: 0. Did you forget to add trips?")))
            msg = await callback.message.answer((i18n.get("Here is the menu")), reply_markup=MENU_KEYBOARD)
        elif (total_days["daysperyearlimit"] == 0) and (total_days["dayspertwoyearslimit"] == 0):
            await callback.message.answer(QUESTION_MARK + (i18n.get('Total number of days abroad: {daysabroad}. Did you forget to set limits in settings?', daysabroad=days_abroad)))
            msg = await callback.message.answer((i18n.get("Here is the menu")), reply_markup=MENU_KEYBOARD)
        elif (total_days["remaining_days_one_year"] > 0) and (total_days["daysperyearlimit"] > 0) and (total_days["dayspertwoyearslimit"] == 0):
            await callback.message.answer((i18n.get("Total number of days abroad: {daysabroad}", daysabroad=days_abroad)))
            await callback.message.answer(ALL_GOOD_SIGN + (i18n.get("The number of remaining days abroad during the year is {remaining_days} out of {days_limit}", remaining_days=total_days["remaining_days_one_year"], days_limit=total_days["daysperyearlimit"])))
            msg = await callback.message.answer((i18n.get("Here is the menu")), reply_markup=MENU_KEYBOARD)
        elif (total_days["remaining_days_one_year"] < 0) and (total_days["daysperyearlimit"] > 0) and (total_days["dayspertwoyearslimit"] == 0):
            await callback.message.answer((i18n.get("Total number of days abroad: {daysabroad}", daysabroad=days_abroad)))
            await callback.message.answer(WARNING_SIGN + (i18n.get("Over the past year, you have exceeded your days abroad limit by {remaining_days} of your {days_limit}  limit", remaining_days=abs(total_days["remaining_days_one_year"]), days_limit=total_days["daysperyearlimit"])))
            msg = await callback.message.answer((i18n.get("Here is the menu")), reply_markup=MENU_KEYBOARD)
        elif(total_days["remaining_days_two_years"] > 0) and (total_days["dayspertwoyearslimit"] > 0) and (total_days["daysperyearlimit"] == 0):
            await callback.message.answer((i18n.get("Total number of days abroad: {daysabroad}", daysabroad=days_abroad)))
            await callback.message.answer(ALL_GOOD_SIGN + (i18n.get("The number of remaining days abroad during the last two years is {remaining_days} out of {days_limit}", remaining_days=total_days["remaining_days_two_years"], days_limit=total_days["dayspertwoyearslimit"])))
            msg = await callback.message.answer((i18n.get("Here is the menu")), reply_markup=MENU_KEYBOARD)
        elif (total_days["remaining_days_two_years"] < 0) and (total_days["dayspertwoyearslimit"] > 0) and (total_days["daysperyearlimit"] == 0):
            await callback.message.answer((i18n.get("Total number of days abroad: {daysabroad}", daysabroad=days_abroad)))
            await callback.message.answer(WARNING_SIGN + (i18n.get("Over the past two years, you have exceeded your days abroad limit by {remaining_days} of your {days_limit}  limit", remaining_days=abs(total_days["remaining_days_two_years"]), days_limit=total_days["dayspertwoyearslimit"])))
            msg = await callback.message.answer((i18n.get("Here is the menu")), reply_markup=MENU_KEYBOARD)
        elif (total_days["remaining_days_one_year"] > 0) and (total_days["daysperyearlimit"] > 0) and (total_days["remaining_days_two_years"] > 0) and (total_days["dayspertwoyearslimit"] > 0):
            await callback.message.answer((i18n.get("Total number of days abroad: {daysabroad}", daysabroad=days_abroad)))
            await callback.message.answer(ALL_GOOD_SIGN + (i18n.get("The number of remaining days abroad during the year is {remaining_days} out of {days_limit}", remaining_days=total_days["remaining_days_one_year"], days_limit=total_days["daysperyearlimit"])))
            await callback.message.answer(ALL_GOOD_SIGN + (i18n.get("The number of remaining days abroad during the last two years is {remaining_days} out of {days_limit}", remaining_days=total_days["remaining_days_two_years"], days_limit=total_days["dayspertwoyearslimit"])))
            msg = await callback.message.answer((i18n.get("Here is the menu")), reply_markup=MENU_KEYBOARD)
        elif (total_days["remaining_days_one_year"] < 0) and (total_days["daysperyearlimit"] > 0) and (total_days["remaining_days_two_years"] > 0) and (total_days["dayspertwoyearslimit"] > 0):
            await callback.message.answer((i18n.get("Total number of days abroad: {daysabroad}", daysabroad=days_abroad)))
            await callback.message.answer(WARNING_SIGN + (i18n.get("Over the past year, you have exceeded your days abroad limit by {remaining_days} of your {days_limit}  limit", remaining_days=abs(total_days["remaining_days_one_year"]), days_limit=total_days["daysperyearlimit"])))
            await callback.message.answer(ALL_GOOD_SIGN + (i18n.get("The number of remaining days abroad during the last two years is {remaining_days} out of {days_limit}", remaining_days=total_days["remaining_days_two_years"], days_limit=total_days["dayspertwoyearslimit"])))
            msg = await callback.message.answer((i18n.get("Here is the menu")), reply_markup=MENU_KEYBOARD)
        elif (total_days["remaining_days_one_year"] > 0) and (total_days["daysperyearlimit"] > 0) and (total_days["remaining_days_two_years"] < 0) and (total_days["dayspertwoyearslimit"] > 0):
            await callback.message.answer((i18n.get("Total number of days abroad: {daysabroad}", daysabroad=days_abroad)))
            await callback.message.answer(ALL_GOOD_SIGN + (i18n.get("The number of remaining days abroad during the year is {remaining_days} out of {days_limit}", remaining_days=total_days["remaining_days_one_year"], days_limit=total_days["daysperyearlimit"])))
            await callback.message.answer(WARNING_SIGN + (i18n.get("Over the past two years, you have exceeded your days abroad limit by {remaining_days} of your {days_limit}  limit", remaining_days=abs(total_days["remaining_days_two_years"]), days_limit=total_days["dayspertwoyearslimit"])))
            msg = await callback.message.answer((i18n.get("Here is the menu")), reply_markup=MENU_KEYBOARD)
        elif (total_days["remaining_days_one_year"] < 0) and (total_days["daysperyearlimit"] > 0) and (total_days["remaining_days_two_years"] < 0) and (total_days["dayspertwoyearslimit"] > 0):
            await callback.message.answer((i18n.get("Total number of days abroad: {daysabroad}", daysabroad=days_abroad)))
            await callback.message.answer(WARNING_SIGN + (i18n.get("Over the past year, you have exceeded your days abroad limit by {remaining_days} of your {days_limit}  limit", remaining_days=abs(total_days["remaining_days_one_year"]), days_limit=total_days["daysperyearlimit"])))
            await callback.message.answer(WARNING_SIGN + (i18n.get("Over the past two years, you have exceeded your days abroad limit by {remaining_days} of your {days_limit}  limit", remaining_days=abs(total_days["remaining_days_two_years"]), days_limit=total_days["dayspertwoyearslimit"])))
            msg = await callback.message.answer((i18n.get("Here is the menu")), reply_markup=MENU_KEYBOARD)
    else:
        await callback.message.answer(EXCLAMATION_MARK + (i18n.get("Sorry, I'm on maintenance. Please try again later")))
    
    await state.update_data(previous_message_id=msg.message_id)


#Handler for Trip - Add
@user_handlers_router.callback_query(StateFilter(None), F.data.contains("add"))
async def add_trip_callback(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession, i18n: I18nContext) -> None:
    await callback.message.delete_reply_markup()
    await state.update_data(userid=callback.from_user.id)
    await callback.answer(i18n.get("Add start date"))
    msg = await callback.message.answer(i18n.get("Add start date"), reply_markup=await MySimpleCalendar(i18n=i18n, show_alerts=False).start_calendar())
    await state.update_data(previous_message_id=msg.message_id)
    
    await state.set_state(AddChangeTrip.add_start_date)


#Handler for Trip - Change
@user_handlers_router.callback_query(StateFilter(None), F.data.startswith("trip_change"))
async def change_trip_callback(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession, i18n: I18nContext) -> None:
    await callback.message.delete_reply_markup()
    
    trip_buttons = await trips_to_buttons(callback, session, "change")
    
    #A crappy workaround to get the "change" operator to work
    AddChangeTrip.trip_to_change = 1
    
    if trip_buttons != 0:
        trips_to_change = build_dynamic_inline_keyboard(trip_buttons=trip_buttons, current_page=1, items_per_page=5)
        await state.update_data(trip_buttons=trip_buttons)
        await state.update_data(current_page=1)
        msg = await callback.message.answer(i18n.get("Select a trip"), reply_markup=trips_to_change)
        await state.update_data(previous_message_id=msg.message_id)
    else:
        await callback.message.answer(ALL_GOOD_SIGN + (i18n.get("There are no trips to edit")), reply_markup=MENU_KEYBOARD)
        AddChangeTrip.trip_to_change = None
        return

    await state.set_state(AddChangeTrip.select_trip)


#Handler for Trip - Delete
@user_handlers_router.callback_query(StateFilter(None), F.data.startswith("trip_delete"))
async def delete_trip_callback(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession, i18n: I18nContext) -> None:
    await callback.message.delete_reply_markup()
    
    trip_buttons = await trips_to_buttons(callback, session, "delete")
    
    if trip_buttons != 0:
        trips_to_change = build_dynamic_inline_keyboard(trip_buttons=trip_buttons, current_page=1, items_per_page=5)
        await state.update_data(trip_buttons=trip_buttons)
        await state.update_data(current_page=1)
        msg = await callback.message.answer(i18n.get("Select a trip"), reply_markup=trips_to_change)
        await state.update_data(previous_message_id=msg.message_id)
    else:
        await callback.message.answer(ALL_GOOD_SIGN + (i18n.get("There are no trips to remove")), reply_markup=MENU_KEYBOARD)
        return

    await state.set_state(DeleteTrip.select_trip)


#Handler for Trip Change - Trips list forward/backward
@user_handlers_router.callback_query(or_f(StateFilter(AddChangeTrip.select_trip), StateFilter(DeleteTrip.select_trip)),
or_f(F.data.contains("prev_page"), F.data.contains("next_page")))
async def handle_pagination(callback: types.CallbackQuery, state: FSMContext, i18n: I18nContext) -> None:
    await callback.message.delete_reply_markup()
    
    data = callback.data
    
    state_data = await state.get_data()
    if state_data:
        items = state_data["trip_buttons"]
        current_page = state_data["current_page"]
        if current_page == None:
            current_page = 1
    
    if data == "next_page":
        current_page += 1
    elif data == "prev_page":
        current_page = max(1, current_page - 1)
    
    items_per_page = 5
    
    keyboard = build_dynamic_inline_keyboard(items, current_page, items_per_page)
    try:
        await callback.message.edit_reply_markup(reply_markup=keyboard)
    except build_dynamic_inline_keyboard:
        pass
    
    await state.update_data(current_page=current_page)


#Handler for Export trips
@user_handlers_router.callback_query(StateFilter(None), F.data.startswith("export"))
async def export_trips_callback(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession, i18n: I18nContext) -> None:
    await callback.message.delete_reply_markup()
    
    try:
        exported_trips = await export_trips_to_csv(session=session, userid=callback.from_user.id)
    except Exception as e:
        await callback.message.answer(EXCLAMATION_MARK + (i18n.get("Something went wrong. Please start over")), reply_markup=MENU_KEYBOARD)
        return
    
    if os.path.exists(exported_trips):
        await callback.message.reply_document(types.FSInputFile(exported_trips))
        await callback.message.answer(i18n.get("Here is the file with your trips"), reply_markup=MENU_KEYBOARD)
    else:
        await callback.message.answer(EXCLAMATION_MARK + (i18n.get("Something went wrong. Please try again")), reply_markup=MENU_KEYBOARD)


#Handler for Change my settings
@user_handlers_router.callback_query(StateFilter(None), F.data.startswith("my_settings"))
async def change_my_settings_callback(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession, i18n: I18nContext) -> None:
    await callback.message.delete_reply_markup()
    
    try:
        user_settings = await orm_get_user(session=session, userid=callback.from_user.id)
    except Exception as e:
        await callback.message.answer(EXCLAMATION_MARK + (i18n.get("Something went wrong. Please start over")), reply_markup=MENU_KEYBOARD)
        return

    AddChangeUserConfig.user_to_change = 1
    
    await state.update_data(user_settings=user_settings)
    AddChangeUserConfig.user_to_change = user_settings
    
    await state.set_state(AddChangeUserConfig.add_one_year_limit)
    await callback.message.answer(i18n.get("Add a new day limit for one year or send '.' to keep the old value"))


#Handler for Cancel
@user_handlers_router.message(StateFilter("*"), Command("cancel"))
@user_handlers_router.message(StateFilter("*"), F.text.casefold() == "cancel")
async def cancel_handler(message: types.Message, state: FSMContext, i18n: I18nContext) -> None:
    
    data = await state.get_data()
    previous_message_id = data.get('previous_message_id')

    if previous_message_id:
        try:
            await message.bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=previous_message_id, reply_markup=None)
        except Exception as e:
            print(f"Failed to delete reply markup: {e}")
    
    current_state = await state.get_state()
    if current_state is None:
        return
    if AddChangeUserConfig.user_to_change:
        AddChangeUserConfig.user_to_change = None
        
    if AddChangeTrip.trip_to_change:
        AddChangeTrip.trip_to_change = None
        
    await state.clear()
    
    await message.answer(i18n.get("Your actions were cancelled. Let's start it over"), reply_markup=MENU_KEYBOARD)


#Handler for Add / Change user - add add_one_year_limit
@user_handlers_router.message(AddChangeUserConfig.add_one_year_limit, or_f(F.text, F.text == "."))
async def add_user_config_one_year_limit(message: types.Message, state: FSMContext, session: AsyncSession, i18n: I18nContext) -> None:
    if message.text == "." and AddChangeUserConfig.user_to_change:
        await state.update_data(daysperyearlimit=AddChangeUserConfig.user_to_change.daysperyearlimit)
        await state.set_state(AddChangeUserConfig.add_two_year_limit)
        await message.answer(ENTER_DATA + i18n.get("Enter a limit on days abroad for two years"))
    elif message.text.isdigit() and int(message.text) < 365:
        await state.set_state(AddChangeUserConfig.add_two_year_limit)
        await state.update_data(daysperyearlimit=int(message.text))
        await message.answer(ENTER_DATA + i18n.get("Enter a limit on days abroad for two years"))
    else:
        await message.answer(WARNING_SIGN + (i18n.get("Please enter valid number of days. If you want to only use a limit for two years, send 0")))
        return
    

#Handler for Add / Change user - add add_two_years_limit
@user_handlers_router.message(AddChangeUserConfig.add_two_year_limit, or_f(F.text, F.text == "."))
async def add_user_config_two_years_limit(message: types.Message, state: FSMContext, session: AsyncSession, i18n: I18nContext) -> None:
    if message.text == "." and AddChangeUserConfig.user_to_change:
        await state.update_data(dayspertwoyearslimit=AddChangeUserConfig.user_to_change.dayspertwoyearslimit)
    elif message.text.isdigit() and int(message.text) < 730:
        await state.update_data(dayspertwoyearslimit=int(message.text))
    else:
        await message.answer(WARNING_SIGN + (i18n.get("Please enter valid number of days")))
        return
    
    await state.set_state(AddChangeUserConfig.select_language)
    await message.answer(i18n.get("Select your default interface language"), reply_markup=MENU_LANGUAGE)


#Handler for My Settings - language - callback
@user_handlers_router.callback_query(AddChangeUserConfig.select_language, F.data.startswith("lang_"))
async def select_language_en_callback(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession, i18n: I18nContext) -> None:
    await callback.message.delete_reply_markup()
    
    language = callback.data.split("_")[-1]
    
    data = await state.get_data()

    await callback.message.bot.set_my_commands(commands=MENU_ITEMS, scope=types.BotCommandScopeChat(chat_id=callback.message.chat.id))
    
    if AddChangeUserConfig.user_to_change:
        obj = {
        "language":language,
        "daysperyearlimit":data['daysperyearlimit'],
        "dayspertwoyearslimit":data['dayspertwoyearslimit']
        }
        
        try:
            await orm_update_user_settings(session, callback.from_user.id, obj)
        except Exception as e:
            await callback.message.answer(EXCLAMATION_MARK + (i18n.get("Sorry, I'm on maintenance. Please try again later")))
            return
        
        await switch_language(callback.message, state, i18n, session, language, False)
        await callback.message.answer(ALL_GOOD_SIGN + (i18n.get("Your settings have been updated")), reply_markup=MENU_KEYBOARD)
    else:
        obj = {
        "userid": callback.from_user.id,
        "language":language,
        "daysperyearlimit":data['daysperyearlimit'],
        "dayspertwoyearslimit":data['dayspertwoyearslimit']
        }
        
        try:
            await orm_add_user(session, obj)
        except Exception as e:
            await callback.message.answer(EXCLAMATION_MARK + (i18n.get("Sorry, I'm on maintenance. Please try again later")))
            return
        
        await switch_language(callback.message, state, i18n, session, language, False)
        await callback.message.answer(i18n.get("Let's add a record of your first trip"), reply_markup=INITIAL_KEYBOARD)
        
    await state.clear()


#Handler for Trip - Change (change_)
@user_handlers_router.callback_query(AddChangeTrip.select_trip, F.data.startswith("change_"))
async def change_product_callback(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession, i18n: I18nContext) -> None:
    await callback.message.delete_reply_markup()
    
    trip_id = callback.data.split("_")[-1]
    await state.update_data(trip_id=trip_id)
    try:
        trip_to_change_details = await orm_get_trip(session, int(trip_id))
    except Exception as e:
        await callback.message.answer(EXCLAMATION_MARK + (i18n.get("Something went wrong. Please start over")), reply_markup=MENU_KEYBOARD)
        await state.clear()
        return
    
    await state.update_data(trip_to_change_details=trip_to_change_details)
    startdate = trip_to_change_details.startdate
    
    AddChangeTrip.trip_to_change = trip_to_change_details
    
    await callback.answer(i18n.get("Add new start date"))
    msg = await callback.message.answer(i18n.get("Add new start date"), reply_markup=await MySimpleCalendar(i18n=i18n, show_alerts=False).start_calendar(int(startdate.year), int(startdate.month)))
    await state.update_data(previous_message_id=msg.message_id)
    await state.set_state(AddChangeTrip.add_start_date)


#Handler for Trip - Delete (delete_)
@user_handlers_router.callback_query(DeleteTrip.select_trip, F.data.startswith("delete_"))
async def delete_product_callback(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession, i18n: I18nContext) -> None:
    await callback.message.delete_reply_markup()
    
    trip_id = callback.data.split("_")[-1]
    try:
        await orm_delete_trip(session, int(trip_id))
    except Exception as e:
        await callback.message.answer(EXCLAMATION_MARK + (i18n.get("Something went wrong. Please start over")), reply_markup=MENU_KEYBOARD)
        await state.clear()
        return

    await state.clear()
    await callback.answer(i18n.get("The trip has been removed"))
    await callback.message.answer(ALL_GOOD_SIGN + (i18n.get("The trip has been removed")), reply_markup=MENU_KEYBOARD)


#Handler for Trip - Start date
@user_handlers_router.callback_query(StateFilter(AddChangeTrip.add_start_date), SimpleCalendarCallback.filter())
async def trip_start_date_callback(callback: types.CallbackQuery, callback_data: CallbackData, state: FSMContext, session: AsyncSession, i18n: I18nContext) -> None:
    data = await state.get_data()
        
    calendar = MySimpleCalendar(i18n=i18n, show_alerts=False)

    selected, date = await calendar.process_selection(callback, callback_data)
    
    if AddChangeTrip.trip_to_change:
        enddate = data['trip_to_change_details'].enddate
        message_text = i18n.get("Add new end date")
        date_year = int(enddate.year)
        date_month = int(enddate.month)
    else:
        message_text = i18n.get("Add end date")
        date_year = int(datetime.today().year)
        date_month = int(datetime.today().month)
    
    if selected:
        previous_message_id = data.get('previous_message_id')
        if previous_message_id:
            await callback.message.bot.edit_message_text(ALL_GOOD_SIGN + i18n.get("Start date selected: {selected_startdate}", selected_startdate=date.strftime("%d-%m-%y")), callback.message.chat.id, previous_message_id)
        await state.update_data(startdate=date)
        await state.set_state(AddChangeTrip.add_end_date)
        msg = await callback.message.answer(message_text, reply_markup=await MySimpleCalendar(i18n=i18n, show_alerts=False).start_calendar(date_year, date_month))
        await state.update_data(previous_message_id=msg.message_id)


#Handler for Trip - Start date
@user_handlers_router.message(AddChangeTrip.add_start_date, or_f(F.text, F.text == "."))
async def trip_start_date(message: types.Message, state: FSMContext, session: AsyncSession, i18n: I18nContext) -> None:
    data = await state.get_data()
    
    if message.text == "." and AddChangeTrip.trip_to_change:
        await state.update_data(startdate=AddChangeTrip.trip_to_change.startdate)
        input_datetime = AddChangeTrip.trip_to_change.startdate
    else:
        if not is_valid_date_format(message.text):
            await message.answer(WARNING_SIGN + (i18n.get("The information you entered is not a valid date. Please use the following format: dd-mm-yy")))
            return
        input_datetime = datetime.strptime(message.text, '%d-%m-%y')
        await state.update_data(startdate=input_datetime)
    
    previous_message_id = data.get('previous_message_id')
    if previous_message_id:
        await message.bot.edit_message_text(ALL_GOOD_SIGN + i18n.get("Start date selected: {selected_startdate}", selected_startdate=input_datetime.strftime("%d-%m-%y")), message.chat.id, previous_message_id)
    
    msg = await message.answer(i18n.get("Add end date"))
    await state.update_data(previous_message_id=msg.message_id)
    
    await state.set_state(AddChangeTrip.add_end_date)


#Handler for Trip End date - callback
@user_handlers_router.callback_query(StateFilter(AddChangeTrip.add_end_date), SimpleCalendarCallback.filter())
async def trip_end_date_callback(callback: types.CallbackQuery, callback_data: CallbackData, state: FSMContext, session: AsyncSession, i18n: I18nContext) -> None:    
    data = await state.get_data()
    
    calendar = MySimpleCalendar(i18n=i18n, show_alerts=False)
    selected, date = await calendar.process_selection(callback, callback_data)
    if selected:
        if not is_date_after(data['startdate'], date):
            await callback.message.answer(WARNING_SIGN + (i18n.get("The date you entered is before the start date of your trip. Please enter a different date")))
            return
        else:
            await state.update_data(enddate=date)
            previous_message_id = data.get('previous_message_id')
            if previous_message_id:
                await callback.message.bot.edit_message_text(ALL_GOOD_SIGN + i18n.get("End date selected: {selected_enddate}", selected_enddate=date.strftime("%d-%m-%y")), callback.message.chat.id, previous_message_id)
            msg = await callback.message.answer(i18n.get("Add description"))
            await state.update_data(previous_message_id=msg.message_id)
            await state.set_state(AddChangeTrip.add_description)


#Handler for Trip - End date
@user_handlers_router.message(AddChangeTrip.add_end_date, or_f(F.text, F.text == "."))
async def trip_end_date(message: types.Message, state: FSMContext, session: AsyncSession, i18n: I18nContext) -> None:
    data = await state.get_data()
    
    if message.text == "." and AddChangeTrip.trip_to_change:
        await state.update_data(enddate=AddChangeTrip.trip_to_change.enddate)
        input_datetime = AddChangeTrip.trip_to_change.enddate
    else:
        if not is_valid_date_format(message.text):
            await message.answer(WARNING_SIGN + (i18n.get("The information you entered is not a valid date. Please use the following format: dd-mm-yy")))
            return
        if not is_date_after(data['startdate'], datetime.strptime(message.text, '%d-%m-%y')):
            await message.answer(WARNING_SIGN + (i18n.get("The date you entered is before the start date of your trip. Please enter a different date")))
            return
        input_datetime = datetime.strptime(message.text, '%d-%m-%y')
        await state.update_data(enddate=input_datetime)
    
    previous_message_id = data.get('previous_message_id')
    if previous_message_id:
        await message.bot.edit_message_text(ALL_GOOD_SIGN + i18n.get("End date selected: {selected_enddate}", selected_enddate=input_datetime.strftime("%d-%m-%y")), message.chat.id, previous_message_id)
    
    msg = await message.answer(i18n.get("Add description"))
    await state.update_data(previous_message_id=msg.message_id)

    await state.set_state(AddChangeTrip.add_description)


#Handler for Trip - Description
@user_handlers_router.message(AddChangeTrip.add_description, or_f(F.text, F.text == "."))
async def trip_description(message: types.Message, state: FSMContext, session: AsyncSession, i18n: I18nContext) -> None:
    if message.text == "." and AddChangeTrip.trip_to_change:
        await state.update_data(description=AddChangeTrip.trip_to_change.description)
        input_descriptiom = AddChangeTrip.trip_to_change.description
    else:
        await state.update_data(description=message.text)
        input_descriptiom = message.text
    
    await state.update_data(userid=message.from_user.id)
    data = await state.get_data()
    
    try:
        if AddChangeTrip.trip_to_change:
            trip_id = data['trip_id']
            await orm_update_trip(session, trip_id, data)
            AddChangeTrip.trip_to_change = None
            
            message_text = "Trip changed. Number of your days abroad: {days_abroad}"
        else:
            await orm_add_trip(session, data)
            
            message_text = "Trip added. Number of your days abroad: {days_abroad}"
            
        days_abroad = await calculate_number_of_days(session=session, userid=message.from_user.id)
        if days_abroad != -1:
            previous_message_id = data.get('previous_message_id')
            if previous_message_id:
                await message.bot.edit_message_text(ALL_GOOD_SIGN + i18n.get("Description selected: {selected_description}", selected_description=input_descriptiom), message.chat.id, previous_message_id)
            await message.answer(ALL_GOOD_SIGN + (i18n.get(message_text, days_abroad=days_abroad)))
            await message.answer(i18n.get("Here is the menu"), reply_markup=MENU_KEYBOARD)
        else:
            await message.answer(EXCLAMATION_MARK + (i18n.get("Sorry, I'm on maintenance. Please try again later")))
        
    except Exception as e:
        await message.answer(EXCLAMATION_MARK + (i18n.get("Something went wrong. Please start over")), reply_markup=MENU_KEYBOARD)

    await state.clear()
