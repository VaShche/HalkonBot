import telebot as tg
import logging as log
import func
import flats
import text as TEXT
from constants import *
import settings

config = settings.config
log.basicConfig(filename='halkon.log', format='%(asctime)s %(levelname)s %(message)s',
                encoding='utf-8', level=log.INFO)
bot = tg.TeleBot(config['BOT']['token'])
chat_id = config['BOT']['chatid']
data_file_path = config['BOT']['data']
chat_link = config['BOT']['invitelink']

house_dict = func.load_dict_from_file(data_file_path, key=config['BOT']['cryptokey'])
if not house_dict:
    house_dict = flats.getHalkonFlatsStruct()
    func.save_dict_to_file(data_file_path, house_dict, key=config['BOT']['cryptokey'])

log.info('Started. Users: %s', len(flats.getAllHouseResidents(house_dict)))


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
    if type(markup) is list:
        markup.append(button)
    else:
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
    markup = tg.types.InlineKeyboardMarkup(row_width=2)
    button = tg.types.InlineKeyboardButton(str(name), url='tg://user?id={}'.format(tg_id))
    markup.add(button)
    return markup


def get_user_name(tg_id):
    user = None
    try:
        chat = bot.get_chat(tg_id)
        if chat.type == 'private':
            user = chat
    except Exception:
        print("no direct chat")
    if not user:
        try:
            chat_member = bot.get_chat_member(config['BOT']['channelid'], tg_id)
            user = chat_member.user
        except Exception:
            pass
    if user:
        user_name = user.first_name
        if user.last_name:
            user_name = '{} {}'.format(user_name, user.last_name)
    else:
        user_name = 'ID: {}'.format(tg_id)
    return user_name


def send_user_info_wrapper(to_chat_id, message_text, markup, parse_mode=None, disable_notification=False):
    try:
        bot.send_message(to_chat_id, message_text, parse_mode=parse_mode,
                         reply_markup=markup, disable_notification=disable_notification)
    except Exception:
        if markup:
            new_markup = tg.types.InlineKeyboardMarkup()
            for row in markup.keyboard:
                row_buttons = []
                for button in row:
                    if button.url:
                        message_text += '\n<a href="{}">{}</a> <span class="tg-spoiler">ID {}</span>'.\
                            format(button.url, button.text, button.url.replace('tg://user?id=', ''))
                    else:
                        row_buttons.append(button)
                new_markup.add(*row_buttons)
        else:
            new_markup = None
        try:
            bot.send_message(to_chat_id, message_text, parse_mode='HTML',
                             reply_markup=new_markup, disable_notification=disable_notification)
        except Exception:
            bot.send_message(config['BOT']['servicechatid'],
                             'EROOR with sending to tg://user?id={}'.format(to_chat_id))
        log.warning('send_user_info_wrapper for : %s', to_chat_id)


def add_user(tg_id, tg_chat_id, flat_id, floor_for_check=None):
    print(tg_id, tg_chat_id, flat_id)
    log.info('add_user %s to %s', tg_id, flat_id)

    flat = flats.Flat.findByFlatID(flats.getAllHouseFlats(house_dict), flat_id)
    if floor_for_check:
        if flat.floor != floor_for_check:
            # перевод интерес пользователя если он наврал с этажём
            log.warning('alert %s != %s', flat.floor, floor_for_check)
            bot.send_message(config['BOT']['servicechatid'], "Следующий Интересующийся не прошёл проверку этажём")
            add_to_other(INTERESTED, tg_id, tg_chat_id)
            bot.send_message(tg_chat_id, '''Ой ой ой, Вы точно ошиблись при нашем знакомстве...
Будем считать, что Вы просто интересуетесь нашим ЖК. Если это не так - нажмите "{}"'''.format(TEXT.todo_for_bot))
            return 0

    flat.addResident(tg_id, tg_chat_id)
    func.save_dict_to_file(data_file_path, house_dict, key=config['BOT']['cryptokey'])

    user_name = get_user_name(tg_id)
    markup = users_link_markup(tg_id, 'Квартира №{}'.format(flat_id))
    notify_neighbors = flat.closest_neighbors(house_dict)
    confirm_buttons = []
    addButton(confirm_buttons, NEWUSER_ACTION, '✅ Верно', 'Верно'+str(tg_id))  # TODO реализовать подтверждение
    addButton(confirm_buttons, NEWUSER_ACTION, '⛔️ Неправда', 'Неправда' + str(tg_id))  # TODO реализовать подтверждение
    markup.add(*confirm_buttons)
    send_user_info_wrapper(config['BOT']['servicechatid'],
                           TEXT.new_neighbor.format(user_name, tg_id, flats.Resident.getResidentsIDs(notify_neighbors)),
                           markup, parse_mode='HTML')
    for n in notify_neighbors:
        if n.chat_id != tg_chat_id:
            send_user_info_wrapper(n.chat_id,
                                   TEXT.new_neighbor.format(user_name, tg_id, ''),
                                   markup, parse_mode='HTML', disable_notification=True)
    print('Жильцов: {}'.format(len(flats.getAllHouseResidents(house_dict))))
    pass


