import telebot
import pandas as pd
from datetime import datetime, time

TOKEN = "7019876636:AAETMVjAKdp1YLYnwBEs8N2-g-eXSujwtvs"
bot = telebot.TeleBot(TOKEN)


def notify_manager_about_late_opening(sss):
    opening_time = pd.to_datetime(sss[2]).time()
    check_time = pd.to_datetime('7:30:00').time()

    if opening_time > check_time:
        bot.send_message(507500572, "Открыли поздно")


if __name__ == '__main__':
    notify_manager_about_late_opening([1,2,'6:05:19.681022'])
