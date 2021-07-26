import logging
import os
import sys
import time
import platform

from pyrogram import Client, errors
from pyrogram.types import Message

#edrep
async def edrep(msg: Message, **kwargs):
    func = msg.edit_text if msg.from_user.is_self else msg.reply
    spec = getfullargspec(func.__wrapped__).args
    await func(**{k: v for k, v in kwargs.items()
