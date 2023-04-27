from aiogram import Bot, Dispatcher, executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import Message, reply_keyboard, KeyboardButton

from settings.get_token import load_env

from api_requests.request import get_weather

from database import orm

bot: Bot = Bot(token=load_env("BOT_TOKEN"))
storage: MemoryStorage = MemoryStorage()  # Запись состояния в оперативную память
dp: Dispatcher = Dispatcher(bot, storage=storage)


class ChoiceCityWeather(StatesGroup):
    """Класс для сохранения состояния"""

    waiting_city = State()  # Здесь хранится состояние диалога


class SetUserCity(StatesGroup):
    waiting_user_city = State()


async def main_menu():
    markup = reply_keyboard.ReplyKeyboardMarkup(row_width=2)
    btn1 = KeyboardButton('Погода в моём городе')
    btn2 = KeyboardButton('Погода в другом месте')
    btn3 = KeyboardButton('История')
    btn4 = KeyboardButton('Установить свой город')
    markup.add(btn1, btn2, btn3, btn4)
    return markup


@dp.message_handler(commands="start")
async def start_message(message: Message):
    orm.add_user(message.from_user.id)
    markup = await main_menu()
    text = f"Привет, {message.from_user.first_name}! Я - бот, который расскажет тебе о погоде на сегодня"
    await message.reply(text=text, reply_markup=markup)


@dp.message_handler(regexp="Погода в моём городе")
async def get_user_city_weather(message: Message):
    markup = reply_keyboard.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = KeyboardButton("Меню")
    markup.add(btn1)
    text = f"Я пока так не умею"
    await message.reply(text=text, reply_markup=markup)


@dp.message_handler(regexp="Погода в другом городе")
async def city_start(message: Message):
    markup = reply_keyboard.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = KeyboardButton("Меню")
    markup.add(btn1)
    text = "Введите название города"
    await message.reply(text=text, reply_markup=markup)
    await ChoiceCityWeather.waiting_city.set()  # При вводе данного хандлера бот ожидает названия города


@dp.message_handler(regexp="Установить свой город")
async def set_user_city_start(message: Message):
    markup = reply_keyboard.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = KeyboardButton("Меню")
    markup.add(btn1)
    text = "В каком городе проживаете?"
    await message.reply(text=text, reply_markup=markup)
    await SetUserCity.waiting_user_city.set()


@dp.message_handler(state=SetUserCity)
async def user_city_chosen(message: Message, state: FSMContext):
    await state.update_data(waiting_user_city=message.text.capitalize())
    user_data = await state.get_data()
    orm.set_user_city(message.from_user.id, user_data.get("waiting_user_city"))
    markup = await main_menu()
    text = f'Запомнил, {user_data.get("waiting_user_city")} ваш город'
    await message.answer(text, reply_markup=markup)
    await state.finish()


@dp.message_handler(state=ChoiceCityWeather.waiting_city)
async def city_chosen(message: Message, state: FSMContext):
    await state.update_data(waiting_city=message.text.capitalize())
    markup = await main_menu()
    city = await state.get_data()
    data = get_weather(city.get('waiting_city'))
    text = f'''Погода в {city.get("waiting_city")}
    Температура: {data["temp"]} C
    Ощущается как: {data["feels_like"]} C 
    Скорость ветра: {data["wind_speed"]}м/с
    Давление: {data["pressure_mm"]}мм'''
    await message.answer(text=text, reply_markup=markup)
    await state.finish()


@dp.message_handler(regexp="Меню")
async def start_message(message: Message):
    markup = await main_menu()
    text = f"Привет, {message.from_user.first_name}! Я - бот, который расскажет тебе о погоде на сегодня"
    await message.reply(text=text, reply_markup=markup)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)