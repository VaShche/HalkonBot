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


def addButton(markup, text, data=None):
    if not data:
        data = text
    button = tg.types.InlineKeyboardButton(text=text, callback_data=data)
    markup.add(button)


def add_user(tg_id, flat_id):
    print(flat_id)
    # дать ссылку для вступления
    # занести в список пользователей неподтверждённых?
    flats.Flat.findByFlatID(flats.getAllHouseFlats(house_dict), flat_id).addResident(tg_id)

    #func.save_dict_to_file(data_file_path, house_dict)
    print('Жильцов: {}'.format(len(flats.getAllHouseResidents(house_dict))))
    pass


@bot.callback_query_handler(func=lambda call: True)
def register(call):
    print(call)
    tg_id = call.from_user.id
    bot.send_chat_action(tg_id, 'typing')
    if call.data in [TEXT.register_by_number, TEXT.register_by_number_cancel]:
        print("01")
        bot.edit_message_reply_markup(tg_id, call.message.id, reply_markup=None)
        bot.send_message(tg_id, TEXT.enter_flat_number)
        bot.register_next_step_handler(call.message, register_with_number)
        pass
    elif call.data == TEXT.reregister_by_number:
        print("02")
        bot.send_message(tg_id, TEXT.wip)
        pass
    elif call.data == TEXT.register_by_entr_and_floor:
        print("03")
        bot.send_message(tg_id, TEXT.wip)
        pass
    elif call.data.split(':')[0] == TEXT.register_by_number_confirm.split(':')[0]:
        print("04")
        bot.edit_message_reply_markup(tg_id, call.message.id, reply_markup=None)
        flat_id = int(call.data.split(': ')[1])
        add_user(tg_id, flat_id)
        start(call)
    else:
        print("WTF WTF WTF")
        bot.send_message(tg_id, TEXT.error)
        pass
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
        markup = tg.types.InlineKeyboardMarkup()
        addButton(markup, TEXT.register_by_number_confirm.format(flat.id))
        addButton(markup, TEXT.register_by_number_cancel)
        bot.send_message(tg_id, TEXT.register_by_number_check.format(flat.id), reply_markup=markup)
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
    markup = tg.types.InlineKeyboardMarkup()
    text_for_message = ''
    if registered_user:
        if not registered_user.flat_id:
            ''' указал только номер этажа и парадную
            '''
            addButton(markup, TEXT.reregister_by_number)
            pass
        else:
            ''' указал номер квартиры
            '''
            pass
        if registered_user.status_id == 0:
            ''' указал квартиру, но не подтверждён
            '''
            print(0)
            pass
        if registered_user.status_id >= 1:
            ''' подтверждённый пользователь
            '''
            print(2)
            pass
    else:
        ''' новый пользователь, ранее не регистрировался и не попадал в список
        '''
        print(-1)
        text_for_message = TEXT.welcome_first
        addButton(markup, TEXT.register_by_number)
        addButton(markup, TEXT.register_by_entr_and_floor)

    addButton(markup, TEXT.make_post)
    bot.send_message(tg_id, text_for_message, reply_markup=markup)



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
