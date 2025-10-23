import random
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor

# Здесь замени '7977469319:AAGWsXON1zGZnXUo8kmnM_ehRBbRekfsNTU' на свой API-ключ от @BotFather
API_TOKEN = 'токен'


# ‘🎲’, ‘🎯’, ‘🏀’, ‘⚽’, ‘🎳’, or ‘🎰’
# Список с эмодзи

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
logging_middleware = LoggingMiddleware()
dp.middleware.setup(logging_middleware)

@dp.message_handler(commands=['dice'])
async def roll_dice(message: types.Message):
    data = await bot.send_dice(message.chat.id, emoji='🎲')
    await bot.send_message(message.chat.id, f'значение кубика {data.dice.value}')

@dp.message_handler(commands=['dart'])
async def roll_dice(message: types.Message):
    data = await bot.send_dice(message.chat.id, emoji='🎯')
    await bot.send_message(message.chat.id, f'значение дартс {data.dice.value}')

@dp.message_handler(commands=['bask'])
async def roll_dice(message: types.Message):
    data = await bot.send_dice(message.chat.id, emoji='🏀')
    await bot.send_message(message.chat.id, f'значение баскет {data.dice.value}')

@dp.message_handler(commands=['foot'])
async def roll_dice(message: types.Message):
    data = await bot.send_dice(message.chat.id, emoji='⚽')
    await bot.send_message(message.chat.id, f'значение футбол {data.dice.value}')

@dp.message_handler(commands=['bowl'])
async def roll_dice(message: types.Message):
    data = await bot.send_dice(message.chat.id, emoji='🎳')
    await bot.send_message(message.chat.id, f'значение боулинг {data.dice.value}')

@dp.message_handler(commands=['slot'])
async def roll_dice(message: types.Message):
    data = await bot.send_dice(message.chat.id, emoji='🎰')
    await bot.send_message(message.chat.id, f'значение слоты {data.dice.value}')


if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)