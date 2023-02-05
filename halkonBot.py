import telebot as tg
import configparser
import func
import flats
import text as TEXT
from constants import *

config = configparser.ConfigParser()
config.read('settings.ini')

bot = tg.TeleBot(config['BOT']['token'])
chat_id = config['BOT']['chatid']
data_file_path = config['BOT']['data']
chat_link = config['BOT']['invitelink']

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


def addButton(markup, action, text, data=None):
    if not data:
        data = text
    button = tg.types.InlineKeyboardButton(text=text, callback_data=actionCallbackData(action, data))
    markup.add(button)


def actionCallbackData(action, data):
    return '{}{}{}'.format(action, SPLITTER, data)


def getCallbackAction(call):
    try:
        return int(call.data.split(SPLITTER)[0])
    except Exception:
        return -1


def getCallbackData(call):
    return call.data.split(SPLITTER)[1]


def add_user(tg_id, tg_chat_id, flat_id):
    print(tg_id, tg_chat_id, flat_id)
    # дать ссылку для вступления
    # занести в список пользователей неподтверждённых?
    flats.Flat.findByFlatID(flats.getAllHouseFlats(house_dict), flat_id).addResident(tg_id, tg_chat_id)
    bot.send_message(chat_id, TEXT.new_neighbor.format(tg_id, flat_id, tg_id),
                     parse_mode='HTML')  # TODO изменить chat_id в конфиге и рассылать только соседям
    func.save_dict_to_file(data_file_path, house_dict)
    print('Жильцов: {}'.format(len(flats.getAllHouseResidents(house_dict))))
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
        addButton(markup, REGISTER_ACTION, TEXT.register_by_number_confirm.format(flat.id))
        addButton(markup, REGISTER_ACTION, TEXT.register_by_number_cancel)
        addButton(markup, GENERAL_ACTION, TEXT.main_menu)
        bot.send_message(tg_id, TEXT.register_by_number_check.format(flat.id), reply_markup=markup)
    else:
        print("13")
        bot.send_message(tg_id, TEXT.register_by_number_reinput)
        bot.register_next_step_handler(message, register_with_number)


def register_with_commerce(message):
    tg_id = message.from_user.id
    tg_chat_id = message.chat.id
    bot.send_chat_action(tg_id, 'typing')
    company_name = message.text.strip()
    if flats.Flat.findByFlatID(house_dict.get(COMMERCE), company_name):
        flats.Flat.findByFlatID(house_dict.get(COMMERCE), company_name).addResident(tg_id, tg_chat_id)
    else:
        flat = flats.Flat(company_name, COMMERCE, 1)
        flat.addResident(tg_id, tg_chat_id)
        house_dict.get(COMMERCE).append(flat)
    bot.send_message(chat_id, TEXT.new_commerce.format(tg_id, company_name, tg_id),
                     parse_mode='HTML', disable_notification=True)
    func.save_dict_to_file(data_file_path, house_dict)
    start(message)


@bot.callback_query_handler(func=lambda call: getCallbackAction(call) == REGISTER_ACTION)
def register(call):
    print(call)
    call_data = getCallbackData(call)
    print(call_data)
    tg_id = call.from_user.id
    tg_chat_id = call.message.chat.id
    bot.send_chat_action(tg_id, 'typing')
    if call_data in [TEXT.register_by_number, TEXT.register_by_number_cancel]:
        print("01")
        bot.edit_message_reply_markup(tg_id, call.message.id, reply_markup=None)
        bot.send_message(tg_id, TEXT.enter_flat_number)
        bot.register_next_step_handler(call.message, register_with_number)
        pass
    elif call_data == TEXT.reregister_by_number:
        print("02")
        bot.send_message(tg_id, TEXT.wip)  # TODO !!!
        pass
    elif call_data == TEXT.register_by_entr_and_floor:
        print("03")
        bot.send_message(tg_id, TEXT.wip)  # TODO !!!
        pass
    elif call_data == TEXT.register_commerce:
        print("05")
        bot.edit_message_reply_markup(tg_id, call.message.id, reply_markup=None)
        markup = tg.types.InlineKeyboardMarkup(row_width=1)
        addButton(markup, REGISTER_ACTION, TEXT.register_commerce_im_shure)
        addButton(markup, GENERAL_ACTION, TEXT.main_menu)
        bot.send_message(tg_id, TEXT.enter_commerce_approve, reply_markup=markup)
        pass
    elif call_data == TEXT.register_commerce_im_shure:
        print("05")
        bot.edit_message_reply_markup(tg_id, call.message.id, reply_markup=None)
        bot.send_message(tg_id, TEXT.enter_commerce)
        bot.register_next_step_handler(call.message, register_with_commerce)
        pass
    elif call_data.split(':')[0] == TEXT.register_by_number_confirm.split(':')[0]:
        print("04")
        bot.edit_message_reply_markup(tg_id, call.message.id, reply_markup=None)
        flat_id = int(call.data.split(': ')[1])
        add_user(tg_id, tg_chat_id, flat_id)
        start(call)
    else:
        print("WTF register WTF")
        bot.send_message(tg_id, TEXT.error.format('register'))
        pass
    print("00")
    pass


