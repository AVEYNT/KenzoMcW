import html
import requests

from telegram.ext import CommandHandler
from telegram import ParseMode

from bot import dispatcher, IMAGE_URL
from bot.helper import custom_filters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters

def infolain(update, context):
    help_string = '''
⚠️About information
𝙏𝙤𝙧𝙧𝙚𝙣𝙩 𝙨𝙚𝙖𝙧𝙘𝙝 𝙎𝙪𝙥𝙥𝙤𝙧𝙩𝙚𝙙:
nyaa.si, sukebei, 1337x, piratebay,
tgx, yts, eztv, torlock, rarbg
𝘿𝙞𝙧𝙚𝙘𝙩 𝙇𝙞𝙣𝙠 𝙨𝙪𝙥𝙥𝙤𝙧𝙩𝙚𝙙 :
Sourceforge.com, mediafire.com
zippyshare.com, mega.nz,
letsupload.io, hxfile.co, anonfiles.com, bayfiles.com, 
antfiles, fembed.com, fembed.net, femax20.com, layarkacaxxi.icu, fcdn.stream, sbplay.org, naniplay.com, naniplay.nanime.in, naniplay.nanime.biz, sbembed.com,
streamtape.com, streamsb.net, feurl.com, pixeldrain.com, racaty.net,
1fichier.com, 1drv.ms (Only works for file not folder or business account),
uptobox.com (Uptobox account must be premium)
𝙀𝙭𝙩𝙧𝙖𝙘𝙩 𝙨𝙪𝙥𝙥𝙤𝙧𝙩𝙚𝙙 𝙛𝙞𝙡𝙚𝙨:
ZIP, RAR, TAR, 7z, ISO, WIM, 
CAB, GZIP, BZIP2, APM, ARJ,
CHM, CPIO, CramFS, DEB,
DMG, FAT, HFS, LZH, LZMA,
LZMA2, MBR, MSI, MSLZ, NSIS, 
NTFS, RPM, SquashFS, UDF,
VHD, XAR, Z.
'''
    update.effective_message.reply_photo(IMAGE_URL, help_string, parse_mode=ParseMode.HTML)
    
    
INFOLAIN_HANDLER = CommandHandler(BotCommands.InfolainCommand, infolain, filters=(CustomFilters.authorized_chat | CustomFilters.authorized_user) & CustomFilters.mirror_owner_filter, run_async=True)
dispatcher.add_handler(INFOLAIN_HANDLER)