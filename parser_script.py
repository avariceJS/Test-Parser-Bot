import requests
import json
import re
import os
from bs4 import BeautifulSoup

messages = []
limit = 0
iteration = 0
bot_token = '6616595798:AAFRxsUqV4Bp8hqiA1HcI_bYnpehkE25qHM'

def get_filename_from_cd(cd):
    if not cd:
        return None
    fname = re.findall('filename=(.+)', cd)
    if len(fname) == 0:
        return None
    return fname[0]

def domAll(url):
    html_text = requests.get(url).text
    return BeautifulSoup(html_text, 'html.parser')

def download(url, file_path='./files/'):
    if url:
        r = requests.get(url, allow_redirects=True)
        name = url.split('/')[-1][:20]
        content_type = r.headers.get('content-type')
        if content_type:
            file_extension = content_type.split('/')[1]
            filename = '{}.{}'.format(name, file_extension)
            file = os.path.join(file_path, filename)
            if not os.path.exists(file_path):
                os.makedirs(file_path)
            with open(file, 'wb') as f:
                f.write(r.content)

def get_chat_members_count(chat_id):
    url = f"https://api.telegram.org/bot{bot_token}/getChatMembersCount?chat_id={chat_id}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data["ok"]:
            return data["result"]
    return None

def get_chat_members(chat_id):
    url = f"https://api.telegram.org/bot{bot_token}/getChatMembers?chat_id={chat_id}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data["ok"]:
            members = [member["user"]["username"] for member in data["result"]]
            return members
    return None

def parse_all(url):
    global iteration, limit
    soup = domAll(url)

    contents = soup.findAll('div', {'class': 'tgme_widget_message_wrap'})
    for content in contents:
        result = {}

        url = content.find('a')
        if url:
            result['url'] = url.get('href')

        text = content.find('div', {'class': 'tgme_widget_message_text'})
        if text:
            result['text'] = text.text

        photo = content.find('a', {'class': 'tgme_widget_message_photo_wrap'})
        if photo:
            photo_url = photo.get('style').split("'")[1]
            result['photo'] = photo_url
            download(photo_url)

        views = content.find('span', {'class': 'tgme_widget_message_views'})
        if views:
            result['views'] = views.text

        author_name = content.find('div', {'class': 'tgme_widget_message_author'})
        if author_name:
            result['author_name'] = author_name.find('span').text

        author_url = content.find('div', {'class': 'tgme_widget_message_author'})
        if author_url:
            result['author_url'] = author_url.find('a').get('href')

        time = content.find('a', {'class': 'tgme_widget_message_date'}).find('time').get('datetime')
        result['time'] = time

        groupfiles = []
        medias = content.find('div', {'class': 'tgme_widget_message_grouped_layer'})
        if medias:
            for media in medias.findAll('a'):
                groupfiles.append({'url': media.get('href')})
            result['media'] = groupfiles

        video = content.find('a', {'class': 'tgme_widget_message_video_player'})
        if video:
            thumb = video.find('i')
            if thumb:
                result['video_thumb'] = thumb.get('style').split("'")[1]
            video_block = video.find('video')
            if video_block:
                result['video_url'] = video_block.get('src')

        messages.append(result)
    
    prev_link = soup.find(rel="prev")
    if prev_link and (limit == 0 or iteration < limit):
        iteration += 1
        parse_all('https://t.me{}'.format(prev_link.get('href')))

    return messages

def parser_main(url, limit, is_download, chat_id):

    if "/s/" not in url:
        url_parts = url.split("//")
        if len(url_parts) > 1:
            url = url_parts[0] + "//" + url_parts[1].replace("/", "/s/", 1)
    res = parse_all(url)

    members_count = get_chat_members_count(chat_id)
    if members_count is not None:
        print("Количество участников в группе:", members_count)
    else:
        print("Не удалось получить количество участников группы.")

    members = get_chat_members(chat_id)
    if members is not None:
        print("Никнеймы участников группы:")
        print(", ".join(members))
    else:
        print("Не удалось получить список участников группы.")

    for message in res:
        print(json.dumps(message, ensure_ascii=False))

    json_string = json.dumps(res, ensure_ascii=False)
    with open('telegram_group_data.json', 'w', encoding='utf-8') as json_file:
        json_file.write(json_string)