@bot.callback_query_handler(func=lambda call: getCallbackAction(call) == NEIGHBORS_ACTION)
def neighbors(call):
    print(call)
    call_data = getCallbackData(call)
    print(call_data)
    tg_id = call.from_user.id
    bot.send_chat_action(tg_id, 'typing')
    flat = flats.Flat.findByPerson(flats.getAllHouseFlats(house_dict), tg_id)
    n_list = []
    if call_data == TEXT.get_floor_neighbors:
        '''контакты соседей по этажу
        '''
        n_list = flat.getFloorNeighbors(house_dict.get(flat.entrance))
    elif call_data == TEXT.get_entrance_neighbors:
        '''контакты соседей по парадной
        '''
        n_list = flat.getAllNeighbors(house_dict.get(flat.entrance))
    elif call_data == TEXT.get_all_neighbors:
        '''контакты всех всех соседей
        '''
        n_list = flats.getAllHouseResidents(house_dict)
    elif call_data == TEXT.get_house_commerce:
        '''контакты коммерции
        '''
        n_list = flat.getAllNeighbors(house_dict.get(COMMERCE))
    elif flat.id and call_data == TEXT.get_up_neighbors:
        '''контакты соседей выше
        '''
        n_list = flat.getUpNeighbors(house_dict.get(flat.entrance))
    elif flat.id and call_data == TEXT.get_down_neighbors:
        '''контакты соседей ниже
        '''
        n_list = flat.getDownNeighbors(house_dict.get(flat.entrance))
    else:
        print("WTF neighbors WTF")
        bot.send_message(tg_id, TEXT.error.format('neighbors'))
    message_text = TEXT.neighbors_list
    bot.edit_message_reply_markup(tg_id, call.message.id, reply_markup=None)
    markup = tg.types.InlineKeyboardMarkup(row_width=1)
    if n_list:
        for i, neighbor in enumerate(n_list):
            text = '{}) 🙊'.format(i + 1)
            if neighbor.flat_id:
                text = '{}) {}'.format(i + 1, neighbor.flat_id)
            button = tg.types.InlineKeyboardButton(text, url='tg://user?id={}'.format(neighbor.id))
            markup.add(button)
    else:
        if call_data not in (TEXT.get_house_commerce, TEXT.get_entrance_neighbors):
            addButton(markup, NEIGHBORS_ACTION, TEXT.get_entrance_neighbors)
        elif call_data != TEXT.get_house_commerce:
            addButton(markup, NEIGHBORS_ACTION, TEXT.get_all_neighbors)
        message_text = TEXT.neighbors_not_found
    addButton(markup, GENERAL_ACTION, TEXT.main_menu)
    bot.send_message(tg_id, message_text, reply_markup=markup)
    pass


@bot.callback_query_handler(func=lambda call: getCallbackAction(call) == ADVERT_ACTION)
def advert(call):
    print(call)
    call_data = getCallbackData(call)
    print(call_data)
    tg_id = call.from_user.id
    bot.send_message(tg_id, TEXT.wip)  # TODO !!!


@bot.callback_query_handler(func=lambda call: getCallbackAction(call) == GENERAL_ACTION)
def general(call):
    print(call)
    call_data = getCallbackData(call)
    print(call_data)
    tg_id = call.from_user.id
    if call_data == TEXT.main_menu:
        '''назад в главное
        '''
        bot.edit_message_reply_markup(tg_id, call.message.id, reply_markup=None)
        start(call)
    elif call_data == TEXT.get_yk_contact:
        '''контакты управляющей
        '''
        bot.send_contact(tg_id, config['MC']['phone'], config['MC']['name'], config['MC']['lastname'])
    elif call_data == TEXT.statistics:
        '''статистика по боту
        '''
        message_text = 'На данный момент зарегестрировались в боте:'
        for entrance in house_dict.keys():
            res_list = []
            flats_counter = 0
            for f in house_dict.get(entrance):
                if f.id and f.residents:
                    flats_counter += 1
                res_list += f.residents
            if res_list and entrance == COMMERCE:
                message_text += '\n{} - {} представителей из {} компаний'.format(entrance, len(res_list), flats_counter)
            elif res_list:
                message_text += '\n{} - {} человек из {} квартир'.format(entrance, len(res_list), flats_counter)
        bot.edit_message_reply_markup(tg_id, call.message.id, reply_markup=None)
        markup = tg.types.InlineKeyboardMarkup(row_width=1)
        addButton(markup, GENERAL_ACTION, TEXT.main_menu)
        bot.send_message(tg_id, message_text, reply_markup=markup)
    else:
        print("WTF general WTF")
        bot.send_message(tg_id, TEXT.error.format('general'))
    pass


