import pip
#pip.main(['install', 'pytelegrambotapi'])
#pip.main(['install', 'cryptography'])
#from background import keep_alive  # импорт функции для поддержки работоспособности
#keep_alive()  # запускаем flask-сервер в отдельном потоке.
import datetime
today = datetime.date.today()
import logging as log
log.basicConfig(filename='{}_{}_halkon.log'.format(today.year, today.month),
                format='%(asctime)s %(levelname)s %(message)s',
                encoding='utf-8', level=log.INFO)

#import dataMerge
#'''
import halkonBot
from flask import Flask
app = Flask('')


@app.route('/')
def home():
    if halkonBot.bot_check():
        return "I'm alive and bot is checked"
    else:
        print("Problems with bot")


app.run(host='0.0.0.0', port=80)
#'''
