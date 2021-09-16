# Copyright (C) 2020  UserindoBot Team, <https://github.com/userbotindo/UserIndoBot.git>
# Copyright (C) 2021 Slam Devs Team, <https://github.com/SlamDevs/slam-mirrorbot.git>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import shutil, psutil
import signal
import os
import asyncio
import importlib
import traceback
import html
import json
import re
import requests
from typing import Optional

from pyrogram import idle
from sys import executable

from telegram import Message, Chat, User
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import Unauthorized
from telegram.ext import (
    CommandHandler,
    Filters,
    MessageHandler,
    CallbackQueryHandler,
)
from telegram.ext.dispatcher import DispatcherHandlerStop
from telegram.utils.helpers import escape_markdown
from sqlalchemy.exc import SQLAlchemyError, DBAPIError
from telegraph import Telegraph
from wserver import start_server_async
from bot import (
    dispatcher,
    DEV_USERS,
    SUDO_USERS,
    SUPPORT_USERS,
    updater,
    TOKEN,
    MESSAGE_DUMP,
    WEBHOOK,
    CERT_PATH,
    PORT,
    URL,
    LOGGER,
    BLACKLIST_CHATS,
    WHITELIST_CHATS,
)
from bot import bot, app, dispatcher, updater, botStartTime, IMAGE_URL, IGNORE_PENDING_REQUESTS, IS_VPS, PORT, alive, web, OWNER_ID, AUTHORIZED_CHATS, telegraph_token
from bot.helper.ext_utils import fs_utils
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.message_utils import *
from .helper.ext_utils.bot_utils import get_readable_file_size, get_readable_time
from .helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper import button_build

# needed to dynamically load modules
# NOTE: Module order is not guaranteed, specify that in the config file!
from bot.modules import ALL_MODULES
from bot.modules.helper_funcs.chat_status import is_user_admin
from bot.modules.helper_funcs.filters import CustomFilters
from bot.modules.helper_funcs.misc import paginate_modules
from bot.modules.helper_funcs.alternate import typing_action

PM_START_TEXT = f"""
Hello, I am *{dispatcher.bot.first_name}*.
Any questions on how to use me? use /help
Join Our [Group](https://t.me/KenzoMcW) If You wanna Report Issue!
I have lots of handy features ️ such as :
❖ 🔗 Mirror      ❖ 🇯🇵 Anime
❖ 🧲 Torrent    ❖ 📱Android
❖ 🎞 VideoDL  ❖ 🗜 Unpack
        ❖And many more❖
Developer fork [Kenzo McW](https://t.me/KenzoMcWnews)
Wanna Add me to your Group? Ask for access first!
"""

buttons = [
    [
        InlineKeyboardButton(
            text="Add to Group 👥", url="t.me/userbotindobot?startgroup=true"
        ),
        InlineKeyboardButton(
            text="Credits 💰", url="https://github.com/SlamDevs/slam-mirrorbot/graphs/contributors"
        ),
    ]
]


buttons += [
    [
        InlineKeyboardButton(
            text="Command Set⚙️",
            url=f"t.me/{dispatcher.bot.username}?start=help",
        ),
        InlineKeyboardButton(
            text="Support Channel 🧲", url="https://t.me/AVEYPROJECT"
        ),
    ]
]

kyby = [
    [
        InlineKeyboardButton(
            text="Support Channel 🧲", url="https://t.me/AVEYPROJECT"
        ),
    ]
]


HELP_STRINGS = f"""
Hello, I am *{dispatcher.bot.first_name}*.
*Main* commands available:

*Main* commands available:
 × /start: Starts me, can be used to check i'm alive or no...
 × /help: PM's you this message.
 × /help <module name>: PM's you info about that module.
 × /settings: in PM: will send you your settings for all supported modules.
   - in a group: will redirect you to pm, with all that chat's settings.
 \nClick on the buttons below to get documentation about specific modules!"""


