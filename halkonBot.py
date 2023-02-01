import telebot as tg
import configparser
import func
import flats
import text as TEXT


config = configparser.ConfigParser()
config.read('settings.ini')


bot = tg.TeleBot(config['BOT']['token'])
chat_id = config['BOT']['chatid']
data_file_path = config['BOT']['data']

house_dict = func.load_dict_from_file(data_file_path)
if not house_dict:
    house_dict = flats.getHalkonFlatsStruct()
    func.save_dict_to_file(data_file_path, house_dict)
else:
    print(len(flats.getAllHouseResidents(house_dict)))



def get_admins_ids():
    ids = []
    admins = bot.get_chat_administrators(chat_id)
    for a in admins:
        ids.append(a.user.id)
    return ids

def set_admin(tg_id):
    pass
    '''
    promoteChatMember
    setChatAdministratorCustomTitle
    '''


def add_user(tg_id, flat_id):
    print(flat_id)
    # дать ссылку для вступления
    # занести в список пользователей неподтверждённых?
    flats.Flat.findByFlatID(flats.getAllHouseFlats(house_dict), flat_id).addResident(tg_id)

    #func.save_dict_to_file(data_file_path, house_dict)
    print(len(flats.getAllHouseResidents(house_dict)))
    pass


def register(message):
    tg_id = message.from_user.id
    bot.send_chat_action(tg_id, 'typing')
    print(message.text.split(':')[0])
    print(TEXT.register_by_number_confirm.split(':')[0])
    if message.text in [TEXT.register_by_number, TEXT.register_by_number_cancel]:
        print("01")
        bot.send_message(tg_id, TEXT.enter_flat_number)
        bot.register_next_step_handler(message, register_with_number)
        pass
    elif message.text == TEXT.reregister_by_number:
        print("02")
        pass
    elif message.text == TEXT.register_by_entr_and_floor:
        print("03")
        pass
    elif message.text.split(':')[0] == TEXT.register_by_number_confirm.split(':')[0]:
        print("04")
        flat_id = int(message.text.split(': ')[1])
        add_user(tg_id, flat_id)
        start(message)
    print("00")
    pass


def register_with_number(message):
    tg_id = message.from_user.id
    bot.send_chat_action(tg_id, 'typing')
    flat_number = None
    try:
        flat_number = int(message.text.strip())
    except Exception:
        pass
        print("11")
    flat = flats.Flat.findByFlatID(flats.getAllHouseFlats(house_dict), flat_number)
    if flat and flat_number:
        print("12")
        markup = tg.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        item1 = tg.types.KeyboardButton(TEXT.register_by_number_confirm.format(flat.id))
        item2 = tg.types.KeyboardButton(TEXT.register_by_number_cancel)
        markup.add(item1)
        markup.add(item2)
        bot.send_message(tg_id, TEXT.register_by_number_check.format(flat.id), reply_markup=markup)
        bot.register_next_step_handler(message, register)
    else:
        print("13")
        bot.send_message(tg_id, TEXT.register_by_number_reinput)
        bot.register_next_step_handler(message, register_with_number)




@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.send_chat_action(message.from_user.id, 'typing')
    str = '''hhh'''
    bot.reply_to(message, '''Я ещё в разработке...''')

@bot.message_handler()
def start(message):
    tg_id = message.from_user.id
    bot.send_chat_action(tg_id, 'typing')
    print(message)
    #print(message.forward_from.id)
    registered_user = flats.Resident.findByTgID(flats.getAllHouseResidents(house_dict), tg_id)
    if registered_user:
        if registered_user.status_id == 0:
            ''' указал квартиру, но не подтверждён
            '''
            print(0)
            pass
        elif registered_user.status_id >= 1:
            ''' подтверждённый пользователь
            '''
            print(2)
            pass
    else:
        ''' новый пользователь, ранее не регистрировался и не попадал в список
        '''
        print(-1)
        markup = tg.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        item1 = tg.types.KeyboardButton(TEXT.register_by_number)
        item2 = tg.types.KeyboardButton(TEXT.register_by_entr_and_floor)
        markup.add(item1)
        markup.add(item2)
        bot.send_message(tg_id, TEXT.welcome_first, reply_markup=markup)
        bot.register_next_step_handler(message, register)



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