def del_user(tg_id, del_by_tg_id, user_name):
    print(tg_id)
    log.info('del_user %s to %s', tg_id, del_by_tg_id)
    flat = flats.Flat.findByPerson(flats.getAllHouseFlats(house_dict), tg_id)
    if not flat:
        bot.send_message(tg_id, 'нет такого')
        return None

    flat.removeResident(tg_id)
    func.save_dict_to_file(data_file_path, house_dict, key=config['BOT']['cryptokey'])

    markup = users_link_markup(tg_id, user_name)
    send_user_info_wrapper(del_by_tg_id, 'Удалён', markup)
    send_user_info_wrapper(config['BOT']['servicechatid'], 'Удалён пользователем {}'.format(del_by_tg_id), markup)
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
        buttons = []
        floors = flat.get_floors_for_check()
        for floor in floors:
            addButton(buttons, REGISTER_ACTION, TEXT.register_by_number_floor_check.format(flat.id, floor))
        markup = tg.types.InlineKeyboardMarkup(row_width=2)
        markup.add(*buttons)
        addButton(markup, GENERAL_ACTION, TEXT.main_menu)
        bot.send_message(tg_id, TEXT.welcome_register_flat_choose_floor.format(flat.id), reply_markup=markup)
    else:
        print("13")
        bot.send_message(tg_id, TEXT.register_by_number_reinput)
        bot.register_next_step_handler(message, register_with_number)


def get_another_id(message):
    if message.forward_from:
        another_tg_id = message.forward_from.id
        another_user_name = message.forward_from.first_name
    else:
        another_tg_id = get_id_from_text(message.text)
        another_user_name = message.text
    return another_tg_id, another_user_name


def register_another_user(message):
    tg_id = message.from_user.id
    bot.send_chat_action(tg_id, 'typing')
    from_user_person = flats.Resident.findByTgID(flats.getAllHouseResidents(house_dict), tg_id)
    if not from_user_person.adding_user_id:
        '''Получение ID пользователя
        '''
        another_tg_id, another_user_name = get_another_id(message)
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
    another_tg_id, another_user_name = get_another_id(message)
    if another_tg_id:
        del_user(another_tg_id, tg_id, another_user_name)
        start(message)
    else:
        bot.send_message(tg_id, TEXT.unsuccessful)
        start(message)


def ban_user(tg_id, by_tg_id, banned_name=''):
    del_user(tg_id, by_tg_id, banned_name)
    add_to_other(BAN, tg_id, tg_id)


def ban_another_user(message):
    tg_id = message.from_user.id
    bot.send_chat_action(tg_id, 'typing')
    another_tg_id, another_user_name = get_another_id(message)
    if another_tg_id:
        ban_user(tg_id=another_tg_id, by_tg_id=tg_id, banned_name=another_user_name)
    else:
        bot.send_message(tg_id, TEXT.unsuccessful)
        start(message)


def register_with_commerce(message):
    tg_id = message.from_user.id
    tg_chat_id = message.chat.id
    bot.send_chat_action(tg_id, 'typing')
    company_name = message.text.strip()
    flat = flats.Flat.findByFlatID(house_dict.get(COMMERCE), company_name)
    if not flat:
        flat = flats.Flat(company_name, COMMERCE, 1)
        house_dict.get(COMMERCE).append(flat)
    flat.addResident(tg_id, tg_chat_id)
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


