import telebot as tg
import logging as log
from constants import *


def get_admins_ids(bot, chat_id_for_search):
    ids = []
    admins = bot.get_chat_administrators(chat_id_for_search)
    for a in admins:
        ids.append(a.user.id)
    return ids


def set_admin_in_chat(bot, resident_for_promote, chat_id_for_promote):
    try:
        bot.promote_chat_member(chat_id_for_promote, resident_for_promote.id,
                                can_change_info=False, can_post_messages=True, can_edit_messages=False,
                                can_delete_messages=False, can_invite_users=True, can_restrict_members=False,
                                can_pin_messages=True, can_manage_chat=False, can_promote_members=False,
                                can_manage_video_chats=True, can_manage_voice_chats=True, can_manage_topics=False)
        bot.set_chat_administrator_custom_title(chat_id_for_promote, resident_for_promote.id,
                                                resident_for_promote.getStatus())
    except Exception as ex:
        log.error('error at bot.promote in set_admin_in_chat: %s', ex)


def actionCallbackData(action, data):
    return '{}{}{}'.format(action, SPLITTER, data)


def getCallbackAction(call):
    try:
        return int(call.data.split(SPLITTER)[0])
    except Exception:
        return -1


def getCallbackData(call):
    return call.data.split(SPLITTER)[1]


def addButton(markup, action, text, data=None):
    if not data:
        data = text
    button = tg.types.InlineKeyboardButton(text=text, callback_data=actionCallbackData(action, data))
    if type(markup) is list:
        markup.append(button)
    else:
        markup.add(button)


def users_link_markup(tg_id, name):
    markup = tg.types.InlineKeyboardMarkup(row_width=2)
    button = tg.types.InlineKeyboardButton(str(name), url='tg://user?id={}'.format(tg_id))
    markup.add(button)
    return markup


def get_user_name(bot, channel_id, tg_id):
    user = None
    try:
        chat = bot.get_chat(tg_id)
        if chat.type == 'private':
            user = chat
    except Exception:
        print("no direct chat")
    if not user:
        try:
            chat_member = bot.get_chat_member(channel_id, tg_id)
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


def send_user_info_wrapper(bot, to_chat_id, message_text, markup,
                           parse_mode=None, disable_notification=False, service_chat_id=None):
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
            if service_chat_id:
                bot.send_message(service_chat_id,
                                 'EROOR with sending to tg://user?id={}'.format(to_chat_id))
        log.warning('send_user_info_wrapper for : %s', to_chat_id)


def get_id_from_text(message_text):
    try:
        res_id = int(message_text.strip())
    except Exception:
        res_id = None
    return res_id


def get_another_id(message):
    if message.forward_from:
        another_tg_id = message.forward_from.id
        another_user_name = message.forward_from.first_name
    else:
        another_tg_id = get_id_from_text(message.text)
        another_user_name = message.text
    return another_tg_id, another_user_name
