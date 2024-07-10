import pandas as pd
import requests
import datetime


def main():
    df = pd.read_excel('data/reviews.xlsx')

    addresses = ['Мәңгілік Ел 37', 'Мәңгілік Ел 40', 'Мухамедханова', 'Таха Хусейна 2/1', 'Тәуелсіздік 34']
    opened_addresses = list(df[(df['Дата'] == str(datetime.datetime.now().date())) & (df['Статус'] == 'Отметка')]['Точка'].unique())
    non_opened_addresses = [element for element in addresses if element not in opened_addresses]

    text = None
    if len(non_opened_addresses) == 1:
        text = f"Асемгуль, луна кофе по адресу {', '.join(non_opened_addresses)} не был открыт!"
    if len(non_opened_addresses) > 1:
        text = f"Асемгуль, луна кофе по адресу {', '.join(non_opened_addresses)} не были открыты!"


    url = 'https://zvonok.com/manager/cabapi_external/api/v1/phones/call/'

    # +77011994199
    if text:
        payload = {
            'public_key': '22dc3a76017437d85401e95423154821',
            'phone': '+77088504506',
            'campaign_id': '1124317061',
            'text': text
        }

        response = requests.post(url, data=payload)

        print(response.status_code)
        print(response.json())


if __name__ == '__main__':
    import schedule
    import time

    # Schedule the function to run every day at 14:00
    schedule.every().day.at("14:55").do(main)

    # Infinite loop to continuously check and run scheduled tasks
    while True:
        schedule.run_pending()
        time.sleep(30)
    
