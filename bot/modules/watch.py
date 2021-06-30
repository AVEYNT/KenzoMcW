from telegram.ext import CommandHandler
from telegram import Bot, Update, BotCommand
from bot import Interval, DOWNLOAD_DIR, DOWNLOAD_STATUS_UPDATE_INTERVAL, dispatcher, LOGGER
from bot.helper.ext_utils.bot_utils import setInterval
from bot.helper.telegram_helper.message_utils import update_all_messages, sendMessage, sendStatusMessage
from .mirror import MirrorListener
from bot.helper.mirror_utils.download_utils.youtube_dl_download_helper import YoutubeDLHelper
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
import threading


def _watch(bot: Bot, update, isTar=False):
    mssg = update.message.text
    message_args = mssg.split(' ')
    name_args = mssg.split('|')
    try:
        link = message_args[1]
    except IndexError:
        msg = f"/{BotCommands.WatchCommand} [youtube-dl supported link] [quality] |[CustomName] to mirror with youtube-dl.\n\n"
        msg += "<b>Note: Quality and custom name are optional</b>\n\nExample of quality: audio, 144, 240, 360, 480, 720, 1080, 2160."
        msg += "\n\nIf you want to use custom filename, enter it after |"
        msg += f"\n\nExample:\n<code>/{BotCommands.WatchCommand} https://youtu.be/Pk_TthHfLeE 720 |Slam</code>\n\n"
        msg += "This file will be downloaded in 720p quality and it's name will be <b>Slam</b>"
        sendMessage(msg, bot, update)
        return
    try:
      if "|" in mssg:
        mssg = mssg.split("|")
        qual = mssg[0].split(" ")[2]
        if qual == "":
          raise IndexError
      else:
        qual = message_args[2]
      if qual != "audio":
        qual = f'bestvideo[height<={qual}]+bestaudio/best[height<={qual}]'
    except IndexError:
      qual = "bestvideo+bestaudio/best"
    try:
      name = name_args[1]
    except IndexError:
      name = ""
    reply_to = update.message.reply_to_message
    if reply_to is not None:
        tag = reply_to.from_user.username
    else:
        tag = None
    pswd = ""
    listener = MirrorListener(bot, update, pswd, isTar, tag)
    ydl = YoutubeDLHelper(listener)
    threading.Thread(target=ydl.add_download,args=(link, f'{DOWNLOAD_DIR}{listener.uid}', qual, name)).start()
    sendStatusMessage(update, bot)
    if len(Interval) == 0:
        Interval.append(setInterval(DOWNLOAD_STATUS_UPDATE_INTERVAL, update_all_messages))


def watchTar(update, context):
    _watch(context.bot, update, True)


def watch(update, context):
    _watch(context.bot, update)


__help__ = """
Mirror Feature :
/{BotCommands.HelpCommand}: To get this message
/{BotCommands.MirrorCommand} [download_url][magnet_link]: Start mirroring the link to Google Drive.
/{BotCommands.UnzipMirrorCommand} [download_url][magnet_link]: Starts mirroring and if downloaded file is any archive, extracts it to Google Drive
/{BotCommands.TarMirrorCommand} [download_url][magnet_link]: Start mirroring and upload the archived (.tar) version of the download
/{BotCommands.CloneCommand}: Copy file/folder to Google Drive
/{BotCommands.CountCommand}: Count file/folder of Google Drive Links
/{BotCommands.DeleteCommand} [link]: Delete file from Google Drive (Only Owner & Sudo)
/{BotCommands.WatchCommand} [youtube-dl supported link]: Mirror through youtube-dl. Click /{BotCommands.WatchCommand} for more help.
/{BotCommands.TarWatchCommand} [youtube-dl supported link]: Mirror through youtube-dl and tar before uploading
/{BotCommands.CancelMirror}: Reply to the message by which the download was initiated and that download will be cancelled
/{BotCommands.StatusCommand}: Shows a status of all the downloads
/{BotCommands.ListCommand} [search term]: Searches the search term in the Google Drive, if found replies with the link
/{BotCommands.StatsCommand}: Show Stats of the machine the bot is hosted on
/{BotCommands.AuthorizeCommand}: Authorize a chat or a user to use the bot (Can only be invoked by Owner & Sudo of the bot)
/{BotCommands.UnAuthorizeCommand}: Unauthorize a chat or a user to use the bot (Can only be invoked by Owner & Sudo of the bot)
/{BotCommands.AuthorizedUsersCommand}: Show authorized users (Only Owner & Sudo)
/{BotCommands.AddSudoCommand}: Add sudo user (Only Owner)
/{BotCommands.RmSudoCommand}: Remove sudo users (Only Owner)
/{BotCommands.LogCommand}: Get a log file of the bot. Handy for getting crash reports
/{BotCommands.ConfigMenuCommand}: Get Info Menu about bot config (Owner Only).
/{BotCommands.UpdateCommand}: Update Bot from Upstream Repo. (Owner Only).
/{BotCommands.UsageCommand}: To see Heroku Dyno Stats (Owner & Sudo only).
/{BotCommands.SpeedCommand}: Check Internet Speed of the Host
/{BotCommands.MediaInfoCommand}: Get detailed info about replied media (Only for Telegram file).
/{BotCommands.ShellCommand}: Run commands in Shell (Terminal).
/tshelp: Get help for Torrent search module.
"""

__mod_name__ = "Mirror"

mirror_handler = CommandHandler(BotCommands.WatchCommand, watch,
                                filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
tar_mirror_handler = CommandHandler(BotCommands.TarWatchCommand, watchTar,
                                    filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
dispatcher.add_handler(mirror_handler)
dispatcher.add_handler(tar_mirror_handler)
