# Base
import shutil
from dotenv import load_dotenv
import requests
import re
import os
import aiohttp

# bs4
from bs4 import BeautifulSoup, Tag

load_dotenv()

# Bot token
BOT_TOKEN = f'{os.getenv("BOT_TOKEN")}'

# Bot token for API requests
FILES_FOLDER = "./files"
GROUP_DATA_FILE = "telegram_group_data.txt"


# Function to delete a folder and its contents
def delete_folder(folder_path):
    try:
        shutil.rmtree(folder_path)
        print("Папка успешно удалена:", folder_path)
    except OSError as e:
        print("Ошибка при удалении папки:", folder_path, e)


# Function to delete a file
def delete_file(file_path):
    try:
        os.remove(file_path)
        print("Файл успешно удален:", file_path)
    except OSError as e:
        print("Ошибка при удалении файла:", file_path, e)


# Delete existing folder and file
delete_folder(FILES_FOLDER)
delete_file(GROUP_DATA_FILE)

os.makedirs(FILES_FOLDER)


# Function to extract filename from Content-Disposition header
def get_filename_from_cd(cd):
    if not cd:
        return None
    fname = re.findall("filename=(.+)", cd)
    if len(fname) == 0:
        return None
    return fname[0]


# Function to parse HTML content using BeautifulSoup
async def dom_all(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                html_text = await response.text()
                return BeautifulSoup(html_text, "html.parser")
            else:
                print("Ошибка при получении HTML-контента:", url, response.status)


# Function to download a file from a URL
async def download(url, file_path=FILES_FOLDER + "/"):
    if url:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    name = url.split("/")[-1][:20]
                    content_type = response.headers.get("content-type")
                    if content_type:
                        if "image" in content_type:
                            file_extension = content_type.split("/")[1]
                            filename = "{}.{}".format(name, file_extension)
                            file = os.path.join(file_path, filename)
                            if not os.path.exists(file_path):
                                os.makedirs(file_path)
                            with open(file, "wb") as f:
                                async for data in response.content.iter_any():
                                    f.write(data)
                            return file
                        else:
                            print("Пропущен файл с типом контента:", content_type)
                    else:
                        print("Не удалось определить тип контента для файла:", url)
                else:
                    print("Ошибка при загрузке файла:", url, response.status)


# Function to get the number of members in a chat
def get_chat_members_count(chat_id):
    url = (
        f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMembersCount?chat_id={chat_id}"
    )
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data["ok"]:
            return data["result"]
    return None


# Function to get the usernames of members in a chat
def get_chat_members(chat_id):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMembers?chat_id={chat_id}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data["ok"]:
            members = [member["user"]["username"] for member in data["result"]]
            return members
    return None


# Function to parse all messages from a group/channel
async def parse_all(url, limit, is_download=False, iteration=0, messages=[]):
    soup = await dom_all(url)

    contents = soup.findAll("div", {"class": "tgme_widget_message_wrap"})
    for content in contents:
        result = {}

        url = content.find("a")
        if url:
            result["url"] = url.get("href")

        text = content.find("div", {"class": "tgme_widget_message_text"})
        if text:
            result["text"] = text.text

        photo = content.find("a", {"class": "tgme_widget_message_photo_wrap"})
        if photo:
            photo_url = photo.get("style").split("'")[1]
            result["photo"] = photo_url
            if is_download:
                await download(photo_url)

        views = content.find("span", {"class": "tgme_widget_message_views"})
        if views:
            result["views"] = views.text

        author_name = content.find("div", {"class": "tgme_widget_message_author"})
        if author_name:
            result["author_name"] = author_name.find("span").text

        author_url = content.find("div", {"class": "tgme_widget_message_author"})
        if author_url:
            result["author_url"] = author_url.find("a").get("href")

        time = (
            content.find("a", {"class": "tgme_widget_message_date"})
            .find("time")
            .get("datetime")
        )
        result["time"] = time

        groupfiles = []
        medias = content.find("div", {"class": "tgme_widget_message_grouped_layer"})
        if medias:
            for media in medias.findAll("a"):
                groupfiles.append({"url": media.get("href")})
            result["media"] = groupfiles

        video = content.find("a", {"class": "tgme_widget_message_video_player"})
        if video:
            thumb = video.find("i")
            if thumb:
                result["video_thumb"] = thumb.get("style").split("'")[1]
            video_block = video.find("video")
            if video_block:
                result["video_url"] = video_block.get("src")

        messages.append(result)

    prev_link = soup.find(rel="prev")
    if (
        prev_link
        and isinstance(prev_link, Tag)
        and (int(limit) == 0 or int(iteration) < int(limit))
    ):
        iteration += 1
        await parse_all(
            "https://t.me{}".format(prev_link.get("href")),
            limit,
            is_download,
            iteration,
            messages,
        )
    return messages


# Function to count files in a folder
def count_files_in_folder(folder_path):
    if os.path.exists(folder_path):
        files = os.listdir(folder_path)
        return len(files)
    else:
        return 0


# Main function to parse messages and download media files if required
async def parser_main(url, limit, is_download, chat_id):
    if "/s/" not in url:
        url_parts = url.split("//")
        if len(url_parts) > 1:
            url = url_parts[0] + "//" + url_parts[1].replace("/", "/s/", 1)
    res = await parse_all(url, limit)

    # Write parsed data to file
    with open(GROUP_DATA_FILE, "w", encoding="utf-8") as txt_file:
        if res is not None:
            for message in res:
                txt_file.write(str(message) + "\n")

    photo_files = []
    if is_download == "yes":
        if res is not None:
            for message in res:
                if "photo" in message:
                    photo_file = await download(message["photo"])
                    photo_files.append(photo_file)
    return res, GROUP_DATA_FILE, photo_files
