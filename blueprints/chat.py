from vkbottle.bot import Blueprint, Message
from vkbottle import ErrorHandler
from deep_translator import GoogleTranslator
import re
import requests
import aiohttp
import aiofiles
from vkbottle.tools import PhotoMessageUploader, VideoUploader
from datetime import datetime
import locale
locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
import os


bp = Blueprint('Commands for chat')
bp.labeler.vbml_ignore_case = True
error_handler = ErrorHandler(redirect_arguments=False, raise_exceptions=False)

async def download_media(url, filename):
    chunk_size = 60 * 1024 * 1024

    async with aiohttp.ClientSession() as session:
        async with session.post('https://www.genmirror.com/includes/process.php?action=update', data={'u': url}) as response:
            async with aiofiles.open(filename, 'wb') as file:
                while True:
                    chunk = await response.content.read(chunk_size)
                    if not chunk:
                        break
                    await file.write(chunk)

@bp.on.chat_message(text=['x <url>', 'x перевод <url>', 'х <url>', 'х перевод <url>', 't <url>', 't перевод <url>', 'т <url>', 'т перевод <url>'])
async def twitter_handler(message: Message, translate=None, url=None):
    if message.from_id < 0 or message.from_id == 308737013:
        print('self')
        return

    url = str(url)
    if url is None:
        await message.answer('Нет url')
        return

    id = re.search(r'(?<=status\/)\d*', url)
    if not id:
        await message.answer('Некорректная ссылка')

    twitter_text = ''
    author = ''
    photos = []
    videos = []
    attachment = []
    likes = 0
    retweets = 0
    timestamp = 0
    q_author = ''
    q_twitter_text = ''

    id = id.group(0)
    response = requests.get('https://api.fxtwitter.com/Twitter/status/' + id)
    if response.status_code != 200:
        await message.answer('Некорректная ссылка')
        return

    content = response.json()['tweet']
    author = '@' + content['author']['screen_name']
    twitter_text = content['text']
    likes = content['likes']
    retweets = content['retweets']
    timestamp = content['created_timestamp']
    str_date = datetime.fromtimestamp(timestamp).strftime('%d %b %Y\n%H:%M (GTM+3)')

    if 'media' in content:
        if 'photos' in content['media']:
            photos = [x['url'] for x in content['media']['photos']]
        if 'videos' in content['media']:
            videos = [x['url'] for x in content['media']['videos']]

    if 'quote' in content:
        q_author = '@' + content['quote']['author']['screen_name']
        q_twitter_text = content['quote']['text']
        if 'media' in content['quote']:
            if 'photos' in content['quote']['media']:
                photos = photos + [x['url'] for x in content['quote']['media']['photos']]
            if 'videos' in content['quote']['media']:
                videos = videos + [x['url'] for x in content['quote']['media']['videos']]

    if 'quote' in content:
        text = 'Твит от: ' + author + '\n\n' + twitter_text + '\n\nРепост: '+ q_author + '\n\n' + q_twitter_text
    else:
        text = 'Твит от: ' + author + '\n\n' + twitter_text

    if 'перевод' in message.text:
        if 'quote' in content:
            text = text + '\n\nПеревод:\n' + GoogleTranslator(
                                source='auto', target='ru').translate(twitter_text + '\n\n' + q_twitter_text)
        else:
            text = text + '\n\nПеревод:\n' + GoogleTranslator(
                                source='auto', target='ru').translate(twitter_text)

    text += '\n\n' + str_date
    if likes or retweets:
        text += '\n\n'
        if likes:
            text += '❤︎' + str(likes) + ' '
        if retweets:
            text += '↪' + str(retweets)

    if photos:
        photo_uploader = PhotoMessageUploader(bp.api)
        for photo in photos:
            url = photo
            filename = str(message.id) + '.tmp'
            await download_media(url, filename)
            img = await photo_uploader.upload(
                file_source=filename
            )
            attachment.append(img)
            os.remove(filename)
    if videos:
        video_uploader = VideoUploader(bp.api)
        for video in videos:
            url = video
            filename = str(message.id) + '.tmp'
            await download_media(url, filename)
            img = await video_uploader.upload(
                file_source=filename
            )
            attachment.append(img)
            os.remove(filename)

    if attachment:
        await message.answer(text, attachment=attachment)
    else:
        await message.answer(text)