def add_to_other(other_type, tg_id, tg_chat_id, user_name=''):
    flat = flats.Flat.findByFlatID(house_dict.get(OTHER, []), other_type)
    if not flat:
        flat = flats.Flat(other_type, OTHER, 1)
        if not house_dict.get(OTHER, None):
            house_dict[OTHER] = []
        house_dict.get(OTHER).append(flat)
    flat.addResident(tg_id, tg_chat_id)
    func.save_dict_to_file(data_file_path, house_dict, key=config['BOT']['cryptokey'])
    markup = users_link_markup(tg_id, '{} {}'.format(other_type, user_name))
    send_user_info_wrapper(config['BOT']['servicechatid'], str(tg_id), markup,
                           parse_mode='HTML', disable_notification=True)


@bot.callback_query_handler(func=lambda call: getCallbackAction(call) == REGISTER_ACTION)
def register(call):
    call_data = getCallbackData(call)
    tg_id = call.from_user.id
    log.info('%s in "register" with "%s"', tg_id, call_data)
    tg_chat_id = call.message.chat.id
    bot.send_chat_action(tg_id, 'typing')
    bot.edit_message_reply_markup(tg_id, call.message.id, reply_markup=None)
    if call_data in [TEXT.register_by_number, TEXT.register_by_number_cancel]:
        print("01")
        bot.send_message(tg_id, TEXT.welcome_register_flat)
        bot.register_next_step_handler(call.message, register_with_number)
        pass
    elif call_data == TEXT.register_start:
        print("001")
        markup = tg.types.InlineKeyboardMarkup()
        addButton(markup, REGISTER_ACTION, TEXT.register_by_number)
        #addButton(markup, REGISTER_ACTION, TEXT.register_by_entr_and_floor)  # TODO
        addButton(markup, REGISTER_ACTION, TEXT.register_commerce)
        addButton(markup, REGISTER_ACTION, TEXT.register_living_close)
        addButton(markup, REGISTER_ACTION, TEXT.register_interested)
        addButton(markup, GENERAL_ACTION, TEXT.main_menu)
        bot.send_message(tg_id, TEXT.welcome_register, reply_markup=markup)
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
        bot.send_message(tg_id, TEXT.welcome_register_company,
                         reply_markup=markup)
        pass
    elif call_data == TEXT.register_commerce_im_shure:
        print("051")
        bot.send_message(tg_id, "Пожалуйста напишите название Вашей компании без кавычек")
        bot.register_next_step_handler(call.message, register_with_commerce)
        pass

    elif call_data.split(':')[0] == TEXT.register_by_number_floor_check.split(':')[0]:
        d = call.data.split(' на ')
        flat_id = d[0].split(': ')[1]
        floor = d[1].split(': ')[1]
        markup = tg.types.InlineKeyboardMarkup()
        addButton(markup, REGISTER_ACTION, TEXT.register_by_number_confirm.format(flat_id, floor))
        addButton(markup, REGISTER_ACTION, TEXT.register_by_number_cancel)
        bot.send_message(tg_id, TEXT.welcome_register_flat_confirm.format(flat_id, floor), reply_markup=markup)
    elif call_data.split(':')[0] == TEXT.register_by_number_confirm.split(':')[0]:
        print("012")
        d = call.data.split(' на ')
        flat_id = d[0].split(': ')[1]
        floor = d[1].split(': ')[1]
        add_user(tg_id, tg_chat_id, get_id_from_text(flat_id), get_id_from_text(floor))
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
    elif call_data == TEXT.register_ban:
        print("085")
        bot.send_message(tg_id, 'Сообщение или ID человека для бана (для отмены - "нет"):')
        bot.register_next_step_handler(call.message, ban_another_user)
        pass
    elif call_data == TEXT.register_living_close:
        print("091")
        markup = tg.types.InlineKeyboardMarkup(row_width=1)
        addButton(markup, REGISTER_ACTION, TEXT.register_living_close_im_shure)
        addButton(markup, GENERAL_ACTION, TEXT.main_menu)
        bot.send_message(tg_id, "Вы указали, что живёте рядом с ЖК Халькон. Верно? ⤵️",
                         reply_markup=markup)
        pass
    elif call_data == TEXT.register_interested:
        print("081")
        markup = tg.types.InlineKeyboardMarkup(row_width=1)
        addButton(markup, REGISTER_ACTION, TEXT.register_interested_im_shure)
        addButton(markup, GENERAL_ACTION, TEXT.main_menu)
        bot.send_message(tg_id,
                         "Вы указали, что не имеете никакого отношения к ЖК Халькон, а только интересуетесь. Верно? ⤵️",
                         reply_markup=markup)
        pass
    elif call_data == TEXT.register_living_close_im_shure:
        print("092")
        add_to_other(CLOSELIVING, tg_id, tg_chat_id)
        start(call)
    elif call_data == TEXT.register_interested_im_shure:
        print("082")
        add_to_other(INTERESTED, tg_id, tg_chat_id)
        start(call)
    else:
        print("WTF register WTF")
        bot.send_message(tg_id, TEXT.error.format('register'))
        start(call)
        pass
    print("00")
    pass


