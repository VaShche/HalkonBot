import telebot as tg
import configparser
import func

config = configparser.ConfigParser()
config.read('settings.ini')


bot = tg.TeleBot(config['BOT']['token'])
chat_id = config['BOT']['chatid']

data_file_name = 'data.data'
#house_dict = {1:[], 2}
house_dict = func.load_dict_from_file(data_file_name)


def get_admins_ids():
    ids = []
    admins = bot.get_chat_administrators(chat_id)
    for a in admins:
        ids.append(a.user.id)
    return ids

def set_admin(id):
    pass
    '''
    promoteChatMember
    setChatAdministratorCustomTitle
    '''


def add_user(id):
    # дать ссылку для вступления
    # занести в список пользователей неподтверждённых?
    pass

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.send_chat_action(message.from_user.id, 'typing')
    str = '''hhh'''
    bot.reply_to(message, '''Я ещё в разработке...''')

@bot.message_handler()
def debug(message):
    print(message)
    print(message.forward_from.id)

    add_user()
    set_admin()


#@bot.chat_join_request_handler()
def todo1(ChatInviteLink):
    pass
    # promoteChatMember

# while True:
if True:
    try:
        bot.polling(none_stop=True)
    finally:
        print('zzz')

print("hello world")