STAFF_HELP_STRINGS = """Hey there staff users. Nice to see you :)
Here is all the staff's commands. Users above has the command access for all commands below.

*OWNER*
× /broadcast: Send a broadcast message to all chat that i'm currently in.
× /staffids: Get all staff's you have.
× /ip: Sends the bot's IP address to ssh in if necessary (PM only).

*DEV USERS*
× /gitpull: Pull latest update.
× /reboot: Restart the bot.
× /dbcleanup: Clean my invalid database.
× /leavemutedchats: Leave all chats where i can't send message.
× /leave <chatid>: Tell me to leave the given group. (alias /leavechat /leavegroup).
× /stats: List of all blacklists, filters, federations, gbans, etc from all group.
× /getlink <chatid>: Get chat invite link.
× /sysinfo: Get my system info.

*SUDO USERS*
× /snipe <chatid> <string>: Tell me to send a message to the given chat.
× /echo <string>: Like snipe but on the current chat.
× /chatlist: Get the list of chat that i'm currently in.
× /ping: Start a ping test.
× /speedtest: Start a speedtest from my server.

*SUPPORT USERS*
× /gban <userid>: global ban a user.
× /ungban <userid>: remove currently gbanned user.
× /gbanlist: Get the list of currently gbanned users."""


IMPORTED = {}
MIGRATEABLE = []
HELPABLE = {}
STATS = []
USER_INFO = []
DATA_IMPORT = []
DATA_EXPORT = []

CHAT_SETTINGS = {}
USER_SETTINGS = {}

GDPR = []

for module_name in ALL_MODULES:
    imported_module = importlib.import_module(
        "bot.modules." + module_name
    )
    if not hasattr(imported_module, "__mod_name__"):
        imported_module.__mod_name__ = imported_module.__name__

    if not imported_module.__mod_name__.lower() in IMPORTED:
        IMPORTED[imported_module.__mod_name__.lower()] = imported_module
    else:
        raise Exception(
            "Can't have two modules with the same name! Please change one"
        )

    if hasattr(imported_module, "__help__") and imported_module.__help__:
        HELPABLE[imported_module.__mod_name__.lower()] = imported_module

    # Chats to migrate on chat_migrated events
    if hasattr(imported_module, "__migrate__"):
        MIGRATEABLE.append(imported_module)

    if hasattr(imported_module, "__stats__"):
        STATS.append(imported_module)

    if hasattr(imported_module, "__gdpr__"):
        GDPR.append(imported_module)

    if hasattr(imported_module, "__user_info__"):
        USER_INFO.append(imported_module)

    if hasattr(imported_module, "__import_data__"):
        DATA_IMPORT.append(imported_module)

    if hasattr(imported_module, "__export_data__"):
        DATA_EXPORT.append(imported_module)

    if hasattr(imported_module, "__chat_settings__"):
        CHAT_SETTINGS[imported_module.__mod_name__.lower()] = imported_module

    if hasattr(imported_module, "__user_settings__"):
        USER_SETTINGS[imported_module.__mod_name__.lower()] = imported_module


def stats(update, context):
    currentTime = get_readable_time(time.time() - botStartTime)
    total, used, free = shutil.disk_usage('.')
    total = get_readable_file_size(total)
    used = get_readable_file_size(used)
    free = get_readable_file_size(free)
    sent = get_readable_file_size(psutil.net_io_counters().bytes_sent)
    recv = get_readable_file_size(psutil.net_io_counters().bytes_recv)
    cpuUsage = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    stats = f'<b>Bot Uptime:</b> <code>{currentTime}</code>\n' \
            f'<b>Total Disk Space:</b> <code>{total}</code>\n' \
            f'<b>Used:</b> <code>{used}</code> ' \
            f'<b>Free:</b> <code>{free}</code>\n\n' \
            f'<b>Upload:</b> <code>{sent}</code>\n' \
            f'<b>Download:</b> <code>{recv}</code>\n\n' \
            f'<b>CPU:</b> <code>{cpuUsage}%</code> ' \
            f'<b>RAM:</b> <code>{memory}%</code> ' \
            f'<b>DISK:</b> <code>{disk}%</code>'
    sendMessage(stats, context.bot, update)

