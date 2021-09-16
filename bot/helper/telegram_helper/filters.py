from telegram.ext import MessageFilter
from telegram import Message
from bot import AUTHORIZED_CHATS, SUDO_USERS, OWNER_ID, SUPPORT_USERS, SUDO_USERS, DEV_USERS ,download_dict, download_dict_lock


class CustomFilters:
    class _OwnerFilter(MessageFilter):
        def filter(self, message):
            return bool(message.from_user.id == OWNER_ID)

    owner_filter = _OwnerFilter()

    class _AuthorizedUserFilter(MessageFilter):
        def filter(self, message):
            id = message.from_user.id
            return bool(id in AUTHORIZED_CHATS or id in SUDO_USERS or id == OWNER_ID)

    authorized_user = _AuthorizedUserFilter()

    class _AuthorizedChat(MessageFilter):
        def filter(self, message):
            return bool(message.chat.id in AUTHORIZED_CHATS)

    authorized_chat = _AuthorizedChat()

    class _SudoUser(MessageFilter):
        def filter(self,message):
            return bool(message.from_user.id in SUDO_USERS)

    sudo_user = _SudoUser()
    class _Supporters(MessageFilter):
        def filter(self, message: Message):
            return bool(
                message.from_user
                and message.from_user.id in SUPPORT_USERS
                or message.from_user
                and message.from_user.id in SUDO_USERS
                or message.from_user
                and message.from_user.id in DEV_USERS
            )

    support_filter = _Supporters()

    class _Sudoers(MessageFilter):
        def filter(self, message: Message):
            return bool(
                message.from_user
                and message.from_user.id in SUDO_USERS
                or message.from_user
                and message.from_user.id in DEV_USERS
            )

    sudo_filter = _Sudoers()

    class _Devs(MessageFilter):
        def filter(self, message: Message):
            return bool(
                message.from_user and message.from_user.id in DEV_USERS
            )

    dev_filter = _Devs()

    class _MimeType(MessageFilter):
        def __init__(self, mimetype):
            self.mime_type = mimetype
            self.name = "CustomFilters.mime_type({})".format(self.mime_type)

        def filter(self, message: Message):
            return bool(
                message.document
                and message.document.mime_type == self.mime_type
            )

    mime_type = _MimeType

    class _HasText(MessageFilter):
        def filter(self, message: Message):
            return bool(
                message.text
                or message.sticker
                or message.photo
                or message.document
                or message.video
            )

    has_text = _HasText()


    class _MirrorOwner(MessageFilter):
        def filter(self, message: Message):
            user_id = message.from_user.id
            if user_id == OWNER_ID:
                return True
            args = str(message.text).split(' ')
            if len(args) > 1:
                # Cancelling by gid
                with download_dict_lock:
                    for message_id, status in download_dict.items():
                        if status.gid() == args[1] and status.message.from_user.id == user_id:
                            return True
                    else:
                        return False
            if not message.reply_to_message and len(args) == 1:
                return True
            # Cancelling by replying to original mirror message
            reply_user = message.reply_to_message.from_user.id
            return bool(reply_user == user_id)
    mirror_owner_filter = _MirrorOwner()
