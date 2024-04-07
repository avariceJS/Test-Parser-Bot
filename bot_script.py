
# Base
import asyncio
import logging
import os
import sys
from dotenv import load_dotenv, dotenv_values

# parser_scripts
from parser_script import count_files_in_folder, delete_file, delete_folder, parser_main, download, dom_all

# aiogram
from aiogram import Bot, Dispatcher,  Router, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (InlineKeyboardMarkup, InlineKeyboardButton, Message, BufferedInputFile)

load_dotenv()

# Initialize the bot with its token
bot = Bot(token=f'{os.getenv("BOT_TOKEN")}')

# Include the Router into the Dispatcher
form_router = Router()
dp = Dispatcher()
dp.include_router(form_router)

# States
class Form(StatesGroup):
    url = State()
    limit = State()
    media = State()
    photo_count = State()
    chat_id = State()

# Handler for the /start command
@form_router.message(CommandStart())
async def command_start(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.url)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔎 Парсинг", callback_data="parse")],
        # [InlineKeyboardButton(text="💳 Оплата", callback_data="payment"),
        #  InlineKeyboardButton(text="❓ Помощь", callback_data="help")],
        # [InlineKeyboardButton(text="📩 Бот для поиска сообщений", callback_data="search_messages")],
        # [InlineKeyboardButton(text="🛸 Бот для поиска групп", callback_data="search_groups")],
        # [InlineKeyboardButton(text="⏩ Дополнительно", callback_data="additional")],
    ])
    # Delete existing files and folders on startup
    delete_folder('./files')
    delete_file('telegram_group_data.txt')
    await message.answer("Главное меню:", reply_markup=keyboard)


# "parse" Callback 
@form_router.callback_query(lambda c: c.data == "parse")
async def parse_callback(callback: types.CallbackQuery):
        keyboard = None
        if callback.data == "parse":
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🛠 Дополнительно", callback_data="parse")],
                [InlineKeyboardButton(text="✖️ Отмена", callback_data="cancel")],
            ])
        if callback.message is not None:
            await bot.edit_message_text("Отправьте ссылку на группу, откуда нужно собрать пользователей. "
                                    "Если у группы нет ссылки или через ссылку не получается сделать парсинг, "
                                    "нажмите на кнопку \"Дополнительно\".", callback.from_user.id,
                                    callback.message.message_id, reply_markup=keyboard)
        
        # URL handler
        @form_router.message(Form.url)
        async def process_url(message: Message, state: FSMContext) -> None:
            url = message.text
            await state.update_data(url=url)
            await state.set_state(Form.limit)
            await message.answer("Ограничить количество страниц (0 для неограниченного):")

        # Limit handler
        @form_router.message(Form.limit)
        async def process_limit(message: Message, state: FSMContext) -> None:
            limit = message.text
            await state.update_data(limit=limit)
            await state.set_state(Form.media)
            await message.answer("Загрузить медиафайл? (yes/no):")

        # Media handler
        @form_router.message(Form.media)
        async def process_media(message: Message, state: FSMContext) -> None:
            media = message.text
            await state.update_data(media=media)
            data = await state.get_data()
            url = data.get("url")
            limit = data.get("limit")
            chat_id = data.get("chat_id")
            
            if media == "yes":
                res, file_name, photo_files = parser_main(url, limit, media, chat_id)
                total_photos = count_files_in_folder('./files')
                await state.update_data(total_photos=total_photos)  
                await state.set_state(Form.photo_count)
                await message.answer(f"Сколько фотографий вы хотите отправить? Скачано {total_photos}")
            
            elif media == "no":
                res, file_name, _  = parser_main(url, limit, media, chat_id)
                await bot.send_message(message.chat.id, "Медиафайлы не будут загружены.")
                with open(file_name, 'rb') as file:
                    file_content = file.read()
                input_file = BufferedInputFile(file_content, filename=file_name)
                await bot.send_document(message.chat.id, input_file)
                await state.clear()
                
            else:
                await message.answer("Пожалуйста, ответьте 'yes' или 'no'.")
# Photo handler
@form_router.message(Form.photo_count)
async def process_photo_count(message: Message, state: FSMContext) -> None:
    photo_count = message.text
    if photo_count is None:
        await message.answer("Пожалуйста, введите целое число")
        return
    photo_count = int(photo_count)
    await state.update_data(photo_count=photo_count)

    # Data from state
    data = await state.get_data()
    url = data.get("url")
    limit = data.get("limit")
    media = data.get("media")
    chat_id = data.get("chat_id")
   
   
    res, file_name, photo_files = parser_main(url, limit, media, chat_id)
    download(url)
    dom_all(url)
    parser_main(url, limit, media, chat_id)

    # Logging user data
    logging.info("User data: url=%s, limit=%s, media=%s, chat_id=%s", url, limit, media, chat_id)

    count = int(photo_count)
    for i in range(count):
        with open(photo_files[i], 'rb') as file:
            file_content = file.read()
        input_file = BufferedInputFile(file_content, filename=photo_files[i])
        await bot.send_document(message.chat.id, input_file)

    # main txt file
    with open(file_name, 'rb') as file:
        file_content = file.read()
    input_file = BufferedInputFile(file_content, filename=file_name)
    await bot.send_document(message.chat.id, input_file)
    
    # Delete existing files and folders after parsing
    delete_folder('./files')
    delete_file('telegram_group_data.txt')

    await message.answer("Спасибо! Ваши данные сохранены.")
    await state.clear()

@form_router.callback_query(lambda c: c.data == "cancel")
async def cancel_callback(callback: types.CallbackQuery):
    if callback.data == "cancel":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔎 Парсинг", callback_data="parse")],
        ])
    if callback.message is not None:
        await bot.edit_message_text("Главное меню:", message_id=callback.message.message_id, chat_id=callback.message.chat.id, reply_markup=keyboard)
    
# Main function to start the bot
async def main():
    await dp.start_polling(bot)

# Entry point
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
