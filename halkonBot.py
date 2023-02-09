import telebot as tg
import func
import flats
import text as TEXT
from constants import *
import settings

config = settings.config
bot = tg.TeleBot(config['BOT']['token'])
chat_id = config['BOT']['chatid']
data_file_path = config['BOT']['data']
chat_link = config['BOT']['invitelink']

house_dict = func.load_dict_from_file(data_file_path, key=config['BOT']['cryptokey'])
if not house_dict:
    house_dict = flats.getHalkonFlatsStruct()
    func.save_dict_to_file(data_file_path, house_dict, key=config['BOT']['cryptokey'])
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


def users_link_markup(tg_id, name):
    markup = tg.types.InlineKeyboardMarkup(row_width=1)
    button = tg.types.InlineKeyboardButton(str(name), url='tg://user?id={}'.format(tg_id))
    markup.add(button)
    return markup


def send_user_info_wrapper(to_chat_id, message_text, markup, parse_mode=None, disable_notification=False):
    print('ddddd', markup.to_dict())
    try:
        bot.send_message(to_chat_id, message_text, parse_mode=parse_mode,
                         reply_markup=markup, disable_notification=disable_notification)
    except Exception:
        if markup:
            new_markup = tg.types.InlineKeyboardMarkup()
            for row in markup.keyboard:
                for button in row:
                    if button.url:
                        message_text += '\n<a href="{}">{}</a> <span class="tg-spoiler">ID {}</span>'.\
                            format(button.url, button.text, button.url.replace('tg://user?id=', ''))
                    else:
                        new_markup.add(button)
        else:
            new_markup = None
        try:
            bot.send_message(to_chat_id, message_text, parse_mode='HTML',
                             reply_markup=new_markup, disable_notification=disable_notification)
        except Exception:
            bot.send_message(config['BOT']['servicechatid'],
                             'EROOR with sending to tg://user?id={}'.format(to_chat_id))
        print('fffff')


def add_user(tg_id, tg_chat_id, flat_id):
    print(tg_id, tg_chat_id, flat_id)
    # дать ссылку для вступления
    # занести в список пользователей неподтверждённых?
    flat = flats.Flat.findByFlatID(flats.getAllHouseFlats(house_dict), flat_id)
    flat.addResident(tg_id, tg_chat_id)
    func.save_dict_to_file(data_file_path, house_dict, key=config['BOT']['cryptokey'])

    markup = users_link_markup(tg_id, 'Квартира №{}'.format(flat_id))
    notify_neighbors = flat.closest_neighbors(house_dict)
    send_user_info_wrapper(config['BOT']['servicechatid'],
                           TEXT.new_neighbor.format(tg_id, flats.Resident.getResidentsIDs(notify_neighbors)),
                           markup, parse_mode='HTML')
    for n in notify_neighbors:
        if n.chat_id != tg_chat_id:
            send_user_info_wrapper(n.chat_id,
                                   TEXT.new_neighbor.format(tg_id, ''),
                                   markup, parse_mode='HTML', disable_notification=True)
    print('Жильцов: {}'.format(len(flats.getAllHouseResidents(house_dict))))
    pass


def del_user(tg_id, del_by_tg_id):
    print(tg_id)
    flat = flats.Flat.findByPerson(flats.getAllHouseFlats(house_dict), tg_id)
    if not flat:
        bot.send_message(tg_id, 'нет такого')
        return None

    flat.removeResident(tg_id)
    func.save_dict_to_file(data_file_path, house_dict, key=config['BOT']['cryptokey'])

    markup = users_link_markup(tg_id, tg_id)
    send_user_info_wrapper(del_by_tg_id, 'Удалён', markup)
    send_user_info_wrapper(config['BOT']['servicechatid'], 'Удалён', markup)
    # TODO уведомить соседей
    '''
    notify_neighbors = flat.closest_neighbors(flats.getAllHouseFlats(house_dict))
    for n in notify_neighbors:
        bot.send_message(n.chat_id, 'Удалён', reply_markup=markup, disable_notification=True)
    '''
    print('Жильцов: {}'.format(len(flats.getAllHouseResidents(house_dict))))
    return tg_id


def confirm_user(another_tg_id, tg_id):  # TODO добавить установку админского статуса
    pass


def get_id_from_text(message_text):
    try:
        res_id = int(message_text.strip())
    except Exception:
        res_id = None
    return res_id