@bot.callback_query_handler(func=lambda call: getCallbackAction(call) == NEWUSER_ACTION)
def new_user(call):
    call_data = getCallbackData(call)
    tg_id = call.from_user.id
    log.info('%s in "new_user" with "%s"', tg_id, call_data)
    bot.send_chat_action(tg_id, 'typing')
    new_markup = None
    if call_data.split(':')[0] == TEXT.register_promote.split(':')[0]:
        print("подтверждение")
    elif call_data.split(':')[0] == TEXT.register_ban.split(':')[0]:
        print("неподтверждение")
        ban_user(tg_id=0, by_tg_id=tg_id)
    else:
        print("WTF new_user WTF")
        bot.send_message(tg_id, TEXT.error.format('new_user'))

    bot.edit_message_reply_markup(tg_id, call.message.id, reply_markup=new_markup)
    if not new_markup:
        start(call)


@bot.callback_query_handler(func=lambda call: getCallbackAction(call) == NEIGHBORS_ACTION)
def neighbors(call):
    call_data = getCallbackData(call)
    tg_id = call.from_user.id
    log.info('%s in "neighbors" with "%s"', tg_id, call_data)
    bot.send_chat_action(tg_id, 'typing')
    bot.edit_message_reply_markup(tg_id, call.message.id, reply_markup=None)
    flat = flats.Flat.findByPerson(flats.getAllHouseFlats(house_dict), tg_id)
    resident = flat.find_resident(tg_id)
    if not flat:
        start(call)
        return 0
    n_list = []
    if call_data == TEXT.get_floor_neighbors:
        '''контакты соседей по этажу
        '''
        n_list = flat.getFloorNeighbors(house_dict.get(flat.entrance))
        if flat.wall_residents:
            n_list += flat.get_wall_neighbors(flats.getAllHouseFlats(house_dict))
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
        n_list = flat.getUpNeighbors(flats.getAllHouseFlats(house_dict))
    elif flat.id and call_data == TEXT.get_down_neighbors:
        '''контакты соседей ниже
        '''
        n_list = flat.getDownNeighbors(flats.getAllHouseFlats(house_dict))
    else:
        print("WTF neighbors WTF")
        bot.send_message(tg_id, TEXT.error.format('neighbors'))
    if resident in n_list:
        n_list.remove(resident)
    message_text = "Контакты ⤵️"
    markup = tg.types.InlineKeyboardMarkup(row_width=2)
    if n_list:
        buttons = []
        for i, neighbor in enumerate(n_list):
            text = '{}) 🙊'.format(i + 1)
            if neighbor.flat_id:
                text = '{}) {}'.format(i + 1, neighbor.flat_id)
            button = tg.types.InlineKeyboardButton(text, url='tg://user?id={}'.format(neighbor.id))
            buttons.append(button)
        markup.add(*buttons)
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


