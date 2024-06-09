# Test-Parser-Bot

Test-Parser-Bot — это простой инструмент для сбора фотографий и сообщений из открытых групп и чатов в Telegram.

## Navigation

1. [Features](#features) ✨

2. [Stack](#stack) 🛠️

3. [Quick Start](#quick-start) 🚀

## Features

- **Сбор фотографий:** 📂 Собирайте фотографии из открытых групп и чатов.

- **Сбор сообщений:** 📝 Собирайте сообщения из открытых групп и чатов.

## Stack

- Python
- Aiogram
- Aiohttp
- Beautifulsoup4
- Requests

## Quick Start

Выполните следующие шаги, чтобы настроить проект локально на вашем компьютере.

### Предварительные условия

Убедитесь, что на вашем компьютере установлено следующее:

- [Git](https://git-scm.com/downloads)
- [Python](https://www.python.org/downloads/)

**Клонирование репозитория**

```sh
git clone https://github.com/avariceJS/Test-Parser-Bot.git
cd Test-Parser-Bot
```

**Установка зависимостей**

```sh
python -m venv myenv

# Windows:
myenv\Scripts\activate

# macOS/Linux:
source myenv/bin/activate

pip install -r requirements.txt
```

Укажите токен бота в ".env" файл

**Запуск проекта**

```sh
python bot.py
```

Запустите вашего бота в telegram командой "/start"
