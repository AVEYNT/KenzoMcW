from bot.helper.telegram_helper.message_utils import sendMessage
from bot import AUTHORIZED_CHATS, SUDO_USERS, dispatcher, DB_URI
from telegram.ext import CommandHandler
from bot.helper.telegram_helper.filters import CustomFilters
from telegram.ext import Filters
from telegram import Update
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.ext_utils.db_handler import DbManger


def authorize(update, context):
    reply_message = None
    message_ = None
    reply_message = update.message.reply_to_message
    message_ = update.message.text.split(' ')
    if len(message_) == 2:
        user_id = int(message_[1])
        if user_id in AUTHORIZED_CHATS:
            msg = 'Pengguna sudah diotorisasi'
        elif DB_URI is not None:
            msg = DbManger().db_auth(user_id)
        else:
            with open('authorized_chats.txt', 'a') as file:
                file.write(f'{user_id}\n')
                AUTHORIZED_CHATS.add(user_id)
                msg = 'Pengguna diotorisasi'
    elif reply_message is None:
        # Trying to authorize a chat
        chat_id = update.effective_chat.id
        if chat_id in AUTHORIZED_CHATS:
            msg = 'Obrolan sudah diotorisasi'

        elif DB_URI is not None:
            msg = DbManger().db_auth(chat_id)
        else:
            with open('authorized_chats.txt', 'a') as file:
                file.write(f'{chat_id}\n')
                AUTHORIZED_CHATS.add(chat_id)
                msg = 'Obrolan diotorisasi'
    else:
        # Trying to authorize someone by replying
        user_id = reply_message.from_user.id
        if user_id in AUTHORIZED_CHATS:
            msg = 'Pengguna sudah diotorisasi'
        elif DB_URI is not None:
            msg = DbManger().db_auth(user_id)
        else:
            with open('authorized_chats.txt', 'a') as file:
                file.write(f'{user_id}\n')
                AUTHORIZED_CHATS.add(user_id)
                msg = 'Pengguna diotorisasi'
    sendMessage(msg, context.bot, update)


def unauthorize(update, context):
    reply_message = None
    message_ = None
    reply_message = update.message.reply_to_message
    message_ = update.message.text.split(' ')
    if len(message_) == 2:
        user_id = int(message_[1])
        if user_id in AUTHORIZED_CHATS:
            if DB_URI is not None:
                msg = DbManger().db_unauth(user_id)
            else:
                AUTHORIZED_CHATS.remove(user_id)
                msg = 'Pengguna tidak sah'
        else:
            msg = 'Pengguna sudah tidak berwenang'
    elif reply_message is None:
        # Trying to unauthorize a chat
        chat_id = update.effective_chat.id
        if chat_id in AUTHORIZED_CHATS:
            if DB_URI is not None:
                msg = DbManger().db_unauth(chat_id)
            else:
                AUTHORIZED_CHATS.remove(chat_id)
                msg = 'Obrolan tidak sah'
        else:
            msg = 'Obrolan sudah tidak sah'
    else:
        # Trying to authorize someone by replying
        user_id = reply_message.from_user.id
        if user_id in AUTHORIZED_CHATS:
            if DB_URI is not None:
                msg = DbManger().db_unauth(user_id)
            else:
                AUTHORIZED_CHATS.remove(user_id)
                msg = 'Pengguna tidak sah'
        else:
            msg = 'Pengguna sudah tidak berwenang'
    with open('authorized_chats.txt', 'a') as file:
        file.truncate(0)
        for i in AUTHORIZED_CHATS:
            file.write(f'{i}\n')
    sendMessage(msg, context.bot, update)


def addSudo(update, context):
    reply_message = None
    message_ = None
    reply_message = update.message.reply_to_message
    message_ = update.message.text.split(' ')
    if len(message_) == 2:
        user_id = int(message_[1])
        if user_id in SUDO_USERS:
            msg = 'Sudah SUDO.'
        elif DB_URI is not None:
            msg = DbManger().db_addsudo(user_id)
        else:
            with open('sudo_users.txt', 'a') as file:
                file.write(f'{user_id}\n')
                SUDO_USERS.add(user_id)
                msg = 'Dipromosikan sebagai SUDO'
    elif reply_message is None:
        msg = "Beri ID atau balas pesan siapa yang ingin Anda promosikan"
    else:
        # Trying to authorize someone by replying
        user_id = reply_message.from_user.id
        if user_id in SUDO_USERS:
            msg = 'Sudah SUDO'
        elif DB_URI is not None:
            msg = DbManger().db_addsudo(user_id)
        else:
            with open('sudo_users.txt', 'a') as file:
                file.write(f'{user_id}\n')
                SUDO_USERS.add(user_id)
                msg = 'Dipromosikan sebagai Sudo'
    sendMessage(msg, context.bot, update)


def removeSudo(update, context):
    reply_message = None
    message_ = None
    reply_message = update.message.reply_to_message
    message_ = update.message.text.split(' ')
    if len(message_) == 2:
        user_id = int(message_[1])
        if user_id in SUDO_USERS:
            if DB_URI is not None:
                msg = DbManger().db_rmsudo(user_id)
            else:
                SUDO_USERS.remove(user_id)
                msg = 'Diturunkan'
        else:
            msg = 'Bukan Sudo'
    elif reply_message is None:
        msg = "Beri ID atau balas pesan siapa yang ingin Anda hapus dari Sudo"
    else:
        user_id = reply_message.from_user.id
        if user_id in SUDO_USERS:
            if DB_URI is not None:
                msg = DbManger().db_rmsudo(user_id)
            else:
                SUDO_USERS.remove(user_id)
                msg = 'Diturunkan'
        else:
            msg = 'Bukan Sudo'
    if DB_URI is None:
        with open('sudo_users.txt', 'a') as file:
            file.truncate(0)
            for i in SUDO_USERS:
                file.write(f'{i}\n')
    sendMessage(msg, context.bot, update)


def sendAuthChats(update, context):
    user = sudo = ''
    user += '\n'.join(str(id) for id in AUTHORIZED_CHATS)
    sudo += '\n'.join(str(id) for id in SUDO_USERS)
    sendMessage(f'<b><u>Authorized Chats</u></b>\n<code>{user}</code>\n<b><u>Sudo Users</u></b>\n<code>{sudo}</code>', context.bot, update)


send_auth_handler = CommandHandler(command=BotCommands.AuthorizedUsersCommand, callback=sendAuthChats,
                                    filters=CustomFilters.owner_filter | CustomFilters.sudo_user, run_async=True)
authorize_handler = CommandHandler(command=BotCommands.AuthorizeCommand, callback=authorize,
                                    filters=CustomFilters.owner_filter | CustomFilters.sudo_user, run_async=True)
unauthorize_handler = CommandHandler(command=BotCommands.UnAuthorizeCommand, callback=unauthorize,
                                    filters=CustomFilters.owner_filter | CustomFilters.sudo_user, run_async=True)
addsudo_handler = CommandHandler(command=BotCommands.AddSudoCommand, callback=addSudo,
                                    filters=CustomFilters.owner_filter, run_async=True)
removesudo_handler = CommandHandler(command=BotCommands.RmSudoCommand, callback=removeSudo,
                                    filters=CustomFilters.owner_filter, run_async=True)

dispatcher.add_handler(send_auth_handler)
dispatcher.add_handler(authorize_handler)
dispatcher.add_handler(unauthorize_handler)
dispatcher.add_handler(addsudo_handler)
dispatcher.add_handler(removesudo_handler)
