import shutil, psutil
import signal
import os
import asyncio
import importlib
import re

from pyrogram import idle
from bot import app, alive
from sys import executable

from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, CallbackQueryHandler
from wserver import start_server_async
from bot import bot, dispatcher, updater, botStartTime, OWNER_ID, IGNORE_PENDING_REQUESTS, IS_VPS, SERVER_PORT, IMAGE_URL
from bot.helper.ext_utils import fs_utils
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.message_utils import *
from .helper.ext_utils.bot_utils import get_readable_file_size, get_readable_time
from .helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper import button_build
from bot.modules import ALL_MODULES
from bot.helper.misc import paginate_modules

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
            text="Support Channel 🧲", url="https://t.me/KenzoMcWnews"
        ),
    ]
]



HELP_STRINGS = f"""
Hello, I am *{dispatcher.bot.first_name}*.
*Main* commands available:
 ❖ /start: Starts me, can be used to check i'm alive or no...
 ❖ /help: PM's you this message.
  \nClick on the buttons below to get documentation about specific modules!"""


STAFF_HELP_STRINGS = """
┎─────┨ 👤 Owner ┠────┒
│ ❖ /auth : izinkan  group
│ ❖ /unauth : cabut izin group
│ ❖ /users : izinkan orang
│ ❖ /addsudo : add sudo
│ ❖ /rmsudo : remove sudo
│ ❖ /log : log file bot
│ ❖ /config : info bot config
│ ❖ /specs : stats server
│ ❖ /del : delete files by links
│ ❖ /update : update bot
│ ❖ /term : terminal commands
│ ❖ /eval : run Python Code Lines
│ ❖ /exec : run Commands In Exec
│ ❖ /clearlocals : Cleared locals
│ ❖ /life : check life of bot
│ ❖ /exechelp : executor help
┖──────────────────┚
"""

IMPORTED = {}
HELPABLE = {}


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
    stats = f'<b>Bot Uptime:</b> {currentTime}\n' \
            f'<b>Total Disk Space:</b> {total}\n' \
            f'<b>Used:</b> {used}  ' \
            f'<b>Free:</b> {free}\n\n' \
            f'📊Data Usage\n<b>Upload:</b> {sent}\n' \
            f'<b>Download:</b> {recv}\n\n' \
            f'<b>CPU:</b> {cpuUsage}%\n' \
            f'<b>RAM:</b> {memory}%\n' \
            f'<b>DISK:</b> {disk}%'
    update.effective_message.reply_photo(IMAGE_URL, stats, parse_mode=ParseMode.HTML)


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
         update.effective_message.reply_text(
            "Edotensei success!!!✨, /help di pm anjing!!!🗿"
        )

def restart(update, context):
    restart_message = sendMessage("Restarting, Please wait!", context.bot, update)
    # Save restart message object in order to reply to it after restarting
    with open(".restartmsg", "w") as f:
        f.truncate(0)
        f.write(f"{restart_message.chat.id}\n{restart_message.message_id}\n")
    fs_utils.clean_all()
    alive.terminate()
    os.execl(executable, executable, "-m", "bot")


def ping(update, context):
    start_time = int(round(time.time() * 1000))
    reply = sendMessage("Starting Ping", context.bot, update)
    end_time = int(round(time.time() * 1000))
    editMessage(f'{end_time - start_time} ms', reply)


def log(update, context):
    sendLogFile(context.bot, update)


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
                user.id == OWNER_ID
            ):
                keyb += [
                    [
                        InlineKeyboardButton(
                            text="👤Owner", callback_data="help_staff"
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


def staff_help(update, context):
    chat = update.effective_chat
    user = update.effective_user

    if chat.type != chat.PRIVATE:
        update.effective_message.reply_text(
            "Contact me in PM to get the list of staff's command"
        )
        return

    if (
        user.id == OWNER_ID
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


def get_help(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user
    args = update.effective_message.text.split(None, 1)

    # ONLY send help in PM
    if chat.type != chat.PRIVATE:

        update.effective_message.reply_text(
            "Use this command in private chat bitch, motherfucker.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="⚙️Help",
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
            user.id == OWNER_ID
        ):
            keyb += [
                [
                    InlineKeyboardButton(
                        text="👤Owner", callback_data="help_staff"
                    )
                ]
            ]

        send_help(chat.id, HELP_STRINGS, InlineKeyboardMarkup(keyb))

botcmds = [
        (f'{BotCommands.HelpCommand}','Get Detailed Help'),
        (f'{BotCommands.MirrorCommand}', 'Start Mirroring'),
        (f'{BotCommands.TarMirrorCommand}','Start mirroring and upload as .tar'),
        (f'{BotCommands.ZipMirrorCommand}','Start mirroring and upload as .zip'),
        (f'{BotCommands.UnzipMirrorCommand}','Extract files'),
        (f'{BotCommands.CloneCommand}','Copy file/folder to Drive'),
        (f'{BotCommands.CountCommand}','Count file/folder of Drive link'),
        (f'{BotCommands.DeleteCommand}','Delete file from Drive'),
        (f'{BotCommands.WatchCommand}','Mirror Youtube-dl support link'),
        (f'{BotCommands.TarWatchCommand}','Mirror Youtube playlist link as .tar'),
        (f'{BotCommands.CancelMirror}','Cancel a task'),
        (f'{BotCommands.CancelAllCommand}','Cancel all tasks'),
        (f'{BotCommands.ListCommand}','Searches files in Drive'),
        (f'{BotCommands.StatusCommand}','Get Mirror Status message'),
        (f'{BotCommands.StatsCommand}','Bot Usage Stats'),
        (f'{BotCommands.PingCommand}','Ping the Bot'),
        (f'{BotCommands.RestartCommand}','Restart the bot [owner/sudo only]'),
        (f'{BotCommands.LogCommand}','Get the Bot Log [owner/sudo only]')
    ]


def main():
    fs_utils.start_cleanup()

    if IS_VPS:
        asyncio.get_event_loop().run_until_complete(start_server_async(SERVER_PORT))

    # Check if the bot is restarting
    if os.path.isfile(".restartmsg"):
        with open(".restartmsg") as f:
            chat_id, msg_id = map(int, f)
        bot.edit_message_text("Restarted successfully!", chat_id, msg_id)
        os.remove(".restartmsg")
    bot.set_my_commands(botcmds)

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
    stats_handler = CommandHandler(BotCommands.StatsCommand,
                                   stats, filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
    log_handler = CommandHandler(BotCommands.LogCommand, log, filters=CustomFilters.owner_filter | CustomFilters.sudo_user, run_async=True)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(ping_handler)
    dispatcher.add_handler(restart_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(help_callback_handler)
    dispatcher.add_handler(help_staff_handler)
    dispatcher.add_handler(stats_handler)
    dispatcher.add_handler(log_handler)
    updater.start_polling(drop_pending_updates=IGNORE_PENDING_REQUESTS)
    LOGGER.info("Bot Started!")
    signal.signal(signal.SIGINT, fs_utils.exit_clean_up)

app.start()
main()
idle()
