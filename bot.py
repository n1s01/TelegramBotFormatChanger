import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

cache = {}

def get_token():
    return os.getenv('BOT_TOKEN') or input('Enter bot token: ')

def gen_key(text, msg_id):
    return f"fmt_{hash(text)}_{msg_id}"

def make_kb(key):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="HTML", callback_data=f"html_{key}")],
        [InlineKeyboardButton(text="Markdown", callback_data=f"md_{key}")]
    ])

def to_html(text):
    return (text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#x27;'))

def to_md(text):
    chars = ['\\', '`', '*', '_', '{', '}', '[', ']', '(', ')', '#', '+', '-', '.', '!']
    for char in chars:
        text = text.replace(char, f'\\{char}')
    return text

async def start_cmd(msg: Message):
    await msg.answer("Send me text and I'll format it for HTML or Markdown")

async def process_text(msg: Message):
    text = msg.html_text or msg.text
    key = gen_key(text, msg.message_id)
    cache[key] = text
    
    await msg.answer(
        f"Original text:\n<code>{to_html(text)}</code>\n\nChoose format:",
        reply_markup=make_kb(key),
        parse_mode=ParseMode.HTML
    )

async def handle_callback(call: CallbackQuery):
    fmt, key = call.data.split("_", 1)
    text = cache.get(key, "Text not found")
    
    if fmt == "html":
        result = f"<code>{to_html(text)}</code>"
        parse_mode = ParseMode.HTML
    else:
        result = f"```\n{to_md(text)}\n```"
        parse_mode = ParseMode.MARKDOWN_V2
    
    await call.message.edit_text(f"Formatted text:\n{result}", parse_mode=parse_mode)
    await call.answer()

dp = Dispatcher()
dp.message.register(start_cmd, CommandStart())
dp.message.register(process_text, F.text)
dp.callback_query.register(handle_callback, F.data.startswith(("html_", "md_")))

async def main():
    bot = Bot(get_token(), default=DefaultBotProperties(parse_mode=None))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())