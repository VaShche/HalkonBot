import telebot as tg
import logging as log
import threading
import datetime
import func
import flats
import text as TEXT
from constants import *
import tg_func as tgf
import settings


CONFIG = settings.config
BOT = tg.TeleBot(CONFIG['BOT']['token'])
CHAT_ID = CONFIG['BOT']['chatid']
CHANNEL_TG_ID = CONFIG['BOT']['channelid']
DATA_FILE_PATH = CONFIG['BOT']['data']
CHAT_LINK = CONFIG['BOT']['invitelink']


TODAY = datetime.date.today()
HOUSE_DICT = func.load_dict_from_file(DATA_FILE_PATH, key=CONFIG['BOT']['cryptokey'])
if not HOUSE_DICT:
    HOUSE_DICT = flats.getHalkonFlatsStruct()
    func.save_dict_to_file(DATA_FILE_PATH, HOUSE_DICT, key=CONFIG['BOT']['cryptokey'])
else:  # BACKUP
    func.save_dict_to_file('{}_{}_{}'.format(TODAY.year, TODAY.month, DATA_FILE_PATH),
                           HOUSE_DICT, key=CONFIG['BOT']['cryptokey'])
log.info('Started. Users: %s', len(flats.getAllHouseResidents(HOUSE_DICT)))


def add_user(tg_id, tg_chat_id, flat_id, floor_for_check=None):
    print(tg_id, tg_chat_id, flat_id)
    log.info('add_user %s to %s', tg_id, flat_id)

    flat = flats.Flat.findByFlatID(flats.getAllHouseFlats(HOUSE_DICT), flat_id)
    if floor_for_check:
        if flat.floor != floor_for_check:
            # перевод интерес пользователя если он наврал с этажём
            log.warning('alert %s != %s', flat.floor, floor_for_check)
            BOT.send_message(CONFIG['BOT']['servicechatid'], "Следующий Интересующийся не прошёл проверку этажём")
            add_to_other(INTERESTED, tg_id, tg_chat_id)
            BOT.send_message(tg_chat_id, '''Ой ой ой, Вы точно ошиблись при нашем знакомстве...
Будем считать, что Вы просто интересуетесь нашим ЖК. Если это не так - нажмите "{}"'''.format(TEXT.todo_for_bot))
            return 0

    flat.addResident(tg_id, tg_chat_id)
    func.save_dict_to_file(DATA_FILE_PATH, HOUSE_DICT, key=CONFIG['BOT']['cryptokey'])

    user_name = tgf.get_user_name(BOT, CHANNEL_TG_ID, tg_id)
    markup = tgf.users_link_markup(tg_id, 'Квартира №{}'.format(flat_id))
    notify_neighbors = flat.closest_neighbors(HOUSE_DICT)
    confirm_buttons = []
    tgf.addButton(confirm_buttons, NEWUSER_ACTION, TEXT.newuser_confirm, '{}:{}'.format(TEXT.newuser_confirm, tg_id))
    tgf.addButton(confirm_buttons, NEWUSER_ACTION, TEXT.newuser_ban, '{}:{}'.format(TEXT.newuser_ban, tg_id))
    markup.add(*confirm_buttons)
    tgf.send_user_info_wrapper(BOT, CONFIG['BOT']['servicechatid'],
                               TEXT.new_neighbor.format(user_name, tg_id,
                                                        flats.Resident.getResidentsIDs(notify_neighbors)),
                               markup, parse_mode='HTML')
    for n in notify_neighbors:
        if n.chat_id != tg_chat_id:
            tgf.send_user_info_wrapper(BOT, n.chat_id,
                                       TEXT.new_neighbor.format(user_name, tg_id, ''),
                                       markup, parse_mode='HTML', disable_notification=True,
                                       service_chat_id=CONFIG['BOT']['servicechatid'])
    print('Жильцов: {}'.format(len(flats.getAllHouseResidents(HOUSE_DICT))))
    pass


def del_user(tg_id, del_by_tg_id, user_name):
    print(tg_id)
    log.info('del_user %s to %s', tg_id, del_by_tg_id)
    flat = flats.Flat.findByPerson(flats.getAllHouseFlats(HOUSE_DICT), tg_id)
    if not flat:
        BOT.send_message(tg_id, 'нет такого')
        return None

    flat.removeResident(tg_id)
    func.save_dict_to_file(DATA_FILE_PATH, HOUSE_DICT, key=CONFIG['BOT']['cryptokey'])

    markup = tgf.users_link_markup(tg_id, user_name)
    tgf.send_user_info_wrapper(BOT, del_by_tg_id, 'Удалён', markup, service_chat_id=CONFIG['BOT']['servicechatid'])
    tgf.send_user_info_wrapper(BOT, CONFIG['BOT']['servicechatid'], 'Удалён пользователем {}'.format(del_by_tg_id), markup)
    # TODO уведомить соседей при удалении?
    '''
    notify_neighbors = flat.closest_neighbors(flats.getAllHouseFlats(house_dict))
    for n in notify_neighbors:
        bot.send_message(n.chat_id, 'Удалён', reply_markup=markup, disable_notification=True)
    '''
    print('Жильцов: {}'.format(len(flats.getAllHouseResidents(HOUSE_DICT))))
    return tg_id