# do not async
def send_help(chat_id, text, keyboard=None):
    if not keyboard:
        keyboard = InlineKeyboardMarkup(paginate_modules(0, HELPABLE, "help"))
    dispatcher.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard,
    )

def start(update, context):
    if update.effective_chat.type == "private":
        args = context.args
        if len(args) >= 1:
            if args[0].lower() == "help":
                user = update.effective_user
                keyb = paginate_modules(0, HELPABLE, "help")

                if (
                    user.id == OWNER_ID
                ):
                    keyb += [
                        [
                            InlineKeyboardButton(
                                text="👤Owner", callback_data="help_staff"
                            )
                        ]
                    ]

                send_help(
                    update.effective_chat.id,
                    HELP_STRINGS,
                    InlineKeyboardMarkup(keyb),
                )

            elif args[0].lower().startswith("stngs_"):
                match = re.match("stngs_(.*)", args[0].lower())
                chat = dispatcher.bot.getChat(match.group(1))

                if is_user_admin(chat, update.effective_user.id):
                    send_settings(
                        match.group(1), update.effective_user.id, False
                    )
                else:
                    send_settings(
                        match.group(1), update.effective_user.id, True
                    )

            elif args[0][1:].isdigit() and "rules" in IMPORTED:
                IMPORTED["rules"].send_rules(update, args[0], from_pm=True)

        else:
            update.effective_message.reply_photo(
                IMAGE_URL,
                PM_START_TEXT,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN,
                timeout=60,
            )
    else:
         update.effective_message.reply_photo(
             IMAGE_URL,
            "Edotensei success!!!✨, /help di PM Sloer!!!🗿",
            reply_markup=InlineKeyboardMarkup(kyby),
            parse_mode=ParseMode.MARKDOWN,
            timeout=60
        )

def error_handler(update, context):
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    LOGGER.error(
        msg="Exception while handling an update:", exc_info=context.error
    )
    if isinstance(context.error, SQLAlchemyError) or isinstance(
        context.error, DBAPIError
    ):
        return
    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    else:
        tb_list = traceback.format_exception(
            None, context.error, context.error.__traceback__
        )
        tb_string = "".join(tb_list)

        # Build the message with some markup and additional information about what happened.
        # You might need to add some logic to deal with messages longer than the 4096 character limit.
        message = (
            f"An exception was raised while handling an update\n"
            f"update = {(json.dumps(update.to_dict(), indent=2, ensure_ascii=False))}"
            "\n\n"
            f"context.chat_data = {(str(context.chat_data))}\n\n"
            f"context.user_data = {(str(context.user_data))}\n\n"
            f"{(tb_string)}"
        )

        key = (
            requests.post(
                "https://nekobin.com/api/documents", json={"content": message}
            )
            .json()
            .get("result")
            .get("key")
        )
        markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Nekobin Url", url=f"https://nekobin.com/{key}"
                    ),
                    InlineKeyboardButton(
                        "Nekobin Raw", url=f"https://nekobin.com/raw/{key}"
                    ),
                ]
            ]
        )

    # Finally, send the message
    context.bot.send_message(
        chat_id=MESSAGE_DUMP,
        text="an error has been found here !!!",
        reply_markup=markup,
    )

