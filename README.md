# days_abroad (available in Telegram: @days_abroad_bot)

Features
========
**days_abroad** Telegram bot, built with Aiogram, helps users track their days spent abroad, ensuring compliance with residency or tax regulations.
* Count your days abroad at the touch of a button
* Set thresholds for the number of days spent abroad in one or two years
* Add your trips abroad with a simple calendar based on the Telegram inline keyboard
* Change or delete your trip details at any time

The bot is available in English and Russian. Languages ​​can be changed using the Menu button in the lower left corner or through changing your settings.

Under the hood
========
**days_abroad** is written on Python and utilizes the following: 
* [aiogram](https://github.com/aiogram/aiogram) v3 library
* [aiogram_i18n](https://github.com/aiogram/i18n) library for processing localizations
* [aiogram_calendar](https://github.com/noXplode/aiogram_calendar) library for creating inline keyboard-based calendars
* [sqlalchemy](https://github.com/sqlalchemy/sqlalchemy) ORM toolkit
* [aiohttp](https://github.com/aio-libs/aiohttp) async HTTP framework
* GNU GetText library as a localization core
* SQlite database
* Nginx reverse proxy
* Docker compose
