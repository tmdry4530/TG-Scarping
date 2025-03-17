#!/usr/bin/env python3
import os
import re
import asyncio
import logging
import json
import time
import sys
import hashlib
from collections import OrderedDict

from telethon import TelegramClient, events
from telethon.tl.types import MessageMediaPhoto
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import pyautogui
from dotenv import load_dotenv

# ------------------------------------------------------------------------------
# 로깅 및 환경변수 로드
# ------------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()

# ------------------------------------------------------------------------------
# Config 클래스: 기본 설정 (.env 파일로부터 로드)
# ------------------------------------------------------------------------------
class Config:
    API_ID = int(os.getenv('API_ID', '0'))
    API_HASH = os.getenv('API_HASH', '')
    BOT_TOKEN = os.getenv('BOT_TOKEN', None)
    TARGET_GROUP = int(os.getenv('TARGET_GROUP', '0')) if os.getenv('TARGET_GROUP', '0') else None

    EXCLUDED_GROUP_IDS = {int(x.strip()) for x in os.getenv('EXCLUDED_GROUP_IDS', '').split(',') if x.strip()}
    BOT_CHANNEL_IDS = {int(x.strip()) for x in os.getenv('BOT_CHANNEL_IDS', '').split(',') if x.strip()}

    KEYWORD = os.getenv('KEYWORD', 'open.kakao.com')
    EXCLUDE_KEYWORDS = [kw.strip() for kw in os.getenv('EXCLUDE_KEYWORDS', '').split(',') if kw.strip()]

    IMAGE_DIR = os.getenv('IMAGE_DIR', 'image/')

    CLICK_COORDINATES = []
    click_coords_env = os.getenv('CLICK_COORDINATES', '1994,606;2118,360;2004,510')
    for coord in click_coords_env.split(';'):
        parts = coord.split(',')
        if len(parts) == 2:
            try:
                x = int(parts[0].strip())
                y = int(parts[1].strip())
                CLICK_COORDINATES.append((x, y))
            except ValueError:
                pass

    CLICK_INTERVAL = float(os.getenv('CLICK_INTERVAL', '0.2'))
    PAGE_LOAD_WAIT = float(os.getenv('PAGE_LOAD_WAIT', '2.5'))

# ------------------------------------------------------------------------------
# 런타임에서 변경 가능한 설정 (기본값은 Config에서 로드)
# ------------------------------------------------------------------------------
runtime_config = {
    'KEYWORD': Config.KEYWORD,
    'CLICK_INTERVAL': Config.CLICK_INTERVAL,
    'PAGE_LOAD_WAIT': Config.PAGE_LOAD_WAIT,
    'IMAGE_DIR': Config.IMAGE_DIR,
}
# 메시지 모니터링 시 제외할 키워드 (초기값은 Config.EXCLUDE_KEYWORDS)
runtime_excluded_keywords = set(Config.EXCLUDE_KEYWORDS)

# ------------------------------------------------------------------------------
# WebDriver 클래스: Selenium을 이용한 웹 제어
# ------------------------------------------------------------------------------
class WebDriver:
    def __init__(self):
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        logging.info("ChromeDriver initialized")
    def navigate(self, url):
        logging.info(f"Navigating to {url}")
        self.driver.get(url)
        time.sleep(Config.PAGE_LOAD_WAIT)
    def click_button(self):
        try:
            button = self.driver.find_element(By.CSS_SELECTOR, 'button')
            button.click()
            time.sleep(Config.PAGE_LOAD_WAIT)
        except Exception as e:
            logging.error(f"Error clicking button: {e}")
    def perform_clicks(self):
        for (x, y) in Config.CLICK_COORDINATES:
            logging.info(f"Clicking at ({x}, {y})")
            pyautogui.moveTo(x, y, duration=0.1)
            pyautogui.click()
            time.sleep(Config.CLICK_INTERVAL)
    def quit(self):
        try:
            self.driver.quit()
            logging.info("ChromeDriver closed")
        except Exception as e:
            logging.error(f"Error quitting WebDriver: {e}")

# ------------------------------------------------------------------------------
# MessageCache: 중복 메시지 방지를 위한 캐시 (파일 기반)
# ------------------------------------------------------------------------------
class MessageCache:
    def __init__(self, max_size=1000):
        self.cache_file = 'message_cache.json'
        self.max_size = max_size
        self.cache = OrderedDict()
        self._load_cache()
    def _load_cache(self):
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                items = json.load(f)
                self.cache = OrderedDict(items)
        except FileNotFoundError:
            self.cache = OrderedDict()
    def _save_cache(self):
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(list(self.cache.items()), f, ensure_ascii=False)
    def add_message(self, message):
        message_hash = hashlib.md5(message.encode('utf-8')).hexdigest()
        if message_hash in self.cache:
            return False
        if len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)
        self.cache[message_hash] = message
        self._save_cache()
        return True
    def is_duplicate(self, message_text):
        message_hash = hashlib.md5(message_text.encode('utf-8')).hexdigest()
        return message_hash in self.cache

