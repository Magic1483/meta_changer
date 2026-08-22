import asyncio
import logging
import sys
from os import getenv
from typing import Optional

from aiogram import Bot, Dispatcher, Router,F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart,Command
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.fsm.state import State,StatesGroup
from pathlib import Path
from ..core import *
import dotenv
import shutil
from collections import defaultdict

# Bot token can be obtained via https://t.me/BotFather
dotenv.load_dotenv('.env')
TOKEN = getenv("BOT_TOKEN")
DOWNLOAD_DIR = Path("files")
USER_LOCKS:defaultdict[str,asyncio.Lock] = defaultdict(asyncio.Lock)

dp = Dispatcher()
BOT:Bot  = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

class BotState(StatesGroup):
    wait_for_preset = State()
    upload_archive  = State()

@dp.message(CommandStart())
async def command_start_handler(msg: Message) -> None:
    await msg.answer("Send a zip file with .jpg images after picking a preset with /preset.")

@dp.message(Command('preset'))
async def cmd_set_preset(msg:Message,state:FSMContext):
    await state.set_state(BotState.wait_for_preset)
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=txt) for txt in get_presets()]
        ],
        resize_keyboard=True)
    await msg.answer('Select preset:',reply_markup=kb)

@dp.message(BotState.wait_for_preset)
async def process_preset(msg: Message, state: FSMContext):
    await state.update_data(preset=msg.text)
    await state.set_state(BotState.upload_archive)
    await msg.answer(f"Upload zip archive with .jpg images", 
                     reply_markup=ReplyKeyboardRemove())

@dp.message(BotState.upload_archive , F.document)
async def cmd_download_arch(msg:Message,state:FSMContext):
    if not (msg.document.file_name or '').lower().endswith('zip'):
        return await msg.answer('Archive should be in zip format')
    
    chat_id      = str(msg.chat.id)
    if USER_LOCKS[chat_id].locked():
        await msg.answer('task in progress, wait..')
        return

    preset = (await state.get_data()).get('preset','')
    await state.clear()

    zip_path = DOWNLOAD_DIR / f"{chat_id}.zip"
    await BOT.download(msg.document,destination=zip_path)
    await msg.answer(f'Start processing photos with preset {preset}')
    asyncio.create_task(process_archive(zip_path,chat_id,preset))

async def process_archive(zip_path:Path,chat_id:str,preset:str):
    ext_dir = zip_path.with_suffix("")
    out_zip = DOWNLOAD_DIR / f"{chat_id}_out.zip"

    async with USER_LOCKS[chat_id]:
        try:
            await asyncio.to_thread(shutil.unpack_archive, filename=zip_path, extract_dir=ext_dir)
            zip_path.unlink()
            await asyncio.to_thread(set_metadata,[f'{ext_dir}/*'],preset)

            await asyncio.to_thread(shutil.make_archive, 
                    str(out_zip.with_suffix("")), 'zip', ext_dir)

            await BOT.send_document(
                chat_id,
                FSInputFile(out_zip,filename="processed.zip"),
                caption='Done!')
        except Exception as err:
            await BOT.send_message(chat_id,f'Error processing images: {err}')
        finally:
            if ext_dir.exists(): await asyncio.to_thread(shutil.rmtree,ext_dir)
            out_zip.unlink(missing_ok=True)
            if not USER_LOCKS[chat_id].locked(): USER_LOCKS.pop(chat_id,None)

async def run_bot() -> None:
    if not TOKEN:
        raise RuntimeError('bot TOKEN not found in .env file')
    
    DOWNLOAD_DIR.mkdir(exist_ok=True,parents=True)
    await dp.start_polling(BOT)

def main():
    asyncio.run(run_bot())

if __name__ == "__main__":
    main()