def register_with_number(message):
    tg_id = message.from_user.id
    BOT.send_chat_action(tg_id, 'typing')
    flat_number = tgf.get_id_from_text(message.text)
    flat = flats.Flat.findByFlatID(flats.getAllHouseFlats(HOUSE_DICT), flat_number)
    if flat and flat_number:
        print("12")
        buttons = []
        floors = flat.get_floors_for_check()
        for floor in floors:
            tgf.addButton(buttons, REGISTER_ACTION, TEXT.register_by_number_floor_check.format(flat.id, floor))
        markup = tg.types.InlineKeyboardMarkup(row_width=2)
        markup.add(*buttons)
        tgf.addButton(markup, GENERAL_ACTION, TEXT.main_menu)
        BOT.send_message(tg_id, TEXT.welcome_register_flat_choose_floor.format(flat.id), reply_markup=markup)
    else:
        print("13")
        BOT.send_message(tg_id, TEXT.register_by_number_reinput)
        BOT.register_next_step_handler(message, register_with_number)


def register_another_user(message):
    tg_id = message.from_user.id
    BOT.send_chat_action(tg_id, 'typing')
    from_user_person = flats.Resident.findByTgID(flats.getAllHouseResidents(HOUSE_DICT), tg_id)
    if not from_user_person.adding_user_id:
        '''Получение ID пользователя
        '''
        another_tg_id, another_user_name = tgf.get_another_id(message)
        if another_tg_id:
            from_user_person.adding_user_id = another_tg_id
            print(another_tg_id)
            BOT.send_message(tg_id, 'Напишите квартиру <a href="tg://user?id={}">человека</a> в ЖК Халькон (числом)'.format(another_tg_id), parse_mode='HTML')
            BOT.register_next_step_handler(message, register_another_user)
        else:
            BOT.send_message(tg_id, TEXT.unsuccessful)
            start(message)
    elif not from_user_person.adding_user_flat_id:
        '''Получение помещения
        '''
        flat_number = tgf.get_id_from_text(message.text)
        if not flat_number and str(tg_id) == str(CONFIG['BOT']['adminid']):
            flat_number = message.text
            flat = flats.Flat(flat_number, COMMERCE, 1)
            HOUSE_DICT.get(COMMERCE).append(flat)

        flat = flats.Flat.findByFlatID(flats.getAllHouseFlats(HOUSE_DICT), flat_number)
        if flat and flat_number:
            another_tg_id = from_user_person.adding_user_id
            from_user_person.adding_user_id = None
            from_user_person.adding_user_flat_id = None
            add_user(another_tg_id, another_tg_id, flat_number)
            start(message)
        else:
            BOT.send_message(tg_id, TEXT.register_by_number_reinput)
            BOT.register_next_step_handler(message, register_another_user)


def remove_another_user(message):
    tg_id = message.from_user.id
    BOT.send_chat_action(tg_id, 'typing')
    another_tg_id, another_user_name = tgf.get_another_id(message)
    if another_tg_id:
        del_user(another_tg_id, tg_id, another_user_name)
        start(message)
    else:
        BOT.send_message(tg_id, TEXT.unsuccessful)
        start(message)


def ban_user(tg_id, by_tg_id):
    banned_name = tgf.get_user_name(BOT, CHANNEL_TG_ID, tg_id)
    del_user(tg_id, by_tg_id, banned_name)
    add_to_other(BAN, tg_id, tg_id)
    try:
        BOT.promote_chat_member(CHAT_ID, tg_id, can_change_info=False, can_post_messages=False, can_edit_messages=False,
                                can_delete_messages=False, can_invite_users=False, can_restrict_members=False,
                                can_pin_messages=False, can_manage_chat=False, can_promote_members=False,
                                can_manage_video_chats=False, can_manage_voice_chats=False, can_manage_topics=False)
    except Exception:
        pass


def promote_user(tg_id, by_tg_id, new_status=2):
    new_resident = flats.Resident.findByTgID(flats.getAllHouseResidents(HOUSE_DICT), tg_id)
    BOT.send_message(CONFIG['BOT']['servicechatid'],
                     'Пользователь {} подтвердил {} c ID {}'.format(tgf.get_user_name(BOT, CHANNEL_TG_ID, by_tg_id),
                                                                    tgf.get_user_name(BOT, CHANNEL_TG_ID, new_resident.id),
                                                                    new_resident.id))
    if not new_resident:
        log.error('user not exist in promote_user')
        BOT.send_message(CONFIG['BOT']['servicechatid'], 'error')
        return 0
    new_resident.setStatus(new_status, by_tg_id)
    func.save_dict_to_file(DATA_FILE_PATH, HOUSE_DICT, key=CONFIG['BOT']['cryptokey'])
    tgf.set_admin_in_chat(BOT, new_resident, CHAT_ID)
    BOT.send_message(by_tg_id, "Спасибо!")
    BOT.send_message(new_resident.id,
                     'Получено подтверждение от {}. Добро пожаловать :)'.format(tgf.get_user_name(BOT, CHANNEL_TG_ID,
                                                                                                  by_tg_id)))