# ------------------------------------------------------------------------------
# LinkCache: 처리한 링크의 중복 여부를 확인하기 위한 캐시
# ------------------------------------------------------------------------------
class LinkCache:
    def __init__(self):
        self.cache_file = 'link_cache.json'
        self.cache = set()
        self._load_cache()
    def _load_cache(self):
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                links = json.load(f)
                self.cache = set(links)
        except FileNotFoundError:
            self.cache = set()
    def _save_cache(self):
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(list(self.cache), f, ensure_ascii=False)
    def add_link(self, link):
        if link in self.cache:
            return False
        self.cache.add(link)
        self._save_cache()
        return True
    def is_duplicate_link(self, link):
        return link in self.cache

# ------------------------------------------------------------------------------
# MessageHandler: 메시지 처리 및 URL/미디어 처리, 오픈채팅 자동 접속 기능
# ------------------------------------------------------------------------------
class MessageHandler:
    def __init__(self, user_client, bot_client, web_driver, message_cache):
        self.user_client = user_client
        self.bot_client = bot_client  # 봇 기능 미사용 시 None
        self.web_driver = web_driver
        self.message_cache = message_cache
        self.link_cache = LinkCache()
    def extract_urls(self, text):
        url_pattern = r'http[s]?://(?:[a-zA-Z0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        return re.findall(url_pattern, text)
    async def send_notification(self, message_text, media=None):
        if self.bot_client and Config.TARGET_GROUP:
            try:
                await self.bot_client.send_message(Config.TARGET_GROUP, message_text, file=media)
                logging.info(f"Notification sent to target group {Config.TARGET_GROUP}")
            except Exception as e:
                logging.error(f"Failed to send notification via bot: {e}")
        else:
            logging.info("Notification (no bot configured):")
            logging.info(message_text)
    async def process_message(self, event):
        try:
            if event.chat_id in Config.BOT_CHANNEL_IDS or event.chat_id in Config.EXCLUDED_GROUP_IDS:
                logging.info(f"Skipping message from excluded chat: {event.chat_id}")
                return
            message_text = event.message.message
            if not message_text:
                return
            if self.message_cache.is_duplicate(message_text):
                logging.info("Duplicate message detected, skipping...")
                return
            lower_text = message_text.lower()
            if any(ex_kw.lower() in lower_text for ex_kw in runtime_excluded_keywords):
                logging.info("Message contains an excluded keyword, skipping...")
                return
            urls = self.extract_urls(message_text)
            new_urls = []
            # runtime_config['KEYWORD']를 사용하여 최신 키워드 반영
            for url in urls:
                if runtime_config['KEYWORD'].lower() in url.lower():
                    if not self.link_cache.is_duplicate_link(url):
                        new_urls.append(url)
                        self.link_cache.add_link(url)
            if new_urls:
                notification_text = f"Detected message:\n{message_text}\n\nLinks:\n" + "\n".join(new_urls)
                media_file = None
                if event.message.media and isinstance(event.message.media, MessageMediaPhoto):
                    if not os.path.exists(runtime_config['IMAGE_DIR']):
                        os.makedirs(runtime_config['IMAGE_DIR'])
                    media_file = await event.download_media(file=runtime_config['IMAGE_DIR'])
                await self.send_notification(notification_text, media=media_file)
                for url in new_urls:
                    await self.process_url(url)
                self.message_cache.add_message(message_text)
        except Exception as e:
            logging.error(f"Error processing message: {e}")
    async def process_url(self, url):
        try:
            self.web_driver.navigate(url)
            self.web_driver.click_button()
            self.web_driver.perform_clicks()
        except Exception as e:
            logging.error(f"Error processing URL {url}: {e}")