def send_post(message):
    tg_id = message.from_user.id
    bot.send_chat_action(tg_id, 'typing')
    last_name = ''
    if message.from_user.last_name:
        last_name = message.from_user.last_name
    message_text = '''
———
<a href="tg://user?id={}">{} {}</a>'''.format(tg_id, message.from_user.first_name, last_name)
    result = '✅ Сообщение отправлено в @Halvon_SPb'
    if message.content_type == 'text':
        if len(message.text) < 3:
            result = '❌ Сообщение не может быть короче трёх символов.'
        else:
            message_text = message.text + message_text
            bot.send_message(config['BOT']['channelid'], message_text, parse_mode='HTML')
    else:
        print(message.content_type)
        if message.content_type in ['poll', 'sticker']:
            message_text = 'От <a href="tg://user?id={}">{} {}</a>:'.format(tg_id,
                                                                            message.from_user.first_name, last_name)
            bot.send_message(config['BOT']['channelid'], message_text, parse_mode='HTML', disable_notification=True)
            message_text = None
        if message.caption:
            message_text = message.caption + message_text
        bot.copy_message(config['BOT']['channelid'], tg_id, message.id,
                         caption=message_text, parse_mode='HTML', allow_sending_without_reply=True)
    bot.send_message(tg_id, result)
    start(message)


@bot.callback_query_handler(func=lambda call: getCallbackAction(call) == ADVERT_ACTION)
def advert(call):
    call_data = getCallbackData(call)
    tg_id = call.from_user.id
    log.info('%s in "advert" with "%s"', tg_id, call_data)
    bot.edit_message_reply_markup(tg_id, call.message.id, reply_markup=None)
    if call_data == TEXT.make_advert:
        '''объявление на модерацию
        '''
        bot.send_message(tg_id, 'Отправьте пожалуйста объявление одним сообщением. После модерации оно будет перенаправлено в @Halkon_SPb:')
        bot.register_next_step_handler(call.message, send_advert)
    elif call_data == TEXT.todo_for_bot:
        '''обратная связь
        '''
        bot.send_message(tg_id, 'Напишите пожалуйста ваши идеи/предложения для отправки разработчику:')
        bot.register_next_step_handler(call.message, send_idea)
    elif call_data == TEXT.make_post:
        '''сообщение от проверенного в канал
        '''
        bot.send_message(tg_id, 'Напишите пожалуйста ваше сообщение. Оно будет опубликовано от имени канала в @Halkon_SPb. Ваше имя будет добавлено в подпись к сообщению. Для отмены отправьте любую букву.')
        bot.register_next_step_handler(call.message, send_post)
    else:
        print("WTF advert WTF")
        bot.send_message(tg_id, TEXT.error.format('advert'))