def help_button(update, context):
    query = update.callback_query
    user = update.effective_user
    mod_match = re.match(r"help_module\((.+?)\)", query.data)
    staff_match = re.match(r"help_staff", query.data)
    back_match = re.match(r"help_back", query.data)
    try:
        if mod_match:
            module = mod_match.group(1)
            text = (
                "Here is the help for the *{}* module:\n".format(
                    HELPABLE[module].__mod_name__
                )
                + HELPABLE[module].__help__
            )
            query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="⬅️ Back", callback_data="help_back"
                            )
                        ]
                    ]
                ),
            )

        elif staff_match:
            query.message.edit_text(
                text=STAFF_HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="⬅️ Back", callback_data="help_back"
                            )
                        ]
                    ]
                ),
            )

        elif back_match:
            keyb = paginate_modules(0, HELPABLE, "help")
            # Add aditional button if staff user detected
            if (
                user.id in DEV_USERS
                or user.id in SUDO_USERS
                or user.id in SUPPORT_USERS
            ):
                keyb += [
                    [
                        InlineKeyboardButton(
                            text="Staff", callback_data="help_staff"
                        )
                    ]
                ]

            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyb),
            )

        # ensure no spinny white circle
        context.bot.answer_callback_query(query.id)
    except Exception as excp:
        if excp.message == "Message is not modified":
            pass
        elif excp.message == "Query_id_invalid":
            pass
        elif excp.message == "Message can't be deleted":
            pass
        else:
            query.message.edit_text(excp.message)
            LOGGER.exception("Exception in help buttons. %s", str(query.data))


@typing_action
def staff_help(update, context):
    chat = update.effective_chat
    user = update.effective_user

    if chat.type != chat.PRIVATE:
        update.effective_message.reply_text(
            "Contact me in PM to get the list of staff's command"
        )
        return

    if (
        user.id in DEV_USERS
        or user.id in SUDO_USERS
        or user.id in SUPPORT_USERS
    ):
        update.effective_message.reply_text(
            text=STAFF_HELP_STRINGS,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Modules help", callback_data="help_back"
                        )
                    ]
                ]
            ),
        )
    else:
        update.effective_message.reply_text("You can't access this command")


@typing_action
def get_help(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user
    args = update.effective_message.text.split(None, 1)

    # ONLY send help in PM
    if chat.type != chat.PRIVATE:

        update.effective_message.reply_text(
            "Contact me in PM to get the list of possible commands.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Help",
                            url="t.me/{}?start=help".format(
                                context.bot.username
                            ),
                        )
                    ]
                ]
            ),
        )
        return

    elif len(args) >= 2 and any(args[1].lower() == x for x in HELPABLE):
        module = args[1].lower()
        text = (
            "Here is the available help for the *{}* module:\n".format(
                HELPABLE[module].__mod_name__
            )
            + HELPABLE[module].__help__
        )
        send_help(
            chat.id,
            text,
            InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Back", callback_data="help_back"
                        )
                    ]
                ]
            ),
        )

    else:
        keyb = paginate_modules(0, HELPABLE, "help")
        # Add aditional button if staff user detected
        if (
            user.id in DEV_USERS
            or user.id in SUDO_USERS
            or user.id in SUPPORT_USERS
        ):
            keyb += [
                [
                    InlineKeyboardButton(
                        text="Staff", callback_data="help_staff"
                    )
                ]
            ]

        send_help(chat.id, HELP_STRINGS, InlineKeyboardMarkup(keyb))


def send_settings(chat_id, user_id, user=False):
    if user:
        if USER_SETTINGS:
            settings = "\n\n".join(
                "*{}*:\n{}".format(
                    mod.__mod_name__, mod.__user_settings__(user_id)
                )
                for mod in USER_SETTINGS.values()
            )
            dispatcher.bot.send_message(
                user_id,
                "These are your current settings:" + "\n\n" + settings,
                parse_mode=ParseMode.MARKDOWN,
            )

        else:
            dispatcher.bot.send_message(
                user_id,
                "Seems like there aren't any user specific settings available :'(",
                parse_mode=ParseMode.MARKDOWN,
            )

    else:
        if CHAT_SETTINGS:
            chat_name = dispatcher.bot.getChat(chat_id).title
            dispatcher.bot.send_message(
                user_id,
                text="Which module would you like to check {}'s settings for?".format(
                    chat_name
                ),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)
                ),
            )
        else:
            dispatcher.bot.send_message(
                user_id,
                "Seems like there aren't any chat settings available :'(\nSend this "
                "in a group chat you're admin in to find its current settings!",
                parse_mode=ParseMode.MARKDOWN,
            )


