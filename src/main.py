import asyncio
import sys
from os import getenv

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile, URLInputFile, BufferedInputFile
from aiogram import exceptions
from aiohttp import *

from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from pprint import pprint
import io
import os

TOKEN = '6264571804:AAGNFCvBnpFy7FaUZTDwSX6fvSVh3TFnLaE'
SCOPES = ["https://www.googleapis.com/auth/drive"]

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

items = []

service = None


async def drive():
    global service
    global items
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
    #   creds = flow.run_local_server(port=0)
    with open("token.json", "w") as token:
      token.write(creds.to_json())

    service = build("drive", "v3", credentials=creds)

    # Call the Drive v3 API
    # results = (
    #         service.files()
    #         .list(pageSize=10, fields="nextPageToken, files(id, name)")
    #         .execute()
    #     )

    results = service.files().list(
    pageSize=1000, 
    fields="nextPageToken, files(id, name, mimeType, size)").execute()
    
    items = results.get("files", [])
    return items


@dp.message(Command('help'))
async def start(message: Message):
    text = '''
    Usage:
    /print
    /download file_id
    write /upload in description
    /delete file_id
    '''

    await bot.send_message(chat_id=1250479132, text=text)


@dp.message(Command("print"))
async def see_all(message: Message):
    items = await drive()
    text = ''
    for i in range(len(items)):
        try:
            if not (items[i]["mimeType"] == 'application/vnd.google-apps.map') and not (items[i]["mimeType"] == 'application/vnd.google-apps.folder') and items[i]["size"]:
                text += f'{items[i]["name"]} ({items[i]["id"]})\n'
                text += '---\n'
        except Exception as e:
            if not (items[i]["mimeType"] == 'application/vnd.google-apps.map') and not (items[i]["mimeType"] == 'application/vnd.google-apps.folder'):
                text += f'{items[i]["name"]} ({items[i]["id"]})\n'
                text += '---\n'

    for i in range(0, len(text), 4096):
        chunk = text[i:i + 4096]
        await bot.send_message(1250479132, chunk)
        await asyncio.sleep(1)



@dp.message(Command("download"))
async def download(message):
    # print(items)
    mimeType = ''
    filename = ''
    for item in items:
        if item.get('id') == message.text[10:]:
            filename = item.get("name", '')
            mimeType = item.get("mimeType", '')
            print(filename)

    file_id = message.text[10:]
    
    if mimeType == 'application/vnd.google-apps.spreadsheet':
        request = service.files().export_media(fileId=file_id,
                                    mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        filename += '.xlsx'
    elif mimeType == 'application/vnd.google-apps.document':
        request = service.files().export_media(fileId=file_id,
                                           mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        filename += '.docx'
    elif mimeType == 'application/vnd.google-apps.presentation':
        request = service.files().export_media(fileId=file_id,
                                           mimeType='application/vnd.openxmlformats-officedocument.presentationml.presentation')
        filename += '.pptx'
    else:
        request = service.files().get_media(fileId=file_id)
    
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)

    print(mimeType, filename, file_id)

    done = False
    await bot.send_message(chat_id=1250479132, text=f"Download {filename}")
    while not done:
        status, done = downloader.next_chunk()
        await bot.send_message(chat_id=1250479132, text=f"{int(status.progress() * 100)}%")
    fh.seek(0)
    file_save_path = os.path.join('./data', filename)
    with open(file_save_path, 'wb') as f:
        f.write(fh.read())
        f.close()
        
    
    try:
        document = FSInputFile(path=f'./data/{filename}')
        await bot.send_document(chat_id=1250479132, document=document)   
        os.remove(f'data/{filename}')

    except exceptions.TelegramEntityTooLarge:
        file = service.files().get(fileId=file_id, fields='webViewLink').execute()
        await bot.send_message(chat_id=1250479132, text="File is too large")
        await bot.send_message(chat_id=1250479132, text=f"{file.get('webViewLink')}")
        os.remove(f'data/{filename}')
    return


@dp.message(Command("upload"))
async def upload(message: Message):
    file_id_tg = message.document.file_id
    file_info = await bot.get_file(file_id_tg)
    file_path = file_info.file_path
    download_path = './data'
    
    async with ClientSession() as session:
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
        async with session.get(file_url) as response:
            if response.status == 200:
                file_name = message.document.file_name
                file_save_path = os.path.join('./data', file_name)
                with open(file_save_path, 'wb') as f:
                    f.write(await response.read())
            else:
                await bot.send_message(chat_id=1250479132, text="Error")
    
    try:
        file_metadata = {
            'name': file_name
        }
        media = MediaFileUpload(f'./data/{file_name}', resumable=True)
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        await bot.send_message(chat_id=1250479132, text=f"{file.get('id')}")
        os.remove(f'./data/{file_name}')
    except Exception as e:
        print(e)
    await drive()
    return


@dp.message(Command('delete'))
async def delete(message: Message):
    file_id = message.text[8:]
    try:
        service.files().delete(fileId=file_id).execute()
        await bot.send_message(chat_id=1250479132, text='The file has been successfully deleted')
    except Exception as e:
        await bot.send_message(chat_id=1250479132, text='You don`t have permission to delete this file')
    return


async def main():
    # global items1
    # results = await drive()
    # for i in range(len(results["files"])):
    #     if results["files"][i]["name"].startswith('-'):
    #         continue
    #     items1 += results["files"][i]["name"] + "\n"
    # print(items1)
    await drive()
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())