import math

from aiogram import Bot, Dispatcher, executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import Message, reply_keyboard, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

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
    btn2 = KeyboardButton('Погода в другом городе')
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


@dp.message_handler(regexp="Меню")
async def start_message(message: Message):
    markup = await main_menu()
    text = f"Привет, {message.from_user.first_name}! Я - бот, который расскажет тебе о погоде на сегодня"
    await message.reply(text=text, reply_markup=markup)


@dp.message_handler(regexp="Погода в моём городе")
async def get_user_city_weather(message: Message):
    markup = reply_keyboard.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = KeyboardButton("Меню")
    markup.add(btn1)
    city = orm.get_user_city(message.from_user.id)
    if not city:
        text = "Пожалуйста установите город проживания"
        await message.reply(text=text)
        await set_user_city_start()
        return
    data = get_weather(city)
    orm.create_report(message.from_user.id, data["temp"], data["feels_like"], data["wind_speed"],
                      data["pressure_mm"], city)
    text = f'Погода в {city}\nТемпература: {data["temp"]} C\nОщущается как: {data["feels_like"]} C \nСкорость ветра: ' \
           f'{data["wind_speed"]}м/с\nДавление: {data["pressure_mm"]}мм'
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


@dp.message_handler(regexp="История")
async def get_reports(message: Message):
    current_page = 1
    reports = orm.get_reports(message.from_user.id)
    total_pages = math.ceil(len(reports) / 4)
    text = "История запросов"
    inline_markup = InlineKeyboardMarkup()
    for report in reports[:current_page * 4]:
        inline_markup.add(InlineKeyboardButton(text=f"{report.city} {report.date.day}.{report.date.month}."
                                                    f"{report.date.year}", callback_data=f"report_{report.id}"))
    current_page += 1
    inline_markup.row(
        InlineKeyboardButton(text=f'{current_page - 1}/{total_pages}', callback_data='None'),
        InlineKeyboardButton(text='Вперёд', callback_data=f'next_{current_page}'))
    await message.reply(text=text, reply_markup=inline_markup)


@dp.callback_query_handler(lambda call: True)
async def callback_query(call, state: FSMContext):
    # Получаем тип операции  и номер страницы или отчета из callback_data
    query_type, query_id = call.data.split('_')
    async with state.proxy() as data:

        if data.get('current_page', None) is None:
            data['current_page'] = 0

        if query_type is None:
            return

        if query_type in ('next', 'prev', 'reports'):
            data['current_page'] += {
                'next': 1,
                'prev': -1,
                'reports': 0,
            }[query_type]
            await state.update_data(current_page=data['current_page'])
            reports = orm.get_reports(call.from_user.id)
            total_pages = math.ceil(len(reports) / 4)
            inline_markup = InlineKeyboardMarkup()
            for report in reports[data['current_page'] * 4: (data['current_page'] + 1) * 4]:
                inline_markup.add(InlineKeyboardButton(
                    text=f'{report.city} {report.date.day}.{report.date.month}.{report.date.year}',
                    callback_data=f'report_{report.id}'
                ))
            buttons = []
            if data['current_page']:
                buttons.append(InlineKeyboardButton(text='Назад', callback_data=f'prev_{data["current_page"] - 1}'))
            buttons.append(InlineKeyboardButton(text=f'{data["current_page"]+1}/{total_pages}', callback_data='None'))
            if (data['current_page']+1)*4 < len(reports):
                buttons.append(InlineKeyboardButton(text='Вперёд', callback_data=f'next_{data["current_page"]}'))
            inline_markup.row(*buttons)
            await call.message.edit_text(text="История запросов:", reply_markup=inline_markup)

        if query_type == 'report':
            reports = orm.get_reports(call.from_user.id)
            report_id = call.data.split('_')[1]
            inline_markup = InlineKeyboardMarkup()
            for report in reports:
                if report.id == int(report_id):
                    inline_markup.add(
                        InlineKeyboardButton(text='Назад', callback_data=f'reports_{data["current_page"]}'),
                        InlineKeyboardButton(text='Удалить запрос', callback_data=f'delete_report_{report_id}')
                    )
                    await call.message.edit_text(
                        text=f'Данные по запросу\n'
                             f'Город:{report.city}\n'
                             f'Температура:{report.temp}\n'
                             f'Ощущается как:{report.feels_like}\n'
                             f'Скорость ветра:{report.wind_speed}\n'
                             f'Давление:{report.pressure_mm}',
                        reply_markup=inline_markup
                    )
                    break


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
    orm.create_report(message.from_user.id, data["temp"], data["feels_like"], data["wind_speed"], data["pressure_mm"],
                      city.get("waiting_city"))
    text = f'Погода в {city}\nТемпература: {data["temp"]} C\nОщущается как: {data["feels_like"]} C ' \
                      f'\nСкорость ветра: {data["wind_speed"]}м/с\nДавление: {data["pressure_mm"]}мм'
    await message.answer(text=text, reply_markup=markup)
    await state.finish()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)