def settings_button(update, context):
    query = update.callback_query
    user = update.effective_user
    mod_match = re.match(r"stngs_module\((.+?),(.+?)\)", query.data)
    prev_match = re.match(r"stngs_prev\((.+?),(.+?)\)", query.data)
    next_match = re.match(r"stngs_next\((.+?),(.+?)\)", query.data)
    back_match = re.match(r"stngs_back\((.+?)\)", query.data)
    try:
        if mod_match:
            chat_id = mod_match.group(1)
            module = mod_match.group(2)
            chat = context.bot.get_chat(chat_id)
            text = "*{}* has the following settings for the *{}* module:\n\n".format(
                escape_markdown(chat.title), CHAT_SETTINGS[module].__mod_name__
            ) + CHAT_SETTINGS[
                module
            ].__chat_settings__(
                chat_id, user.id
            )
            query.message.reply_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Back",
                                callback_data="stngs_back({})".format(chat_id),
                            )
                        ]
                    ]
                ),
            )

        elif prev_match:
            chat_id = prev_match.group(1)
            curr_page = int(prev_match.group(2))
            chat = context.bot.get_chat(chat_id)
            query.message.reply_text(
                "Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(chat.title),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(
                        curr_page - 1, CHAT_SETTINGS, "stngs", chat=chat_id
                    )
                ),
            )

        elif next_match:
            chat_id = next_match.group(1)
            next_page = int(next_match.group(2))
            chat = context.bot.get_chat(chat_id)
            query.message.reply_text(
                "Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(chat.title),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(
                        next_page + 1, CHAT_SETTINGS, "stngs", chat=chat_id
                    )
                ),
            )

        elif back_match:
            chat_id = back_match.group(1)
            chat = context.bot.get_chat(chat_id)
            query.message.reply_text(
                text="Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(escape_markdown(chat.title)),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)
                ),
            )

        # ensure no spinny white circle
        query.message.delete()
        context.bot.answer_callback_query(query.id)
    except Exception as excp:
        if excp.message == "Message is not modified":
            pass
        elif excp.message == "Query_id_invalid":
            pass
        elif excp.message == "Message can't be deleted":
            pass
        else:
            query.message.edit_text(excp.message)
            LOGGER.exception(
                "Exception in settings buttons. %s", str(query.data)
            )


@typing_action
def get_settings(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]
    msg.text.split(None, 1)

    # ONLY send settings in PM
    if chat.type != chat.PRIVATE:
        if is_user_admin(chat, user.id):
            text = "Click here to get this chat's settings, as well as yours."
            msg.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Settings",
                                url="t.me/{}?start=stngs_{}".format(
                                    context.bot.username, chat.id
                                ),
                            )
                        ]
                    ]
                ),
            )
        else:
            text = "Click here to check your settings."

    else:
        send_settings(chat.id, user.id, True)


def migrate_chats(update, context):
    msg = update.effective_message  # type: Optional[Message]
    if msg.migrate_to_chat_id:
        old_chat = update.effective_chat.id
        new_chat = msg.migrate_to_chat_id
    elif msg.migrate_from_chat_id:
        old_chat = msg.migrate_from_chat_id
        new_chat = update.effective_chat.id
    else:
        return

    LOGGER.info("Migrating from %s, to %s", str(old_chat), str(new_chat))
    for mod in MIGRATEABLE:
        mod.__migrate__(old_chat, new_chat)

    LOGGER.info("Successfully migrated!")
    raise DispatcherHandlerStop


def is_chat_allowed(update, context):
    if len(WHITELIST_CHATS) != 0:
        chat_id = update.effective_message.chat_id
        if chat_id not in WHITELIST_CHATS:
            try:
                context.bot.send_message(
                    chat_id=chat_id,
                    text="This group is Blacklisted! Leaving...",
                )
                context.bot.leave_chat(chat_id)
            except Unauthorized:
                pass
            finally:
                raise DispatcherHandlerStop
    if len(BLACKLIST_CHATS) != 0:
        chat_id = update.effective_message.chat_id
        if chat_id in BLACKLIST_CHATS:
            try:
                context.bot.send_message(
                    chat_id=chat_id,
                    text="This group is Blacklisted! Leaving...",
                )
                context.bot.leave_chat(chat_id)
            except Unauthorized:
                pass
            finally:
                raise DispatcherHandlerStop
    if len(WHITELIST_CHATS) != 0 and len(BLACKLIST_CHATS) != 0:
        chat_id = update.effective_message.chat_id
        if chat_id in BLACKLIST_CHATS:
            try:
                context.bot.send_message(
                    chat_id=chat_id,
                    text="This group is Blacklisted! Leaving..."
                )
                context.bot.leave_chat(chat_id)
            except Unauthorized:
                pass
            finally:
                raise DispatcherHandlerStop

