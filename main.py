import pip
pip.main(['install', 'pytelegrambotapi'])
pip.main(['install', 'cryptography'])
from background import keep_alive  # импорт функции для поддержки работоспособности
keep_alive()  # запускаем flask-сервер в отдельном потоке.

import halkonBot