@bot.callback_query_handler(func=lambda call: getCallbackAction(call) == GENERAL_ACTION)
def general(call):
    call_data = getCallbackData(call)
    tg_id = call.from_user.id
    log.info('%s in "general" with "%s"', tg_id, call_data)
    if call_data == TEXT.main_menu:
        '''назад в главное
        '''
        bot.edit_message_reply_markup(tg_id, call.message.id, reply_markup=None)
        start(call)
    elif call_data == TEXT.get_yk_contact:
        '''контакты управляющей
        '''
        bot.send_contact(tg_id, config['MC']['phone'], config['MC']['name'], config['MC']['lastname'])
    elif call_data == TEXT.admin_actions:
        '''меню администратора
        '''
        bot.edit_message_reply_markup(tg_id, call.message.id, reply_markup=None)
        markup = tg.types.InlineKeyboardMarkup(row_width=1)
        addButton(markup, REGISTER_ACTION, TEXT.register_approve)
        addButton(markup, REGISTER_ACTION, TEXT.register_cancel)
        addButton(markup, REGISTER_ACTION, TEXT.register_ban)
        addButton(markup, GENERAL_ACTION, TEXT.main_menu)
        bot.send_message(tg_id, 'Доступные действия ⤵️', reply_markup=markup)
    elif call_data == TEXT.get_neighbors:
        '''меню поиска соседей
        '''
        bot.edit_message_reply_markup(tg_id, call.message.id, reply_markup=None)
        markup = tg.types.InlineKeyboardMarkup(row_width=1)
        registered_user_flat = flats.Flat.findByPerson(flats.getAllHouseFlats(house_dict), tg_id)
        if registered_user_flat:
            if registered_user_flat.up_residents:
                addButton(markup, NEIGHBORS_ACTION, TEXT.get_up_neighbors)
            addButton(markup, NEIGHBORS_ACTION, TEXT.get_floor_neighbors)
            if registered_user_flat.down_residents:
                addButton(markup, NEIGHBORS_ACTION, TEXT.get_down_neighbors)
            addButton(markup, NEIGHBORS_ACTION, TEXT.get_entrance_neighbors)
        addButton(markup, GENERAL_ACTION, TEXT.main_menu)
        bot.send_message(tg_id, 'Доступные действия ⤵️', reply_markup=markup)
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
            elif res_list and entrance == OTHER:
                message_text += '\n{} - {} интересующихся или живущих рядом'.format(entrance, len(res_list))
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
    log.info('%s in "start"', tg_id)
    bot.send_message(config['BOT']['adminid'],
                     '<a href="tg://user?id={}">{}</a> в старте 🐉'.format(tg_id, message.from_user.first_name),
                     parse_mode='HTML', disable_notification=True)
    # print(message.forward_from.id)
    registered_user = None
    registered_user_flat = flats.Flat.findByPerson(flats.getAllHouseFlats(house_dict), tg_id)
    if registered_user_flat:
        registered_user = flats.Resident.findByTgID(registered_user_flat.residents, tg_id)
    markup = tg.types.InlineKeyboardMarkup(row_width=8)
    text_for_message = ''
    if registered_user:
        if registered_user_flat.id == BAN:
            '''BAN'''
            markup = None
            bot.send_message(tg_id, TEXT.welcome_ban, reply_markup=markup)
            return 0  # EXIT
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

            if registered_user_flat.entrance == COMMERCE:
                ''' для УК и коммерческой
                '''
                text_for_message = TEXT.welcome_commerce.format(registered_user.flat_id)
            elif registered_user_flat.id == INTERESTED:
                text_for_message = TEXT.welcome_interested
            elif registered_user_flat.id == CLOSELIVING:
                text_for_message = TEXT.welcome_living_close
            elif registered_user_flat.entrance != OTHER:
                ''' для зарегестрированных жильцов
                '''
                button = tg.types.InlineKeyboardButton(text=TEXT.close_chat_link, url=chat_link)
                markup.add(button)
                if not registered_user.flat_id:
                    ''' указал только номер этажа и парадную
                    '''
                    text_for_message = "👋 Вы не указали квартиру. Доступные действия ⤵️"
                    addButton(markup, NEIGHBORS_ACTION, TEXT.get_floor_neighbors)
                    addButton(markup, REGISTER_ACTION, TEXT.reregister_by_number)
                else:
                    ''' указал номер квартиры
                    '''
                    text_for_message = TEXT.welcome_flat.format(registered_user.flat_id)
                    addButton(markup, GENERAL_ACTION, TEXT.get_neighbors)
                pass
        if registered_user.status_id >= 1:
            ''' подтверждённый пользователь
            '''
            print(2)
            addButton(markup, ADVERT_ACTION, TEXT.make_post)  # TODO реализовать отправку
            pass
        if str(registered_user.id) == str(config['BOT']['adminid']):
            print('admin')
            addButton(markup, GENERAL_ACTION, TEXT.admin_actions)
            pass
        if registered_user.flat_id not in (CLOSELIVING, INTERESTED):
            '''кроме не относящихся к дому'''
            addButton(markup, GENERAL_ACTION, TEXT.statistics)
            addButton(markup, GENERAL_ACTION, TEXT.get_yk_contact)
        else:
            pass  # TODO добавить возможность переехать в наш ЖК
        addButton(markup, NEIGHBORS_ACTION, TEXT.get_house_commerce)
    else:
        ''' новый пользователь, ранее не регистрировался и не попадал в список
        '''
        print(-1)
        text_for_message = TEXT.welcome_first
        addButton(markup, REGISTER_ACTION, TEXT.register_start)

    addButton(markup, ADVERT_ACTION, TEXT.make_advert)
    addButton(markup, ADVERT_ACTION, TEXT.todo_for_bot)
    bot.send_message(tg_id, text_for_message, reply_markup=markup)


if True:
    try:
        bot.polling(none_stop=True)
    finally:
        log.error('zzz')