def restart(update, context):
    restart_message = sendMessage("Restarting, Please wait!", context.bot, update)
    # Save restart message object in order to reply to it after restarting
    with open(".restartmsg", "w") as f:
        f.truncate(0)
        f.write(f"{restart_message.chat.id}\n{restart_message.message_id}\n")
    fs_utils.clean_all()
    alive.terminate()
    web.terminate()
    os.execl(executable, executable, "-m", "bot")


def ping(update, context):
    start_time = int(round(time.time() * 1000))
    reply = sendMessage("Starting Ping", context.bot, update)
    end_time = int(round(time.time() * 1000))
    editMessage(f'{end_time - start_time} ms', reply)


def log(update, context):
    sendLogFile(context.bot, update)



def bot_menu(update, context):
    help_string_telegraph = f'''<br>
<b>/{BotCommands.HelpCommand}</b>: To get this message
<br><br>
<b>/{BotCommands.MirrorCommand}</b> [download_url][magnet_link]: Start mirroring the link to Google Drive.
<br><br>
<b>/{BotCommands.TarMirrorCommand}</b> [download_url][magnet_link]: Start mirroring and upload the archived (.tar) version of the download
<br><br>
<b>/{BotCommands.ZipMirrorCommand}</b> [download_url][magnet_link]: Start mirroring and upload the archived (.zip) version of the download
<br><br>
<b>/{BotCommands.UnzipMirrorCommand}</b> [download_url][magnet_link]: Starts mirroring and if downloaded file is any archive, extracts it to Google Drive
<br><br>
<b>/{BotCommands.QbMirrorCommand}</b> [magnet_link]: Start Mirroring using qBittorrent, Use /{BotCommands.QbMirrorCommand} s to select files before downloading
<br><br>
<b>/{BotCommands.QbTarMirrorCommand}</b> [magnet_link]: Start mirroring using qBittorrent and upload the archived (.tar) version of the download
<br><br>
<b>/{BotCommands.QbZipMirrorCommand}</b> [magnet_link]: Start mirroring using qBittorrent and upload the archived (.zip) version of the download
<br><br>
<b>/{BotCommands.QbUnzipMirrorCommand}</b> [magnet_link]: Starts mirroring using qBittorrent and if downloaded file is any archive, extracts it to Google Drive
<br><br>
<b>/{BotCommands.CloneCommand}</b> [drive_url]: Copy file/folder to Google Drive
<br><br>
<b>/{BotCommands.CountCommand}</b> [drive_url]: Count file/folder of Google Drive Links
<br><br>
<b>/{BotCommands.DeleteCommand}</b> [drive_url]: Delete file from Google Drive (Only Owner & Sudo)
<br><br>
<b>/{BotCommands.WatchCommand}</b> [youtube-dl supported link]: Mirror through youtube-dl. Click /{BotCommands.WatchCommand} for more help
<br><br>
<b>/{BotCommands.TarWatchCommand}</b> [youtube-dl supported link]: Mirror through youtube-dl and tar before uploading
<br><br>
<b>/{BotCommands.ZipWatchCommand}</b> [youtube-dl supported link]: Mirror through youtube-dl and zip before uploading
<br><br>
<b>/{BotCommands.CancelMirror}</b>: Reply to the message by which the download was initiated and that download will be cancelled
<br><br>
<b>/{BotCommands.CancelAllCommand}</b>: Cancel all running tasks
<br><br>
<b>/{BotCommands.ListCommand}</b> [search term]: Searches the search term in the Google Drive, If found replies with the link
<br><br>
<b>/{BotCommands.StatusCommand}</b>: Shows a status of all the downloads
<br><br>
<b>/{BotCommands.StatsCommand}</b>: Show Stats of the machine the bot is hosted on
'''

    help_string = f'''
/{BotCommands.PingCommand}: Check how long it takes to Ping the Bot

/{BotCommands.AuthorizeCommand}: Authorize a chat or a user to use the bot (Can only be invoked by Owner & Sudo of the bot)

/{BotCommands.UnAuthorizeCommand}: Unauthorize a chat or a user to use the bot (Can only be invoked by Owner & Sudo of the bot)

/{BotCommands.AuthorizedUsersCommand}: Show authorized users (Only Owner & Sudo)

/{BotCommands.AddSudoCommand}: Add sudo user (Only Owner)

/{BotCommands.RmSudoCommand}: Remove sudo users (Only Owner)

/{BotCommands.RestartCommand}: Restart the bot

/{BotCommands.LogCommand}: Get a log file of the bot. Handy for getting crash reports

/{BotCommands.SpeedCommand}: Check Internet Speed of the Host

/{BotCommands.ShellCommand}: Run commands in Shell (Only Owner)

/{BotCommands.ExecHelpCommand}: Get help for Executor module (Only Owner)

/{BotCommands.TsHelpCommand}: Get help for Torrent search module
'''
    help = Telegraph(access_token=telegraph_token).create_page(title = 'AVEY Help', author_name='AVEY',
                                                               author_url='https://t.me/AVEYNT', html_content=help_string_telegraph)["path"]
    button = button_build.ButtonMaker()
    button.buildbutton("Other Commands", f"https://telegra.ph/{help}")
    reply_markup = InlineKeyboardMarkup(button.build_menu(1))
    sendMarkup(help_string, context.bot, update, reply_markup)