@bot.callback_query_handler(func=lambda call: True)
def empty_action(call):
    print(call)
    tg_id = call.from_user.id
    bot.send_chat_action(tg_id, 'typing')
    print("WTF empty_action WTF")
    bot.send_message(tg_id, TEXT.error.format('empty_action'))


@bot.message_handler(commands=['start', 'help'])
def bot_commands_handler(message):
    bot_all_messages_handler(message)


@bot.message_handler(func=lambda message: True,
                     content_types=['audio', 'photo', 'voice', 'video', 'document', 'text', 'location', 'contact',
                                    'sticker'])
def bot_all_messages_handler(message):
    if message.chat.type == 'private':
        start(message)


def start(message):
    tg_id = message.from_user.id
    bot.send_chat_action(tg_id, 'typing')
    print(message)
    # print(message.forward_from.id)
    registered_user = flats.Resident.findByTgID(flats.getAllHouseResidents(house_dict), tg_id)
    markup = tg.types.InlineKeyboardMarkup(row_width=8)
    text_for_message = ''
    if registered_user:
        # проверка на админство в чате (для присвоения статуса проверенного)
        chat_admins = bot.get_chat_administrators(chat_id)
        for admin in chat_admins:
            if admin.user.id == registered_user.id:
                registered_user.status_id = 2

        if registered_user.status_id >= 0:
            ''' зареган, но не подтверждён
            '''
            print(0)

            if flats.Flat.findByPerson(house_dict.get(COMMERCE), tg_id):
                ''' для УК и коммерческой
                '''
                text_for_message = TEXT.welcome_commerce.format(registered_user.flat_id)
            else:
                ''' для зарегестрированных жильцов
                '''
                button = tg.types.InlineKeyboardButton(text=TEXT.close_chat_link, url=chat_link)
                markup.add(button)
                addButton(markup, NEIGHBORS_ACTION, TEXT.get_floor_neighbors)
                if not registered_user.flat_id:
                    ''' указал только номер этажа и парадную
                    '''
                    text_for_message = TEXT.welcome_floor
                    addButton(markup, REGISTER_ACTION, TEXT.reregister_by_number)
                    pass
                else:
                    ''' указал номер квартиры
                    '''
                    text_for_message = TEXT.welcome_flat.format(registered_user.flat_id)
                    addButton(markup, NEIGHBORS_ACTION, TEXT.get_up_neighbors)
                    addButton(markup, NEIGHBORS_ACTION, TEXT.get_down_neighbors)
                    pass
                pass
        if registered_user.status_id >= 1:
            ''' подтверждённый пользователь
            '''
            print(2)
            addButton(markup, REGISTER_ACTION, TEXT.register_approve)  # `TODO
            addButton(markup, REGISTER_ACTION, TEXT.register_cancel)  # `TODO
            pass
        addButton(markup, GENERAL_ACTION, TEXT.statistics)
        addButton(markup, GENERAL_ACTION, TEXT.get_yk_contact)
        addButton(markup, NEIGHBORS_ACTION, TEXT.get_house_commerce)
    else:
        ''' новый пользователь, ранее не регистрировался и не попадал в список
        '''
        print(-1)
        text_for_message = TEXT.welcome_first
        addButton(markup, REGISTER_ACTION, TEXT.register_by_number)
        addButton(markup, REGISTER_ACTION, TEXT.register_by_entr_and_floor)
        addButton(markup, REGISTER_ACTION, TEXT.register_commerce)

    addButton(markup, ADVERT_ACTION, TEXT.make_post)
    addButton(markup, ADVERT_ACTION, TEXT.todo_for_bot)
    bot.send_message(tg_id, text_for_message, reply_markup=markup)


# while True:
if True:
    try:
        bot.polling(none_stop=True)
    finally:
        print('zzz')

print("hello world")
