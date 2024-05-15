import sys
from aiogram import F, types, Router
from aiogram.filters import Command, StateFilter, or_f, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram_i18n import I18nContext, LazyProxy
from sqlalchemy.ext.asyncio import AsyncSession


from common.bot_commands import MENU_ITEMS_ADMIN
from database.orm_query import orm_get_users_count
from filters.chat_types import ChatTypeFilter, IsAdmin
from keyboards.inline_keyboard import build_inline_callback_keyboard
from states.user_states import AdminFeatures

ADMIN_KEYBOARD = build_inline_callback_keyboard(
    buttons={
        LazyProxy("Restart bot"): f"restart", 
        LazyProxy("Get number of users"): f"count"
    }
)

admin_handlers_router = Router()
admin_handlers_router.message.filter(ChatTypeFilter(["private"]), IsAdmin())

@admin_handlers_router.message(StateFilter("*"), Command("cancel"))
@admin_handlers_router.message(StateFilter("*"), or_f(F.data.contains("cancel"), F.text.casefold() == "cancel"))
async def cancel_handler(message: types.Message, state: FSMContext, i18n: I18nContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.clear()
    await message.answer(
        message.answer(i18n.get("Your actions were cancelled. Let's start it over")),
        CommandStart()
    )


@admin_handlers_router.message(StateFilter(None), Command("admin"))
async def admin_features(message: types.Message, state: FSMContext, i18n: I18nContext) -> None:
    await message.bot.delete_my_commands(scope=types.BotCommandScopeChat(chat_id=message.chat.id))
    await message.bot.set_my_commands(
        commands=MENU_ITEMS_ADMIN, scope=types.BotCommandScopeChat(chat_id=message.chat.id)
    )
    await state.set_state(AdminFeatures.selectOption)
    await message.answer(
        i18n.get("Hey, Admin"),
        reply_markup=ADMIN_KEYBOARD
    )


@admin_handlers_router.callback_query(StateFilter(AdminFeatures.selectOption), F.data.contains("restart"))
async def restart_callback(callback: types.CallbackQuery,  state: FSMContext, i18n: I18nContext) -> None:
    await callback.answer(i18n.get("Restarting, please wait..."))
    await state.clear()
    await sys.exit(0)


@admin_handlers_router.callback_query(StateFilter(AdminFeatures.selectOption), F.data.contains("count"))
async def count_callback(callback: types.CallbackQuery,  state: FSMContext, session: AsyncSession, i18n: I18nContext) -> None:
    try:
        users = await orm_get_users_count(session)
    except Exception as e:
        await callback.message.answer(i18n.get("Sorry, I'm on maintenance. Please try again later"))
        
    await callback.message.answer(i18n.get("Number of unique users is {users_count}", users_count=len(users)))
