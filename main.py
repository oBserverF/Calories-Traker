from telebot import TeleBot, types
from telebot import custom_filters
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage

from config import BOT_TOKEN
from database import *

memory_storage = StateMemoryStorage()
bot = TeleBot(BOT_TOKEN, state_storage=memory_storage)


class AddStats(StatesGroup):
    change_data = State()
    add_gender = State()
    add_weight = State()
    add_height = State()
    add_age = State()


class AddFood(StatesGroup):
    product_name = State()
    product_weight = State()


@bot.message_handler(state='*', commands=['start', 'cancel'])
def start(message: types.Message):
    bot.delete_state(message.from_user.id)

    text_msg = """
Добрый день👋!
Этот бот поможет вам подсчитать ваши калории за день!

Список доступных команд:

/info-<i>Выводит список всех команд и информацию о них</i>

/mystats-<i>Показывает данные пользователя(пол, вес, рост, возраст, норма калорий)</i>

/addstats-<i>Начинает диалог занесения всех данных пользователя(пол,вес, рост, возраст)</i>

/norm-<i>Выводит рекомендуемую дневную норму калорий</i>

/today-<i>Выводит кол-во калорий за день</i>

/addfood-<i>Добавить еду в дневной учет калорий</i>

/nextday-<i>Обнуляет значение кол-во калорий за день в бд.</i>
"""
    bot.send_message(message.from_user.id, text_msg, parse_mode='html')
    init_user(message.from_user.id)


@bot.message_handler(commands=['info'])
def info(message: types.Message):
    text_msg = """
Список доступных команд:

/info-<i>Выводит список всех команд и информацию о них</i>

/mystats-<i>Показывает данные пользователя(пол, вес, рост, возраст, норма калорий)</i>

/addstats-<i>Начинает диалог занесения всех данных пользователя(пол,вес, рост, возраст)</i>

/norm-<i>Выводит рекомендуемую дневную норму калорий</i>

/today-<i>Выводит кол-во калорий за день</i>

/addfood-<i>Добавить еду в дневной учет калорий</i>

/nextday-<i>Обнуляет значение кол-во калорий за день.</i>
"""
    bot.send_message(message.from_user.id, text_msg, parse_mode='html')


@bot.message_handler(commands=['mystats'])
def show_stats(message: types.Message):
    db_request = get_user_stats(message.from_user.id)
    if db_request == (None, None, None, None, None):
        bot.send_message(message.from_user.id,
                         'Вы еще не занесли свои данные!\n'
                         'Для того, чтобы занести свои данные пропишите /addstats')
    else:
        gender, weight, height, age, norm_calories = db_request
        text_msg = f"""
Ваш пол: {'Женский' if gender == 'W' else 'Мужской'}
Ваш вес: {weight}
Ваш рост: {height}
Ваш возраст: {age}
Ваша норма дневных калорий: {norm_calories}
"""
        bot.send_message(message.from_user.id, text_msg)


@bot.message_handler(commands=['addstats'])
def add_stats(message: types.Message):
    db_request = get_user_stats(message.from_user.id)
    if db_request == (None, None, None, None, None):
        reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        reply_markup.add(types.KeyboardButton(text='М'),
                         types.KeyboardButton(text='Ж'))
        bot.send_message(message.from_user.id, 'Введите ваш пол (М-мужской, Ж-жеский)\n'
                                               'Для отмены напишите /cancel !', reply_markup=reply_markup)
        bot.set_state(message.from_user.id, AddStats.add_gender)
    else:
        reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        reply_markup.add(types.KeyboardButton(text='Да'),
                         types.KeyboardButton(text='Нет'))
        bot.send_message(message.from_user.id, 'У вас уже заполнены данные, хотите их изменить?',
                         reply_markup=reply_markup)
        bot.set_state(message.from_user.id, AddStats.change_data)


@bot.message_handler(state=AddStats.add_gender)
def add_gender(message: types.Message):
    if message.text.upper() in ['М', 'Ж']:
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            if message.text.upper() == 'М':
                data['gender'] = 'M'
            else:
                data['gender'] = 'W'
        bot.send_message(message.from_user.id, 'Введите ваш вес')
        bot.set_state(message.from_user.id, AddStats.add_weight)
    else:
        bot.send_message(message.from_user.id, 'Введите действительный пол (М-мужской, Ж-женский)!')


@bot.message_handler(state=AddStats.add_weight)
def add_weight(message: types.Message):
    try:
        weight = float(message.text)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['weight'] = weight
        bot.send_message(message.from_user.id, 'Введите ваш рост')
        bot.set_state(message.from_user.id, AddStats.add_height)
    except ValueError:
        bot.send_message(message.from_user.id, 'Вес должен быть числом!')


