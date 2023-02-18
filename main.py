import pip
pip.main(['install', 'pytelegrambotapi'])
pip.main(['install', 'cryptography'])
from background import keep_alive  # импорт функции для поддержки работоспособности
keep_alive()  # запускаем flask-сервер в отдельном потоке.

import logging as log
log.basicConfig(filename='halkon.log', format='%(asctime)s %(levelname)s %(message)s',
                encoding='utf-8', level=log.INFO)

#import dataMerge
import halkonBot
