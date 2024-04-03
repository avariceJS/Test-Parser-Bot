import re
import requests

def get_chat_id(bot_token, url):

    match = re.search(r'(?<=https://t.me/)(\w+)', url)
    if match:
        name_channel = match.group(0)

        api_url = f"https://api.telegram.org/bot{bot_token}/getChat?chat_id=@{name_channel}"
        response = requests.get(api_url)
        if response.status_code == 200:
            data = response.json()
            if data["ok"]:
                chat_id = data["result"]["id"]
                return chat_id
    return None