def ban_another_user(message):
    tg_id = message.from_user.id
    BOT.send_chat_action(tg_id, 'typing')
    another_tg_id, another_user_name = tgf.get_another_id(message)
    if another_tg_id:
        ban_user(tg_id=another_tg_id, by_tg_id=tg_id)
    else:
        BOT.send_message(tg_id, TEXT.unsuccessful)
        start(message)


def register_with_commerce(message):
    tg_id = message.from_user.id
    tg_chat_id = message.chat.id
    BOT.send_chat_action(tg_id, 'typing')
    company_name = message.text.strip()
    flat = flats.Flat.findByFlatID(HOUSE_DICT.get(COMMERCE), company_name)
    if not flat:
        flat = flats.Flat(company_name, COMMERCE, 1)
        HOUSE_DICT.get(COMMERCE).append(flat)
    flat.addResident(tg_id, tg_chat_id)
    func.save_dict_to_file(DATA_FILE_PATH, HOUSE_DICT, key=CONFIG['BOT']['cryptokey'])
    markup = tgf.users_link_markup(tg_id, company_name)
    tgf.send_user_info_wrapper(BOT, CHAT_ID, TEXT.new_commerce.format(tg_id), markup,
                               parse_mode='HTML', disable_notification=True,
                               service_chat_id=CONFIG['BOT']['servicechatid'])
    notify_neighbors = flat.closest_neighbors(HOUSE_DICT)
    for n in notify_neighbors:
        if n.chat_id != tg_chat_id:
            tgf.send_user_info_wrapper(BOT, n.chat_id, TEXT.new_commerce.format(tg_id), markup,
                                       parse_mode='HTML', disable_notification=True,
                                       service_chat_id=CONFIG['BOT']['servicechatid'])
    start(message)


def add_to_other(other_type, tg_id, tg_chat_id, user_name=''):
    flat = flats.Flat.findByFlatID(HOUSE_DICT.get(OTHER, []), other_type)
    if not flat:
        flat = flats.Flat(other_type, OTHER, 1)
        if not HOUSE_DICT.get(OTHER, None):
            HOUSE_DICT[OTHER] = []
        HOUSE_DICT.get(OTHER).append(flat)
    flat.addResident(tg_id, tg_chat_id)
    func.save_dict_to_file(DATA_FILE_PATH, HOUSE_DICT, key=CONFIG['BOT']['cryptokey'])
    markup = tgf.users_link_markup(tg_id, '{} {}'.format(other_type, user_name))
    tgf.send_user_info_wrapper(BOT, CONFIG['BOT']['servicechatid'], str(tg_id), markup,
                               parse_mode='HTML', disable_notification=True)


