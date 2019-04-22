#!/usr/bin/env python3

import logging

logging.basicConfig(level=logging.DEBUG)

import os
import time
import xml.etree.ElementTree as ET

from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import redis
import requests

from telegram.bot import Bot


TG_TOKEN = os.environ["POSTER_TOKEN"]
SUBS_LOC = Path('/var/lib/subscribebot')
bot = Bot(TG_TOKEN)

red = redis.StrictRedis(host=os.environ["POSTER_REDIS_HOST"])

headers = {'User-Agent': 'ubuntu-server:youtubehaiku-archive:0.0.1 (by /u/pingiun)'}


def handle_file(file, root):
    user = file.split('.')[0]
    last_upload = float(red.hget('subscribebot:last_checks', user))
    if not last_upload:
        last_upload = time.time()
        red.hset('subscribebot:last_checks', user, last_upload)

    if root[0].tag != 'body':
        logging.debug(file + " not an opml file")
        return
    if root[0][0].attrib['text'] != 'YouTube Subscriptions':
        logging.debug(file + " not an opml file")
        return
    print("Handling file for " + file)
    to_download = list()
    for channel in root[0][0]:
        if 'xmlUrl' not in channel.attrib:
            print("No url available")
            continue
        feed_url = channel.attrib['xmlUrl']
        print("Checking channel " + channel.attrib['title'])

        r = requests.get(feed_url)
        if r.status_code != 200:
            print("Unable to load channel " + channel.attrib['title'])
        videos = ET.fromstring(r.text)

        for thing in videos:
            if thing.tag != '{http://www.w3.org/2005/Atom}entry':
                continue
            published = thing.find('{http://www.w3.org/2005/Atom}published')
            if published is None:
                print(thing.tag + " No published?")
                continue
            upload_timestamp = datetime.strptime(published.text, "%Y-%m-%dT%H:%M:%S+00:00").timestamp()
            # print("{} < {} = {}".format(upload_timestamp, last_upload, upload_timestamp < last_upload))
            if upload_timestamp < last_upload:
                continue
            video_id = thing.find('{http://www.youtube.com/xml/schemas/2015}videoId')
            print("Downloading " + video_id.text)

            to_download.append((upload_timestamp, video_id.text))

    videos = sorted(to_download, key=lambda x: x[0])
    for _, video in videos:
        bot.send_message(user, "https://youtu.be/" + video)

    red.hset('subscribebot:last_checks', user, time.time())

def main():
    for file in os.listdir(SUBS_LOC):
        root = ET.parse(SUBS_LOC / file).getroot()
        try:
            handle_file(file, root)
        except Exception as e:
            logging.exception(e)

if __name__ == '__main__':
    main()
