import telebot
from telebot import types
from datetime import datetime, timedelta
from loguru import logger
import pandas as pd
import requests
from google_sheets import GoogleAPI
from save_data_manually import Saver


# The bot's token. You can access it from @BotFather
TOKEN = "7019876636:AAETMVjAKdp1YLYnwBEs8N2-g-eXSujwtvs"
bot = telebot.TeleBot(TOKEN)

SPREADSHEET_ID = "1zPZ0yC5iqtNpfFtmV_YJx2bEdvRcnukhplb3DQFUTqI"

# Logging parameters
logger.add("logs/logs.log", rotation="1 day", compression="zip")


# Users' answers
user_data = {}
user_reports = {}

# Decorator
def check_restart(f):
    def inner(message):
        if message.text == '/restart':
            restart(message)
        elif message.text == '/start':
            bot.reply_to(message, "Используйте команду '/restart' для того, чтобы начать заново. Команда /start используется для начало опроса")
            restart(message)
        else:
            f(message)
    return inner

# Static markup
def create_static_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add('Сделать отметку')
    markup.add('Сделать замену')

    return markup

def create_yes_no_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add('Да', 'Нет')

    return markup

# If user sends '/start', then the bot starts a survey 
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    user_data[chat_id] = {}

    # logging
    logger.info(f"User-{message.chat.id} opened the chat")

    markup = create_static_markup()
    bot.send_message(message.chat.id, "Добро пожаловать!\n\nСделать отметку - для открытия смены\nСделать замену - для замены", reply_markup=markup)

# If '/restart' was sent, then the bot restarts the survey
def restart(message):
    user_data[message.chat.id] = {}
    send_welcome(message)

# The start of the survey
@bot.message_handler(func=lambda message: message.text == "Сделать отметку" or "Сделать замену")

@check_restart
def question_1(message):
    user_data[message.chat.id] = {}

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for cafe in [
        'Мәңгілік Ел 37',
        'Мәңгілік Ел 40',
        'Мухамедханова',
        'Таха Хусейна 2/1',
        'Тәуелсіздік 34']:

        markup.add(cafe)
    msg = bot.send_message(message.chat.id, "Выберите точку", reply_markup=markup)

    if message.text == 'Сделать отметку':
        user_data[message.chat.id]['Статус'] = 'Отметка'
    else:
        user_data[message.chat.id]['Статус'] = 'Замена'

    bot.register_next_step_handler(msg, question_2)


@check_restart
def question_2(message):
    text = message.text
    if text in ['Мәңгілік Ел 37', 'Мәңгілік Ел 40', 'Мухамедханова', 'Таха Хусейна 2/1', 'Тәуелсіздік 34']:
        current_datetime = datetime.now() + timedelta(hours=5)
        current_date = current_datetime.date()
        current_time = current_datetime.time() 

        user_data[message.chat.id]['Дата'] = str(current_date)
        user_data[message.chat.id]['Время'] = str(current_time)

        user_data[message.chat.id]['Точка'] = message.text
    else:
        msg = bot.send_message(message.chat.id, "Пожалуйста, выберите из списка")
        bot.register_next_step_handler(msg, question_2)
        return    

    markup = create_yes_no_markup()
    msg = bot.send_message(message.chat.id, "Ваше имя")

    bot.register_next_step_handler(msg, question_3)


@check_restart
def question_3(message):
    user_data[message.chat.id]['Имя'] = message.text

    msg = bot.send_message(message.chat.id, "Ваша фамилия")

    bot.register_next_step_handler(msg, finish_survey)


@check_restart
def finish_survey(message):
    user_data[message.chat.id]['Фамилия'] = message.text
    user_data[message.chat.id]['ID'] = message.chat.id

    markup = create_static_markup()

    if user_data[message.chat.id]['Статус'] == 'Отметка':
        msg = bot.send_message(message.chat.id, 'Вы отметились!', reply_markup=markup)
    else:
        msg = bot.send_message(message.chat.id, 'Вы заменились!', reply_markup=markup)

    # Saving data to google sheets
    logger.info("Trying to save user data to the google sheets...")
    save_survey_data_to_google_sheets(message.chat.id) 

    
def save_survey_data_to_google_sheets(chat_id):
    from collections import OrderedDict

    desired_order = ['Дата', 'Время', 'Точка', 'Статус', 'Имя', 'Фамилия', 'ID']
    ordered_dict = OrderedDict((key, user_data[chat_id][key]) for key in desired_order)

    values = [list(ordered_dict.values())]

    Saver().save_user_data_manually(values)

    if not GoogleAPI().check_token_expicicy_and_refresh():
        logger.info("Token is valid")
    else:
        logger.error("Failed to refresh the token while saving user data to google sheets")
        return

    try: 
        GoogleAPI().append_values(
            spreadsheet_id=SPREADSHEET_ID,
            range_name='A:Z',
            value_input_option="USER_ENTERED",
            values=values,
        ) # type: ignore
    except:
        logger.error("Failed to save the data to google sheets!")


    if user_data[chat_id]['Статус'] == 'Отметка':
        notify_manager_about_late_opening(user_data[chat_id])


def notify_manager_about_late_opening(values):
    opening_time = pd.to_datetime(values['Время']).time()
    address = values['Точка']
    name = values['Имя']
    surname = values['Фамилия']

    check_time = pd.to_datetime('7:30:00').time()

    # 6655437078
    if opening_time > check_time:
        bot.send_message(6655437078, f"!!!ОПОЗДАНИЕ!!!\n\nБариста: {name} {surname}\nТочка: {address}\nВремя: {str(opening_time)[:8]}")


# --------------------START--------------------
import os, sys
from requests.exceptions import ConnectionError, ReadTimeout

try:
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
except (ConnectionError, ReadTimeout) as e:
    sys.stdout.flush()
    os.execv(sys.argv[0], sys.argv)
else:
    bot.infinity_polling(timeout=10, long_polling_timeout=5)