def register_with_number(message):
    tg_id = message.from_user.id
    bot.send_chat_action(tg_id, 'typing')
    flat_number = get_id_from_text(message.text)
    flat = flats.Flat.findByFlatID(flats.getAllHouseFlats(house_dict), flat_number)
    if flat and flat_number:
        print("12")
        markup = tg.types.InlineKeyboardMarkup()
        addButton(markup, REGISTER_ACTION, TEXT.register_by_number_confirm.format(flat.id))
        addButton(markup, REGISTER_ACTION, TEXT.register_by_number_cancel)
        addButton(markup, GENERAL_ACTION, TEXT.main_menu)
        bot.send_message(tg_id, "Ваша квартира №{}, верно? ⤵️".format(flat.id), reply_markup=markup)
    else:
        print("13")
        bot.send_message(tg_id, TEXT.register_by_number_reinput)
        bot.register_next_step_handler(message, register_with_number)


def register_another_user(message):
    tg_id = message.from_user.id
    bot.send_chat_action(tg_id, 'typing')
    from_user_person = flats.Resident.findByTgID(flats.getAllHouseResidents(house_dict), tg_id)
    if not from_user_person.adding_user_id:
        '''Получение ID пользователя
        '''
        if message.forward_from:
            another_tg_id = message.forward_from.id
        else:
            another_tg_id = get_id_from_text(message.text)
        if another_tg_id:
            from_user_person.adding_user_id = another_tg_id
            print(another_tg_id)
            bot.send_message(tg_id, 'Напишите квартиру <a href="tg://user?id={}">человека</a> в ЖК Халькон (числом)'.format(another_tg_id), parse_mode='HTML')
            bot.register_next_step_handler(message, register_another_user)
        else:
            bot.send_message(tg_id, TEXT.unsuccessful)
            start(message)
    elif not from_user_person.adding_user_flat_id:
        '''Получение помещения
        '''
        flat_number = get_id_from_text(message.text)
        if not flat_number and str(tg_id) == str(config['BOT']['adminid']):
            flat_number = message.text
            flat = flats.Flat(flat_number, COMMERCE, 1)
            house_dict.get(COMMERCE).append(flat)

        flat = flats.Flat.findByFlatID(flats.getAllHouseFlats(house_dict), flat_number)
        if flat and flat_number:
            another_tg_id = from_user_person.adding_user_id
            from_user_person.adding_user_id = None
            from_user_person.adding_user_flat_id = None
            add_user(another_tg_id, another_tg_id, flat_number)
            confirm_user(another_tg_id, tg_id)  # TODO добавить проверку на то, что пользователь в чате
            start(message)
        else:
            bot.send_message(tg_id, TEXT.register_by_number_reinput)
            bot.register_next_step_handler(message, register_another_user)


def remove_another_user(message):
    tg_id = message.from_user.id
    bot.send_chat_action(tg_id, 'typing')

    if message.forward_from:
        another_tg_id = message.forward_from.id
    else:
        another_tg_id = get_id_from_text(message.text)
    if another_tg_id:
        del_user(another_tg_id, tg_id)
        start(message)
    else:
        bot.send_message(tg_id, TEXT.unsuccessful)
        start(message)


def register_with_commerce(message):
    tg_id = message.from_user.id
    tg_chat_id = message.chat.id
    bot.send_chat_action(tg_id, 'typing')
    company_name = message.text.strip()
    if flats.Flat.findByFlatID(house_dict.get(COMMERCE), company_name):
        flat = flats.Flat.findByFlatID(house_dict.get(COMMERCE), company_name)
        flat.addResident(tg_id, tg_chat_id)
    else:
        flat = flats.Flat(company_name, COMMERCE, 1)
        flat.addResident(tg_id, tg_chat_id)
        house_dict.get(COMMERCE).append(flat)
    func.save_dict_to_file(data_file_path, house_dict, key=config['BOT']['cryptokey'])
    markup = users_link_markup(tg_id, company_name)
    send_user_info_wrapper(chat_id, TEXT.new_commerce.format(tg_id), markup,
                           parse_mode='HTML', disable_notification=True)
    notify_neighbors = flat.closest_neighbors(house_dict)
    for n in notify_neighbors:
        if n.chat_id != tg_chat_id:
            send_user_info_wrapper(n.chat_id, TEXT.new_commerce.format(tg_id), markup,
                                   parse_mode='HTML', disable_notification=True)
    start(message)