'''
botcmds = [
        (f'{BotCommands.HelpCommand}','Get Detailed Help'),
        (f'{BotCommands.MirrorCommand}', 'Start Mirroring'),
        (f'{BotCommands.TarMirrorCommand}','Start mirroring and upload as .tar'),
        (f'{BotCommands.ZipMirrorCommand}','Start mirroring and upload as .zip'),
        (f'{BotCommands.UnzipMirrorCommand}','Extract files'),
        (f'{BotCommands.QbMirrorCommand}','Start Mirroring using qBittorrent'),
        (f'{BotCommands.QbTarMirrorCommand}','Start mirroring and upload as .tar using qb'),
        (f'{BotCommands.QbZipMirrorCommand}','Start mirroring and upload as .zip using qb'),
        (f'{BotCommands.QbUnzipMirrorCommand}','Extract files using qBitorrent'),
        (f'{BotCommands.CloneCommand}','Copy file/folder to Drive'),
        (f'{BotCommands.CountCommand}','Count file/folder of Drive link'),
        (f'{BotCommands.DeleteCommand}','Delete file from Drive'),
        (f'{BotCommands.WatchCommand}','Mirror Youtube-dl support link'),
        (f'{BotCommands.TarWatchCommand}','Mirror Youtube playlist link as .tar'),
        (f'{BotCommands.ZipWatchCommand}','Mirror Youtube playlist link as .zip'),
        (f'{BotCommands.CancelMirror}','Cancel a task'),
        (f'{BotCommands.CancelAllCommand}','Cancel all tasks'),
        (f'{BotCommands.ListCommand}','Searches files in Drive'),
        (f'{BotCommands.StatusCommand}','Get Mirror Status message'),
        (f'{BotCommands.StatsCommand}','Bot Usage Stats'),
        (f'{BotCommands.PingCommand}','Ping the Bot'),
        (f'{BotCommands.RestartCommand}','Restart the bot [owner/sudo only]'),
        (f'{BotCommands.LogCommand}','Get the Bot Log [owner/sudo only]'),
        (f'{BotCommands.TsHelpCommand}','Get help for Torrent search module')
    ]
'''

