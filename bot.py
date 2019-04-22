#!/usr/bin/env python3

import logging

logging.basicConfig(level=logging.DEBUG)

import os

from pathlib import Path

import redis

from telegram import ChatAction
from telegram.ext import Updater, MessageHandler
from telegram.ext.filters import Filters


TG_TOKEN = os.environ["POSTER_TOKEN"]
SUBS_LOC = Path('/var/lib/subscribebot')


def new_file(update, context):
    if not update.message.document.file_name.endswith('.xml'):
        update.message.reply_text("If you send me a file, it should be a subscriptions list from youtube.")

    context.bot.send_chat_action(update.effective_chat.id, ChatAction.UPLOAD_DOCUMENT)
    file = update.message.document.get_file()
    file.download(custom_path=SUBS_LOC / '{}.xml'.format(update.effective_chat.id))
    update.message.reply_text("Your subscriptions file has been saved, you will now receive new video's from your subscriptions every so often.")


def main():
    updater = Updater(token=TG_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    new_file_h = MessageHandler(Filters.document, new_file)
    dispatcher.add_handler(new_file_h)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