@bot.callback_query_handler(func=lambda call: getCallbackAction(call) == REGISTER_ACTION)
def register(call):
    print(call)
    call_data = getCallbackData(call)
    print(call_data)
    tg_id = call.from_user.id
    tg_chat_id = call.message.chat.id
    bot.send_chat_action(tg_id, 'typing')
    bot.edit_message_reply_markup(tg_id, call.message.id, reply_markup=None)
    if call_data in [TEXT.register_by_number, TEXT.register_by_number_cancel]:
        print("01")
        bot.send_message(tg_id, "Напишите пожалуйста номер Вашей квартиры в ЖК Халькон (числом)")
        bot.register_next_step_handler(call.message, register_with_number)
        pass
    elif call_data == TEXT.reregister_by_number:
        print("02")
        bot.send_message(tg_id, TEXT.wip)  # TODO !!!
        start(call)
        pass
    elif call_data == TEXT.register_by_entr_and_floor:
        print("03")
        bot.send_message(tg_id, TEXT.wip)  # TODO !!!
        start(call)
        pass
    elif call_data == TEXT.register_commerce:
        print("05")
        markup = tg.types.InlineKeyboardMarkup(row_width=1)
        addButton(markup, REGISTER_ACTION, TEXT.register_commerce_im_shure)
        addButton(markup, GENERAL_ACTION, TEXT.main_menu)
        bot.send_message(tg_id, "Вы регистрируетесь как представитель компании, работающей с ЖК Халькон. Верно? ⤵️",
                         reply_markup=markup)
        pass
    elif call_data == TEXT.register_commerce_im_shure:
        print("06")
        bot.send_message(tg_id, "Пожалуйста напишите название Вашей компании без кавычек")
        bot.register_next_step_handler(call.message, register_with_commerce)
        pass
    elif call_data.split(':')[0] == TEXT.register_by_number_confirm.split(':')[0]:
        print("04")
        flat_id = int(call.data.split(': ')[1])
        add_user(tg_id, tg_chat_id, flat_id)
        start(call)
    elif call_data == TEXT.register_approve:
        print("07")
        bot.send_message(tg_id, TEXT.choose_register_way_confirm)
        bot.register_next_step_handler(call.message, register_another_user)
        pass
    elif call_data == TEXT.register_cancel:
        print("08")
        bot.send_message(tg_id, 'Сообщение или ID человека для удаления (для отмены - "нет"):')
        bot.register_next_step_handler(call.message, remove_another_user)
        pass
    else:
        print("WTF register WTF")
        bot.send_message(tg_id, TEXT.error.format('register'))
        start(call)
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
    message_text = "Контакты ⤵️"
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
    send_user_info_wrapper(tg_id, message_text, markup)


def send_advert(message):
    tg_id = message.from_user.id
    bot.send_chat_action(tg_id, 'typing')
    bot.send_message(config['BOT']['servicechatid'], 'Объявление на модерацию для канала:')
    bot.forward_message(config['BOT']['servicechatid'], message.chat.id, message.message_id)
    bot.send_message(tg_id, '✅ Сообщение отправлено на модерацию. После неё оно будет опубликовано в @Halkon_SPb')
    start(message)


def send_idea(message):
    tg_id = message.from_user.id
    bot.send_chat_action(tg_id, 'typing')
    bot.send_message(config['BOT']['adminid'], 'Идея для бота:')
    bot.forward_message(config['BOT']['adminid'], message.chat.id, message.message_id)
    bot.send_message(tg_id, '✅ Сообщение отправлено разработчику. Спасибо!')
    start(message)


@bot.callback_query_handler(func=lambda call: getCallbackAction(call) == ADVERT_ACTION)
def advert(call):
    print(call)
    call_data = getCallbackData(call)
    print(call_data)
    tg_id = call.from_user.id
    if call_data == TEXT.make_post:
        '''объявление на модерацию
        '''
        bot.send_message(tg_id, 'Отправьте пожалуйста объявление одним сообщением. После модерации оно будет перенаправлено в @Halkon_SPb:')
        bot.register_next_step_handler(call.message, send_advert)
    elif call_data == TEXT.todo_for_bot:
        '''обратная связь
        '''
        bot.send_message(tg_id, 'Напишите пожалуйста ваши идеи/предложения для отправки разработчику:')
        bot.register_next_step_handler(call.message, send_idea)
    else:
        print("WTF advert WTF")
        bot.send_message(tg_id, TEXT.error.format('advert'))


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
        # проверка на админство в чате (для присвоения статуса проверенного)  TODO
        if str(registered_user.id) == str(config['BOT']['adminid']):
            registered_user.status_id = 2
        '''
        chat_admins = bot.get_chat_administrators(chat_id)
        for admin in chat_admins:
            if admin.user.id == registered_user.id:
                registered_user.status_id = 2
        '''

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
                    text_for_message = "👋 Вы не указали квартиру. Доступные действия ⤵️"
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
            addButton(markup, REGISTER_ACTION, TEXT.register_approve)
            addButton(markup, REGISTER_ACTION, TEXT.register_cancel)
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
        #addButton(markup, REGISTER_ACTION, TEXT.register_by_entr_and_floor)  # TODO
        addButton(markup, REGISTER_ACTION, TEXT.register_commerce)

    addButton(markup, ADVERT_ACTION, TEXT.make_post)
    addButton(markup, ADVERT_ACTION, TEXT.todo_for_bot)
    bot.send_message(tg_id, text_for_message, reply_markup=markup)


while True:
    try:
        bot.polling(none_stop=True)
    finally:
        print('zzz')