@BOT.callback_query_handler(func=lambda call: tgf.getCallbackAction(call) == REGISTER_ACTION)
def register(call):
    call_data = tgf.getCallbackData(call)
    tg_id = call.from_user.id
    log.info('%s in "register" with "%s"', tg_id, call_data)
    tg_chat_id = call.message.chat.id
    BOT.send_chat_action(tg_id, 'typing')
    BOT.edit_message_reply_markup(tg_id, call.message.id, reply_markup=None)
    if call_data in [TEXT.register_by_number, TEXT.register_by_number_cancel]:
        print("01")
        BOT.send_message(tg_id, TEXT.welcome_register_flat)
        BOT.register_next_step_handler(call.message, register_with_number)
        pass
    elif call_data == TEXT.register_start:
        print("001")
        markup = tg.types.InlineKeyboardMarkup()
        tgf.addButton(markup, REGISTER_ACTION, TEXT.register_by_number)
        #addButton(markup, REGISTER_ACTION, TEXT.register_by_entr_and_floor)  # TODO
        tgf.addButton(markup, REGISTER_ACTION, TEXT.register_commerce)
        tgf.addButton(markup, REGISTER_ACTION, TEXT.register_living_close)
        tgf.addButton(markup, REGISTER_ACTION, TEXT.register_interested)
        tgf.addButton(markup, GENERAL_ACTION, TEXT.main_menu)
        BOT.send_message(tg_id, TEXT.welcome_register, reply_markup=markup)
    elif call_data == TEXT.reregister_by_number:
        print("02")
        BOT.send_message(tg_id, TEXT.wip)  # TODO !!!
        start(call)
        pass
    elif call_data == TEXT.register_by_entr_and_floor:
        print("03")
        BOT.send_message(tg_id, TEXT.wip)  # TODO !!!
        start(call)
        pass
    elif call_data == TEXT.register_commerce:
        print("05")
        markup = tg.types.InlineKeyboardMarkup(row_width=1)
        tgf.addButton(markup, REGISTER_ACTION, TEXT.register_commerce_im_shure)
        tgf.addButton(markup, GENERAL_ACTION, TEXT.main_menu)
        BOT.send_message(tg_id, TEXT.welcome_register_company,
                         reply_markup=markup)
        pass
    elif call_data == TEXT.register_commerce_im_shure:
        print("051")
        BOT.send_message(tg_id, "Пожалуйста напишите название Вашей компании без кавычек")
        BOT.register_next_step_handler(call.message, register_with_commerce)
        pass

    elif call_data.split(':')[0] == TEXT.register_by_number_floor_check.split(':')[0]:
        d = call.data.split(' на ')
        flat_id = d[0].split(': ')[1]
        floor = d[1].split(': ')[1]
        markup = tg.types.InlineKeyboardMarkup()
        tgf.addButton(markup, REGISTER_ACTION, TEXT.register_by_number_confirm.format(flat_id, floor))
        tgf.addButton(markup, REGISTER_ACTION, TEXT.register_by_number_cancel)
        BOT.send_message(tg_id, TEXT.welcome_register_flat_confirm.format(flat_id, floor), reply_markup=markup)
    elif call_data.split(':')[0] == TEXT.register_by_number_confirm.split(':')[0]:
        print("012")
        d = call.data.split(' на ')
        flat_id = d[0].split(': ')[1]
        floor = d[1].split(': ')[1]
        add_user(tg_id, tg_chat_id, tgf.get_id_from_text(flat_id), tgf.get_id_from_text(floor))
        start(call)
    elif call_data == TEXT.register_approve:
        print("07")
        BOT.send_message(tg_id, TEXT.choose_register_way_confirm)
        BOT.register_next_step_handler(call.message, register_another_user)
        pass
    elif call_data == TEXT.register_cancel:
        print("08")
        BOT.send_message(tg_id, 'Сообщение или ID человека для удаления (для отмены - "нет"):')
        BOT.register_next_step_handler(call.message, remove_another_user)
        pass
    elif call_data == TEXT.register_ban:
        print("085")
        BOT.send_message(tg_id, 'Сообщение или ID человека для бана (для отмены - "нет"):')
        BOT.register_next_step_handler(call.message, ban_another_user)
        pass
    elif call_data == TEXT.register_living_close:
        print("091")
        markup = tg.types.InlineKeyboardMarkup(row_width=1)
        tgf.addButton(markup, REGISTER_ACTION, TEXT.register_living_close_im_shure)
        tgf.addButton(markup, GENERAL_ACTION, TEXT.main_menu)
        BOT.send_message(tg_id, "Вы указали, что живёте рядом с ЖК Халькон. Верно? ⤵️",
                         reply_markup=markup)
        pass
    elif call_data == TEXT.register_interested:
        print("081")
        markup = tg.types.InlineKeyboardMarkup(row_width=1)
        tgf.addButton(markup, REGISTER_ACTION, TEXT.register_interested_im_shure)
        tgf.addButton(markup, GENERAL_ACTION, TEXT.main_menu)
        BOT.send_message(tg_id,
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
        BOT.send_message(tg_id, TEXT.error.format('register'))
        start(call)
        pass
    print("00")
    pass


@BOT.callback_query_handler(func=lambda call: tgf.getCallbackAction(call) == NEWUSER_ACTION)
def new_user(call):
    call_data = tgf.getCallbackData(call)
    tg_id = call.from_user.id
    message_chat_id = call.message.chat.id
    log.info('%s in "new_user" with "%s"', tg_id, call_data)
    BOT.send_chat_action(tg_id, 'typing')
    call_data_command = call_data.split(':')[0]
    user_tg_id = int(call_data.split(':')[1])
    old_markup = call.message.reply_markup
    new_markup = tg.types.InlineKeyboardMarkup()
    if len(old_markup.keyboard) > 1:
        new_markup.add(*old_markup.keyboard[0])
    buttons = []
    registered_user = flats.Resident.findByTgID(flats.getAllHouseResidents(HOUSE_DICT), user_tg_id)
    if registered_user:
        if registered_user.flat_id == BAN or registered_user.status_id > 0:
            new_markup = None
            message_text = 'Спасибо! Кто-то из соседей уже подтвердил этого человека'
            if registered_user.flat_id == BAN:
                message_text = 'Спасибо! Кто-то из соседей уже заблокировал этого человека'
            BOT.send_message(message_chat_id, message_text)
        elif tg_id not in tgf.get_admins_ids(BOT, CHAT_ID):
            new_markup = old_markup
            BOT.send_message(message_chat_id,
                             'Для подтверждения соседей у вас должно быть указано "собственник в ЖК" в закрытом чате.')
        elif call_data_command == TEXT.newuser_confirm:
            BOT.send_message(message_chat_id, 'Вы знакомы и можете подтвердить, что это действительно новый сосед?')
            tgf.addButton(buttons, NEWUSER_ACTION, TEXT.newuser_cancel,
                          '{}:{}'.format(TEXT.newuser_cancel, user_tg_id))
            tgf.addButton(buttons, NEWUSER_ACTION, TEXT.newuser_confirm_shure,
                          '{}:{}'.format(TEXT.newuser_confirm_shure, user_tg_id))
            new_markup.add(*buttons)
        elif call_data_command == TEXT.newuser_ban:
            BOT.send_message(message_chat_id,
                             'Вы уверены, что этот человек на самом деле не имеет отношения к указанной квартире и его необходимо заблокировать?')
            tgf.addButton(buttons, NEWUSER_ACTION, TEXT.newuser_cancel,
                          '{}:{}'.format(TEXT.newuser_cancel, user_tg_id))
            tgf.addButton(buttons, NEWUSER_ACTION, TEXT.newuser_ban_shure,
                          '{}:{}'.format(TEXT.newuser_ban_shure, user_tg_id))
            new_markup.add(*buttons)
        elif call_data_command == TEXT.newuser_cancel:
            tgf.addButton(buttons, NEWUSER_ACTION, TEXT.newuser_confirm,
                          '{}:{}'.format(TEXT.newuser_confirm, user_tg_id))
            tgf.addButton(buttons, NEWUSER_ACTION, TEXT.newuser_ban,
                          '{}:{}'.format(TEXT.newuser_ban, user_tg_id))
            new_markup.add(*buttons)
        elif call_data_command == TEXT.newuser_confirm_shure:
            print("подтверждение уверен")
            promote_user(tg_id=user_tg_id, by_tg_id=tg_id)
            start(call)
        elif call_data_command == TEXT.newuser_ban_shure:
            print("неподтверждение уверен")
            ban_user(tg_id=user_tg_id, by_tg_id=tg_id)
            start(call)
        else:
            print("WTF new_user WTF")
            new_markup = old_markup
            BOT.send_message(tg_id, TEXT.error.format('new_user'))
    else:
        # пользователя видимо удалили
        new_markup = None
        BOT.send_message(tg_id, TEXT.error.format('new_user not exist'))

    BOT.edit_message_reply_markup(message_chat_id, call.message.id, reply_markup=new_markup)


@BOT.callback_query_handler(func=lambda call: tgf.getCallbackAction(call) == NEIGHBORS_ACTION)
def neighbors(call):
    call_data = tgf.getCallbackData(call)
    tg_id = call.from_user.id
    log.info('%s in "neighbors" with "%s"', tg_id, call_data)
    BOT.send_chat_action(tg_id, 'typing')
    BOT.edit_message_reply_markup(tg_id, call.message.id, reply_markup=None)
    flat = flats.Flat.findByPerson(flats.getAllHouseFlats(HOUSE_DICT), tg_id)
    resident = flat.find_resident(tg_id)
    if not flat:
        start(call)
        return 0
    n_list = []
    if call_data == TEXT.get_floor_neighbors:
        '''контакты соседей по этажу
        '''
        n_list = flat.getFloorNeighbors(HOUSE_DICT.get(flat.entrance))
        if flat.wall_residents:
            n_list += flat.get_wall_neighbors(flats.getAllHouseFlats(HOUSE_DICT))
    elif call_data == TEXT.get_entrance_neighbors:
        '''контакты соседей по парадной
        '''
        n_list = flat.getAllNeighbors(HOUSE_DICT.get(flat.entrance))
    elif call_data == TEXT.get_all_neighbors:
        '''контакты всех всех соседей
        '''
        n_list = flats.getAllHouseResidents(HOUSE_DICT)
    elif call_data == TEXT.get_house_commerce:
        '''контакты коммерции
        '''
        n_list = flat.getAllNeighbors(HOUSE_DICT.get(COMMERCE))
    elif flat.id and call_data == TEXT.get_up_neighbors:
        '''контакты соседей выше
        '''
        n_list = flat.getUpNeighbors(flats.getAllHouseFlats(HOUSE_DICT))
    elif flat.id and call_data == TEXT.get_down_neighbors:
        '''контакты соседей ниже
        '''
        n_list = flat.getDownNeighbors(flats.getAllHouseFlats(HOUSE_DICT))
    else:
        print("WTF neighbors WTF")
        BOT.send_message(tg_id, TEXT.error.format('neighbors'))
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
            tgf.addButton(markup, NEIGHBORS_ACTION, TEXT.get_entrance_neighbors)
        elif call_data != TEXT.get_house_commerce:
            tgf.addButton(markup, NEIGHBORS_ACTION, TEXT.get_all_neighbors)
        message_text = TEXT.neighbors_not_found
    tgf.addButton(markup, GENERAL_ACTION, TEXT.main_menu)
    tgf.send_user_info_wrapper(BOT, tg_id, message_text, markup, service_chat_id=CONFIG['BOT']['servicechatid'])


def forward_from_user_to_chat(message, to_chat_id, text_to_chat, text_to_user):
    tg_id = message.from_user.id
    BOT.send_chat_action(tg_id, 'typing')
    result = text_to_user
    if message.content_type == 'text':
        if len(message.text) < 3:
            result = '❌ Сообщение не может быть короче трёх символов.'
    if result == text_to_user:
        BOT.send_message(to_chat_id, text_to_chat)
        BOT.forward_message(to_chat_id, message.chat.id, message.message_id)
    BOT.send_message(tg_id, result)
    start(message)


def send_advert(message):
    forward_from_user_to_chat(message, CONFIG['BOT']['servicechatid'],
                              'Объявление на модерацию для канала:',
                              '✅ Сообщение отправлено на модерацию. После неё оно будет опубликовано в @Halkon_SPb')
    # TODO оплата для тех кто не собственник в ЖК


def send_idea(message):
    forward_from_user_to_chat(message, CONFIG['BOT']['adminid'],
                              'Идея для бота:',
                              '✅ Сообщение отправлено разработчику. Спасибо!')


def send_post(message):
    tg_id = message.from_user.id
    BOT.send_chat_action(tg_id, 'typing')
    last_name = ''
    if message.from_user.last_name:
        last_name = message.from_user.last_name
    message_text = '''
———
{} {}'''.format(message.from_user.first_name, last_name)
    result = '✅ Сообщение отправлено в @Halkon_SPb'
    if message.content_type == 'text':
        if len(message.text) < 3:
            result = '❌ Сообщение не может быть короче трёх символов.'
        else:
            message_text = message.text + message_text
            BOT.send_message(CONFIG['BOT']['channelid'], message_text, parse_mode='HTML')
    else:
        print(message.content_type)
        if message.content_type in ['poll', 'sticker']:
            message_text = 'От {} {}:'.format(tg_id, message.from_user.first_name, last_name)
            BOT.send_message(CONFIG['BOT']['channelid'], message_text, parse_mode='HTML', disable_notification=True)
            message_text = None
        if message.caption:
            message_text = message.caption + message_text
        BOT.copy_message(CONFIG['BOT']['channelid'], tg_id, message.id,
                         caption=message_text, parse_mode='HTML', allow_sending_without_reply=True)
    BOT.send_message(tg_id, result)
    BOT.send_message(CONFIG['BOT']['servicechatid'], 'Опубликовал пост ID: {}'.format(tg_id))
    start(message)


@BOT.callback_query_handler(func=lambda call: tgf.getCallbackAction(call) == ADVERT_ACTION)
def advert(call):
    call_data = tgf.getCallbackData(call)
    tg_id = call.from_user.id
    log.info('%s in "advert" with "%s"', tg_id, call_data)
    BOT.edit_message_reply_markup(tg_id, call.message.id, reply_markup=None)
    if call_data == TEXT.make_advert:
        '''объявление на модерацию
        '''
        BOT.send_message(tg_id, 'Отправьте пожалуйста объявление одним сообщением. После модерации оно будет перенаправлено в @Halkon_SPb.\nДля отмены отправьте любую букву.')
        BOT.register_next_step_handler(call.message, send_advert)
    elif call_data == TEXT.todo_for_bot:
        '''обратная связь
        '''
        BOT.send_message(tg_id, 'Напишите пожалуйста ваши идеи/предложения для отправки разработчику.\nДля отмены отправьте любую букву.')
        BOT.register_next_step_handler(call.message, send_idea)
    elif call_data == TEXT.make_post:
        '''сообщение от проверенного в канал
        '''
        BOT.send_message(tg_id, 'Напишите пожалуйста ваше сообщение. Оно будет опубликовано от имени канала в @Halkon_SPb. Ваше имя будет добавлено в подпись к сообщению.\nДля отмены отправьте любую букву.')
        BOT.register_next_step_handler(call.message, send_post)
    else:
        print("WTF advert WTF")
        BOT.send_message(tg_id, TEXT.error.format('advert'))


@BOT.callback_query_handler(func=lambda call: tgf.getCallbackAction(call) == SETTINGS_ACTION)
def user_settings(call):
    call_data = tgf.getCallbackData(call)
    tg_id = call.from_user.id
    log.info('%s in "user_settings" with "%s"', tg_id, call_data)
    registered_user = flats.Resident.findByTgID(flats.getAllHouseResidents(HOUSE_DICT), tg_id)
    BOT.edit_message_reply_markup(tg_id, call.message.id, reply_markup=None)
    if call_data in (TEXT.flat_id_hide, TEXT.flat_id_show):
        '''изменение отображения настроек
        '''
        registered_user.show_flat_id = not registered_user.show_flat_id
        try:
            BOT.set_chat_administrator_custom_title(CHAT_ID, tg_id, registered_user.getStatus())
            func.save_dict_to_file(DATA_FILE_PATH, HOUSE_DICT, key=CONFIG['BOT']['cryptokey'])
            BOT.send_message(tg_id,
                             'Теперь в закрытом чате у Вас указан статус "{}".'.format(registered_user.getStatus()))
        except Exception as ex:
            log.error('error at user_settings in flat_id_hide or show: {}'.format(ex))
            BOT.send_message(tg_id, 'Что-то пошло не так, сообщите пожалуйста автору бота: {}'.format(ex))
    if call_data in (TEXT.flat_id_hide, TEXT.flat_id_show, TEXT.settings_menu):
        '''меню настроек
        '''
        markup = tg.types.InlineKeyboardMarkup(row_width=1)
        if registered_user.show_flat_id:  # управление отображением номера квартиры
            tgf.addButton(markup, SETTINGS_ACTION, TEXT.flat_id_hide)
        else:
            tgf.addButton(markup, SETTINGS_ACTION, TEXT.flat_id_show)

        tgf.addButton(markup, GENERAL_ACTION, TEXT.main_menu)
        BOT.send_message(tg_id, 'Доступные действия ⤵️', reply_markup=markup)


@BOT.callback_query_handler(func=lambda call: tgf.getCallbackAction(call) == GENERAL_ACTION)
def general(call):
    call_data = tgf.getCallbackData(call)
    tg_id = call.from_user.id
    log.info('%s in "general" with "%s"', tg_id, call_data)
    if call_data == TEXT.main_menu:
        '''назад в главное
        '''
        BOT.edit_message_reply_markup(tg_id, call.message.id, reply_markup=None)
        start(call)
    elif call_data == TEXT.get_yk_contact:
        '''контакты управляющей
        '''
        BOT.send_contact(tg_id, CONFIG['MC']['phone'], CONFIG['MC']['name'], CONFIG['MC']['lastname'])
    elif call_data == TEXT.admin_actions:
        '''меню администратора
        '''
        BOT.edit_message_reply_markup(tg_id, call.message.id, reply_markup=None)
        markup = tg.types.InlineKeyboardMarkup(row_width=1)
        tgf.addButton(markup, REGISTER_ACTION, TEXT.register_approve)
        tgf.addButton(markup, REGISTER_ACTION, TEXT.register_cancel)
        tgf.addButton(markup, REGISTER_ACTION, TEXT.register_ban)
        tgf.addButton(markup, NEIGHBORS_ACTION, TEXT.get_all_neighbors)
        tgf.addButton(markup, GENERAL_ACTION, TEXT.main_menu)
        BOT.send_message(tg_id, 'Доступные действия ⤵️', reply_markup=markup)
    elif call_data == TEXT.get_neighbors:
        '''меню поиска соседей
        '''
        BOT.edit_message_reply_markup(tg_id, call.message.id, reply_markup=None)
        markup = tg.types.InlineKeyboardMarkup(row_width=1)
        registered_user_flat = flats.Flat.findByPerson(flats.getAllHouseFlats(HOUSE_DICT), tg_id)
        if registered_user_flat:
            if registered_user_flat.up_residents:
                tgf.addButton(markup, NEIGHBORS_ACTION, TEXT.get_up_neighbors)
            tgf.addButton(markup, NEIGHBORS_ACTION, TEXT.get_floor_neighbors)
            if registered_user_flat.down_residents:
                tgf.addButton(markup, NEIGHBORS_ACTION, TEXT.get_down_neighbors)
            tgf.addButton(markup, NEIGHBORS_ACTION, TEXT.get_entrance_neighbors)
        tgf.addButton(markup, GENERAL_ACTION, TEXT.main_menu)
        BOT.send_message(tg_id, 'Доступные действия ⤵️', reply_markup=markup)
    elif call_data == TEXT.statistics:
        '''статистика по боту
        '''
        message_text = flats.get_text_statistics(HOUSE_DICT)
        BOT.edit_message_reply_markup(tg_id, call.message.id, reply_markup=None)
        markup = tg.types.InlineKeyboardMarkup(row_width=1)
        tgf.addButton(markup, GENERAL_ACTION, TEXT.main_menu)
        BOT.send_message(tg_id, message_text, reply_markup=markup, parse_mode='HTML')
    else:
        print("WTF general WTF")
        BOT.send_message(tg_id, TEXT.error.format('general'))
    pass


@BOT.callback_query_handler(func=lambda call: True)
def empty_action(call):
    print(call)
    tg_id = call.from_user.id
    BOT.send_chat_action(tg_id, 'typing')
    print("WTF empty_action WTF")
    BOT.send_message(tg_id, TEXT.error.format('empty_action'))


@BOT.message_handler(commands=['start', 'help'])
def bot_commands_handler(message):
    bot_all_messages_handler(message)


@BOT.message_handler(func=lambda message: True,
                     content_types=['audio', 'photo', 'voice', 'video', 'document', 'text', 'location', 'contact',
                                    'sticker'])
def bot_all_messages_handler(message):
    if message.chat.type == 'private':
        start(message)


def start(message):
    tg_id = message.from_user.id
    BOT.send_chat_action(tg_id, 'typing')
    log.info('%s in "start"', tg_id)
    BOT.send_message(CONFIG['BOT']['adminid'],
                     '<a href="tg://user?id={}">{}</a> в старте 🐉'.format(tg_id, message.from_user.first_name),
                     parse_mode='HTML', disable_notification=True)
    # print(message.forward_from.id)
    registered_user = None
    registered_user_flat = flats.Flat.findByPerson(flats.getAllHouseFlats(HOUSE_DICT), tg_id)
    if registered_user_flat:
        registered_user = flats.Resident.findByTgID(registered_user_flat.residents, tg_id)
    markup = tg.types.InlineKeyboardMarkup(row_width=8)
    text_for_message = ''
    if registered_user:
        if registered_user_flat.id == BAN:
            '''BAN'''
            markup = None
            BOT.send_message(tg_id, TEXT.welcome_ban, reply_markup=markup)
            return 0  # EXIT

        # проверка на админство в чате (для присвоения статуса проверенного в случае установки человеком)
        if registered_user.status_id == 0:
            if registered_user.id in tgf.get_admins_ids(BOT, CHAT_ID):
                promote_user(registered_user.id, CONFIG['BOT']['adminid'])

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
                button = tg.types.InlineKeyboardButton(text=TEXT.close_chat_link, url=CHAT_LINK)
                markup.add(button)
                if not registered_user.flat_id:
                    ''' указал только номер этажа и парадную
                    '''
                    text_for_message = "👋 Вы не указали квартиру. Доступные действия ⤵️"
                    tgf.addButton(markup, NEIGHBORS_ACTION, TEXT.get_floor_neighbors)
                    tgf.addButton(markup, REGISTER_ACTION, TEXT.reregister_by_number)
                else:
                    ''' указал номер квартиры
                    '''
                    text_for_message = TEXT.welcome_flat.format(registered_user.flat_id)
                    tgf.addButton(markup, GENERAL_ACTION, TEXT.get_neighbors)
                pass
        if registered_user.status_id >= 1:
            ''' подтверждённый пользователь
            '''
            print(2)
            tgf.addButton(markup, ADVERT_ACTION, TEXT.make_post)
            if registered_user.id not in tgf.get_admins_ids(BOT, CHAT_ID):  # ToDO проверка на случай входа в чат после подтверждения человеком
                tgf.set_admin_in_chat(BOT, registered_user, CHAT_ID)
            tgf.addButton(markup, SETTINGS_ACTION, TEXT.settings_menu)
        if str(registered_user.id) == str(CONFIG['BOT']['adminid']):
            print('admin')
            tgf.addButton(markup, GENERAL_ACTION, TEXT.admin_actions)
            pass
        if registered_user.flat_id not in (CLOSELIVING, INTERESTED):
            '''кроме не относящихся к дому'''
            tgf.addButton(markup, GENERAL_ACTION, TEXT.statistics)
            tgf.addButton(markup, GENERAL_ACTION, TEXT.get_yk_contact)
        else:
            pass  # TODO добавить возможность переехать в наш ЖК
        tgf.addButton(markup, NEIGHBORS_ACTION, TEXT.get_house_commerce)
    else:
        ''' новый пользователь, ранее не регистрировался и не попадал в список
        '''
        print(-1)
        text_for_message = TEXT.welcome_first
        tgf.addButton(markup, REGISTER_ACTION, TEXT.register_start)

    tgf.addButton(markup, ADVERT_ACTION, TEXT.make_advert)
    tgf.addButton(markup, ADVERT_ACTION, TEXT.todo_for_bot)
    BOT.send_message(tg_id, text_for_message, reply_markup=markup)


def bot_check():
    return BOT.get_me()


def bot_runner():
    BOT.infinity_polling(none_stop=True)


t = threading.Thread(target=bot_runner)
t.start()


print("---")
residents_list_for_update = flats.getAllHouseResidents(HOUSE_DICT)
print(len(residents_list_for_update))
for registered_user in residents_list_for_update:
    if registered_user.id not in [5105104114]:
        if registered_user.status_id > 1:
            try:
                log.info('%s %s', registered_user.id, registered_user.getStatus())
                tgf.set_admin_in_chat(BOT, registered_user.id, CHAT_ID)
            except Exception as ex:
                log.error('%s in "---"', ex)
        else:
            log.error('%s scip', registered_user.id)
