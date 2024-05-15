import os
from aiogram.filters import Filter
from aiogram import types
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

admins_list_temp = os.getenv("ADMINS_LIST")

if admins_list_temp is not None:
    if admins_list_temp != "":
        admins_list = admins_list_temp.split(',')
        admins_list = list(map(int, admins_list))
    else:
        admins_list = None


class ChatTypeFilter(Filter):
    def __init__(self, chat_types: list[str]) -> None:
        self.chat_types = chat_types

    async def __call__(self, message: types.message) -> bool:
        return message.chat.type in self.chat_types


class IsAdmin(Filter):
    def __init__(self) -> None:
        pass

    async def __call__(self, message: types.message) -> bool:
        if admins_list is not None:
            return (message.from_user.id in admins_list)
        else:
            return False