@bot.message_handler(state=AddStats.add_height)
def add_height(message: types.Message):
    try:
        height = float(message.text)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['height'] = height
        bot.send_message(message.from_user.id, 'Введите ваш возраст')
        bot.set_state(message.from_user.id, AddStats.add_age)
    except ValueError:
        bot.send_message(message.from_user.id, 'Рост должен быть числом!')


@bot.message_handler(state=AddStats.add_age)
def add_age(message: types.Message):
    try:
        age = int(message.text)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['age'] = age
            norm_calories = add_user_data(message.from_user.id,
                                          data['gender'],
                                          data['weight'],
                                          data['height'],
                                          data['age'])
            data = {}
        bot.send_message(message.from_user.id, f'Ваша дневная норма калорий: {norm_calories}')
        info(message)
        bot.delete_state(message.from_user.id)
    except ValueError:
        bot.send_message(message.from_user.id, 'Возраст должен быть числом!')


@bot.message_handler(state=AddStats.change_data)
def change_data(message: types.Message):
    if message.text.upper() == 'ДА':
        reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        reply_markup.add(types.KeyboardButton(text='М'),
                         types.KeyboardButton(text='Ж'))
        bot.send_message(message.from_user.id, 'Введите ваш пол (М-мужской, Ж-жеский)\n'
                                               'Для отмены напишите /cancel !', reply_markup=reply_markup)
        bot.set_state(message.from_user.id, AddStats.add_gender)
    else:
        bot.delete_state(message.from_user.id)
        start(message)


@bot.message_handler(commands=['norm'])
def user_norm(message: types.Message):
    db_request = get_user_stats(message.from_user.id)
    if db_request == (None, None, None, None, None):
        bot.send_message(message.from_user.id,
                         'Вы еще не занесли свои данные!\n'
                         'Для того, чтобы занести свои данные пропишите /addstats')
    else:
        bot.send_message(message.from_user.id, f'Ваша норма калорий: {db_request[-1]}')


@bot.message_handler(commands=['addfood'])
def add_food(message: types.Message):
    bot.send_message(message.from_user.id, 'Напишите название продукта')
    bot.set_state(message.from_user.id, AddFood.product_name)


@bot.message_handler(state=AddFood.product_name)
def add_product_name(message: types.Message):
    if product_in_list(message.text):
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['product'] = message.text
        bot.send_message(message.from_user.id, 'Напишите граммовку продукта')
        bot.set_state(message.from_user.id, AddFood.product_weight)
    else:
        bot.send_message(message.from_user.id, 'Продукт не найден!')


@bot.message_handler(state=AddFood.product_weight)
def add_product_weight(message: types.Message):
    try:
        weight = float(message.text)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            daily = add_product_in_daily(data['product'], weight, message.from_user.id)
        bot.delete_state(message.from_user.id)

        db_request = get_user_stats(message.from_user.id)
        if db_request == (None, None, None, None, None):
            bot.send_message(message.from_user.id,
                             'Вы еще не занесли свои данные! \n'
                             'Для того, чтобы занести свои данные пропишите /addstats')
        else:
            if daily > db_request[-1]:
                bot.send_message(message.from_user.id,
                                 f'Вы превысили суточную норму калорий на {daily - db_request[-1]}')
            elif daily == db_request[-1]:
                bot.send_message(message.from_user.id, f'Вы ровно уложились в суточную норму калорий!')
            elif daily < db_request[-1]:
                bot.send_message(message.from_user.id,
                                 f'Вам осталось {db_request[-1] - daily} калорий до суточной нормы')

    except ValueError:
        bot.send_message(message.from_user.id, 'Граммовка должна быть числом!')


@bot.message_handler(commands=['nextday'])
def nextday(message: types.Message):
    set_zero(message.from_user.id)
    bot.send_message(message.from_user.id, 'Дневные калории успешно обнулены!')


@bot.message_handler(commands=['today'])
def today(message: types.Message):
    daily = get_daily(message.from_user.id)
    bot.send_message(message.from_user.id, f'Ваши калории за день: {daily}')

    db_request = get_user_stats(message.from_user.id)
    if db_request == (None, None, None, None, None):
        bot.send_message(message.from_user.id,
                         'Вы еще не занесли свои данные! \n'
                         'Для того, чтобы занести свои данные пропишите /addstats')
    else:
        if daily > db_request[-1]:
            bot.send_message(message.from_user.id, f'Вы превысили суточную норму калорий на {daily - db_request[-1]}')
        elif daily == db_request[-1]:
            bot.send_message(message.from_user.id, f'Вы ровно уложились в суточную норму калорий!')
        elif daily < db_request[-1]:
            bot.send_message(message.from_user.id, f'Вам осталось {db_request[-1]-daily} калорий до суточной нормы')


if __name__ == '__main__':
    init_db()
    bot.add_custom_filter(custom_filters.StateFilter(bot))
    bot.infinity_polling()