def main():
    fs_utils.start_cleanup()
    if IS_VPS:
        asyncio.get_event_loop().run_until_complete(start_server_async(PORT))
    # Check if the bot is restarting
    if os.path.isfile(".restartmsg"):
        with open(".restartmsg") as f:
            chat_id, msg_id = map(int, f)
        bot.edit_message_text("Restarted successfully!", chat_id, msg_id)
        os.remove(".restartmsg")
    elif OWNER_ID:
        try:
            text = "<b>Bot Restarted!</b>"
            bot.sendMessage(chat_id=OWNER_ID, text=text, parse_mode=ParseMode.HTML)
            if AUTHORIZED_CHATS:
                for i in AUTHORIZED_CHATS:
                    bot.sendMessage(chat_id=i, text=text, parse_mode=ParseMode.HTML)
        except Exception as e:
            LOGGER.warning(e)
    # bot.set_my_commands(botcmds)
    start_handler = CommandHandler(BotCommands.StartCommand, start, run_async=True)
    ping_handler = CommandHandler(BotCommands.PingCommand, ping,
                                  filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
    restart_handler = CommandHandler(BotCommands.RestartCommand, restart,
                                     filters=CustomFilters.owner_filter | CustomFilters.sudo_user, run_async=True)
    help_handler = CommandHandler(BotCommands.HelpCommand, get_help)
    help_callback_handler = CallbackQueryHandler(
        help_button, pattern=r"help_", run_async=True
    )
    help_staff_handler = CommandHandler("staffhelp", staff_help,
        filters=CustomFilters.owner_filter | CustomFilters.sudo_user, run_async=True)
    settings_handler = CommandHandler("settings", get_settings, run_async=True)
    settings_callback_handler = CallbackQueryHandler(
        settings_button, pattern=r"stngs_", run_async=True
    )

    migrate_handler = MessageHandler(
        Filters.status_update.migrate, migrate_chats
    )
    is_chat_allowed_handler = MessageHandler(Filters.chat_type.groups, is_chat_allowed)
    menu_handler = CommandHandler('menu',
                                  bot_menu, filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
    stats_handler = CommandHandler(BotCommands.StatsCommand,
                                   stats, filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
    log_handler = CommandHandler(BotCommands.LogCommand, log, filters=CustomFilters.owner_filter | CustomFilters.sudo_user, run_async=True)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(settings_handler)
    dispatcher.add_handler(help_callback_handler)
    dispatcher.add_handler(help_staff_handler)
    dispatcher.add_handler(settings_callback_handler)
    dispatcher.add_handler(migrate_handler)
    dispatcher.add_handler(is_chat_allowed_handler)
    dispatcher.add_error_handler(error_handler)
    dispatcher.add_handler(ping_handler)
    dispatcher.add_handler(restart_handler)
    dispatcher.add_handler(menu_handler)
    dispatcher.add_handler(stats_handler)
    dispatcher.add_handler(log_handler)
    updater.start_polling(drop_pending_updates=IGNORE_PENDING_REQUESTS)
    
    if WEBHOOK:
        LOGGER.info("Using webhooks.")
        updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN)

        if CERT_PATH:
            updater.bot.set_webhook(
                url=URL + TOKEN, certificate=open(CERT_PATH, "rb")
            )
        else:
            updater.bot.set_webhook(url=URL + TOKEN)

    else:
        LOGGER.info("Using long polling.")
        updater.start_polling(timeout=15, read_latency=5, clean=True)
        if MESSAGE_DUMP:
            updater.bot.send_message(
                chat_id=MESSAGE_DUMP, text="System Started..."
            )

    updater.idle()
    
if __name__ == "__main__":
    LOGGER.info("Successfully loaded modules: " + str(ALL_MODULES))
    LOGGER.info("Bot Started!")
    signal.signal(signal.SIGINT, fs_utils.exit_clean_up)

app.start()
main()
idle()