# ------------------------------------------------------------------------------
# Terminal Command Monitor: 터미널에서 봇 설정 및 제외 키워드 등을 관리
#
# 지원 명령:
#   help                           - 사용 가능한 명령어와 사용법 출력
#   config list                    - 현재 설정 목록 출력
#   config get <param>             - 특정 설정 값 조회
#   config set <param> <value>     - 설정 변경 (변경 가능: KEYWORD, CLICK_INTERVAL, PAGE_LOAD_WAIT, IMAGE_DIR)
#   add <keyword>                  - 제외 키워드 추가
#   remove <keyword>               - 제외 키워드 삭제
#   list                           - 현재 제외 키워드 목록 출력
#   exit                           - 프로그램 종료
# ------------------------------------------------------------------------------
async def monitor_terminal():
    help_text = (
        "Commands:\n"
        "  help                       - Show this help message\n"
        "  config list                - List current configuration parameters\n"
        "  config get <param>         - Get the value of a configuration parameter\n"
        "  config set <param> <value> - Set the value of a configuration parameter (modifiable: KEYWORD, CLICK_INTERVAL, PAGE_LOAD_WAIT, IMAGE_DIR)\n"
        "  add <keyword>              - Add a keyword to the exclude list\n"
        "  remove <keyword>           - Remove a keyword from the exclude list\n"
        "  list                       - List current excluded keywords\n"
        "  exit                       - Exit the program\n"
    )
    print(help_text)
    loop = asyncio.get_event_loop()
    while True:
        try:
            # input()는 블로킹이므로 run_in_executor로 처리
            command = await loop.run_in_executor(None, sys.stdin.readline)
            if not command:
                continue
            command = command.strip()
            if not command:
                continue

            if command.lower() == 'help':
                print(help_text)
            elif command.lower() == 'exit':
                logging.info("Exit command received. Terminating program.")
                os._exit(0)
            elif command.lower() == 'list':
                print("Current excluded keywords:", ", ".join(runtime_excluded_keywords))
            elif command.lower().startswith("add "):
                parts = command.split(" ", 1)
                if len(parts) == 2 and parts[1].strip():
                    kw = parts[1].strip()
                    runtime_excluded_keywords.add(kw)
                    print(f"Added '{kw}' to excluded keywords.")
                else:
                    print("Usage: add <keyword>")
            elif command.lower().startswith("remove "):
                parts = command.split(" ", 1)
                if len(parts) == 2 and parts[1].strip():
                    kw = parts[1].strip()
                    if kw in runtime_excluded_keywords:
                        runtime_excluded_keywords.remove(kw)
                        print(f"Removed '{kw}' from excluded keywords.")
                    else:
                        print(f"Keyword '{kw}' not found in the excluded list.")
                else:
                    print("Usage: remove <keyword>")
            elif command.lower().startswith("config "):
                parts = command.split()
                if len(parts) < 2:
                    print("Invalid config command. Type 'help' for usage.")
                    continue
                subcommand = parts[1].lower()
                if subcommand == "list":
                    print("Current configuration parameters:")
                    for key, value in runtime_config.items():
                        print(f"  {key}: {value}")
                elif subcommand == "get":
                    if len(parts) < 3:
                        print("Usage: config get <param>")
                        continue
                    param = parts[2]
                    if param in runtime_config:
                        print(f"{param}: {runtime_config[param]}")
                    else:
                        print(f"Parameter '{param}' not found.")
                elif subcommand == "set":
                    if len(parts) < 4:
                        print("Usage: config set <param> <value>")
                        continue
                    param = parts[2]
                    value = " ".join(parts[3:])
                    if param in runtime_config:
                        old_value = runtime_config[param]
                        try:
                            if isinstance(old_value, int):
                                new_value = int(value)
                            elif isinstance(old_value, float):
                                new_value = float(value)
                            else:
                                new_value = value
                            runtime_config[param] = new_value
                            # Config 클래스의 속성도 업데이트
                            setattr(Config, param, new_value)
                            print(f"Parameter {param} updated from {old_value} to {new_value}")
                        except Exception as e:
                            print(f"Error updating parameter: {e}")
                    else:
                        print(f"Parameter '{param}' is not modifiable.")
                else:
                    print("Unknown config command. Type 'help' for usage.")
            else:
                print("Unknown command. Type 'help' for commands.")
        except Exception as e:
            logging.error(f"Error in terminal monitor: {e}")
            await asyncio.sleep(1)

# ------------------------------------------------------------------------------
# main() 함수: 텔레그램 클라이언트, 웹드라이버, 메시지 핸들러, 터미널 모니터 실행
# ------------------------------------------------------------------------------
async def main():
    user_client = TelegramClient('user_session', Config.API_ID, Config.API_HASH)
    bot_client = None
    if Config.BOT_TOKEN:
        bot_client = TelegramClient('bot_session', Config.API_ID, Config.API_HASH)
    web_driver = WebDriver()
    message_cache = MessageCache()
    handler = MessageHandler(user_client, bot_client, web_driver, message_cache)
    if bot_client:
        await bot_client.start(bot_token=Config.BOT_TOKEN)
        logging.info("Bot client started.")
    await user_client.start()
    logging.info("User client started. Listening for messages...")
    
    @user_client.on(events.NewMessage)
    async def my_event_handler(event):
        await handler.process_message(event)
    
    # 터미널 명령 모니터를 백그라운드 작업으로 실행
    asyncio.create_task(monitor_terminal())
    
    try:
        await user_client.run_until_disconnected()
    finally:
        web_driver.quit()
        if bot_client:
            await bot_client.disconnect()
        await user_client.disconnect()

# ------------------------------------------------------------------------------
# 프로그램 진입점
# ------------------------------------------------------------------------------
if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Program terminated by user")
    except Exception as e:
        logging.error(f"Program terminated with error: {e}")
