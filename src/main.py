import asyncio
import sys
from os import getenv

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from pprint import pprint
import io

TOKEN = '6264571804:AAGNFCvBnpFy7FaUZTDwSX6fvSVh3TFnLaE'
SCOPES = ["https://www.googleapis.com/auth/drive"]

creds = Credentials.from_authorized_user_file("token.json", SCOPES)
flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES)
# creds = flow.run_local_server(port=0) # for google auth
service = build("drive", "v3", credentials=creds)
results = (
        service.files()
        .list(pageSize=10, fields="nextPageToken, files(id, name)")
        .execute())
items = results.get("files", [])

# pprint(results)


# bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message()
async def echo(message: Message):
    await bot.send_message(result)


async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())