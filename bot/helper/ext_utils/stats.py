import os
import time

import shutil, psutil
from bot import app, botStartTime
from bot.helper.ext_utils import formatter
from bot.helper.ext_utils.bot_utils import get_readable_file_size, get_readable_time
from pyrogram import filters

async def bot_sys_stats():
    currentTime = get_readable_time(time.time() - botStartTime)
    total, used, free = shutil.disk_usage('.')
    total = get_readable_file_size(total)
    used = get_readable_file_size(used)
    free = get_readable_file_size(free)
    sent = get_readable_file_size(psutil.net_io_counters().bytes_sent)
    recv = get_readable_file_size(psutil.net_io_counters().bytes_recv)
    process = psutil.Process(os.getpid())
    cpuUsage = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    stats = f'<b>AVEYUBOT by AVEYNATA</b>\n' \
            f'<b>Bot Uptime:</b> <code>{currentTime}</code>\n' \
            f'<b>Bot:</b> <code>{round(process.memory_info()[0] / 1024 ** 2)} MB</code>\n' \
            f'<b>Total Disk Space:</b> <code>{total}</code>\n' \
            f'<b>Used:</b> <code>{used}</code> ' \
            f'<b>Free:</b> <code>{free}</code>\n\n' \
            f'<b>Upload:</b> <code>{sent}</code>\n' \
            f'<b>Download:</b> <code>{recv}</code>\n\n' \
            f'<b>CPU:</b> <code>{cpuUsage}%</code> ' \
            f'<b>RAM:</b> <code>{memory}%</code> ' \
            f'<b>DISK:</b> <code>{disk}%</code>'
    return stats