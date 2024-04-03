import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, types
from chat_id import get_chat_id
from parser_script import parse_all, parser_main, download, domAll
from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (InlineKeyboardMarkup, InlineKeyboardButton)
from aiogram.types import (

    Message,
)

bot = Bot(token="6616595798:AAFRxsUqV4Bp8hqiA1HcI_bYnpehkE25qHM")
form_router = Router()


class Form(StatesGroup):
    url = State()
    limit = State()
    media = State()
    bot_token = State()
    chat_id = State()


@form_router.message(CommandStart())
async def command_start(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.url)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔎 Парсинг", callback_data="parse"),
        ],
         [
            InlineKeyboardButton(text="💳 Оплата", callback_data="payment"),
            InlineKeyboardButton(text="❓ Помощь", callback_data="help")
        ],
                 [
            InlineKeyboardButton(text="📩 Бот для поиска сообщений", callback_data="search_messages"),
        ],
                         [
            InlineKeyboardButton(text="🛸 Бот для поиска групп", callback_data="search_groups"),
        ],
                [
            InlineKeyboardButton(text="⏩ Дополнительно", callback_data="additional"),
        ],
    ])
    await message.answer("Главное меню:", reply_markup=keyboard)
   
@form_router.callback_query(lambda c: c.data == "parse")
async def parse_callback(callback: types.CallbackQuery):
        keyboard = None
        if callback.data == "parse":
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🛠 Дополнительно", callback_data="parse"),
        ],

        [
            InlineKeyboardButton(text="✖️ Отмена", callback_data="cancel"),
        ],
    ])
    
            await bot.edit_message_text("Отправьте ссылку на группу, откуда нужно собрать пользователей Если у группы нет ссылки, или через ссылку не получается сделать парсинг, нажмите на кнопку \"Дополнительно\" ", callback.from_user.id, callback.message.message_id, reply_markup=keyboard)

        @form_router.message(Form.url)
        async def process_url(message: Message, state: FSMContext) -> None:
            url = message.text
            await state.update_data(url=url)
            await state.set_state(Form.limit)
            await message.answer("Ограничить количество страниц (0 для неограниченного):")


        @form_router.message(Form.limit)
        async def process_limit(message: Message, state: FSMContext) -> None:
            limit = message.text
            await state.update_data(limit=limit)
            await state.set_state(Form.media)
            await message.answer("Загрузить медиафайл? (yes/no):")


        @form_router.message(Form.media)
        async def process_media(message: Message, state: FSMContext) -> None:
            media = message.text
            await state.update_data(media=media)
            await state.set_state(Form.chat_id)
            await message.answer("Введите свой id чата(не обязательно):")

        @form_router.message(Form.chat_id)
        async def process_chat_id(message: Message, state: FSMContext) -> None:
            chat_id = message.text
            await state.update_data(chat_id=chat_id)

            data = await state.get_data()

            url = data.get("url")
            limit = data.get("limit")
            media = data.get("media")
            chat_id = data.get("chat_id")
            
            id = get_chat_id(bot, url)
            result =  parse_all(url)

            download(url)
            domAll(url)
            parser_main(url, limit, media, chat_id)
            
            logging.info("User data: url=%s, limit=%s, media=%s, chat_id=%s", url, limit, media,  chat_id)


            await message.answer("Спасибо! Ваши данные сохранены.")

            await state.clear()


async def main():
    dp = Dispatcher()
    dp.include_router(form_router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
