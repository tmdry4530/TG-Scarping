from telethon import TelegramClient, events
from telethon.tl.types import User, MessageMediaPhoto
from dotenv import load_dotenv
import os
import re
import platform
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging
import sys
import pyautogui
import hashlib
from collections import OrderedDict
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

class Config:
    API_ID = os.getenv('API_ID')
    API_HASH = os.getenv('API_HASH')
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    TARGET_GROUP = int(os.getenv('TARGET_GROUP'))
    EXCLUDED_GROUP_IDS = os.getenv('EXCLUDED_GROUP_IDS', '').split(',')
    KEYWORD = 'open.kakao.com'
    EXCLUDE_KEYWORDS = os.getenv('EXCLUDE_KEYWORDS', '').split(',')
    IMAGE_DIR = os.path.join(os.getcwd(), 'image') + os.path.sep
    PAGE_LOAD_WAIT = 2.5
    
    # 운영체제별 설정
    SYSTEM = platform.system()
    if SYSTEM == 'Darwin':  # macOS
        CLICK_COORDINATES = [(827, 480), (956, 260), (837, 410)]  # macOS 좌표 (예시값, 실제 맥에서 조정 필요)
    else:  # Windows 또는 기타
        CLICK_COORDINATES = [(1994, 606), (2118, 360), (2004, 510)]  # 원래 윈도우 좌표
    
    CLICK_INTERVAL = 0.2

class WebDriver:
    def __init__(self):
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        if Config.SYSTEM == 'Windows':
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        logging.info(f"ChromeDriver initialized on {Config.SYSTEM}")

    def navigate(self, url):
        self.driver.get(url)
        time.sleep(Config.PAGE_LOAD_WAIT)

    def click_button(self):
        try:
            button = self.driver.find_element(By.CSS_SELECTOR, 'button')
            button.click()
            time.sleep(Config.PAGE_LOAD_WAIT)
        except Exception as e:
            logging.error(f"Failed to click button: {e}")

    def perform_clicks(self):
        # 현재 화면 크기 확인
        screen_width, screen_height = pyautogui.size()
        logging.info(f"Screen size: {screen_width}x{screen_height}")
        
        for x, y in Config.CLICK_COORDINATES:
            # 화면 밖으로 나가지 않도록 좌표 조정
            safe_x = min(x, screen_width - 10)
            safe_y = min(y, screen_height - 10)
            
            try:
                pyautogui.moveTo(safe_x, safe_y, duration=0.1)
                pyautogui.click()
                time.sleep(Config.CLICK_INTERVAL)
                logging.info(f"Clicked at coordinates: ({safe_x}, {safe_y})")
            except Exception as e:
                logging.error(f"Failed to click at coordinates ({safe_x}, {safe_y}): {e}")

    def quit(self):
        self.driver.quit()

class MessageCache:
    def __init__(self, max_size=1000):
        self.cache_file = 'message_cache.json'
        self.max_size = max_size
        self.cache = OrderedDict()
        self._load_cache()
    
    def _load_cache(self):
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                self.cache = OrderedDict(json.load(f))
        except FileNotFoundError:
            self.cache = OrderedDict()
    
    def _save_cache(self):
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(list(self.cache.items()), f, ensure_ascii=False)
    
    def add_message(self, message):
        message_hash = hashlib.md5(message.encode()).hexdigest()
        
        if message_hash in self.cache:
            return False
        
        if len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)
        
        self.cache[message_hash] = message
        self._save_cache()
        return True

class MessageHandler:
    def __init__(self, user_client, bot_client, web_driver, message_cache):
        self.user_client = user_client
        self.bot_client = bot_client
        self.web_driver = web_driver
        self.message_cache = message_cache

    def extract_urls(self, text):
        return re.findall(r'(https?://\S+)', text)

    def extract_hyperlink_urls(self, message):
        urls = []
        if message.entities:
            urls.extend(entity.url for entity in message.entities if hasattr(entity, 'url'))
        return urls

    async def send_message_via_bot(self, message_text, media=None):
        try:
            await self.bot_client.send_message(Config.TARGET_GROUP, message_text, file=media)
            logging.info(f"Bot sent message to {Config.TARGET_GROUP}")
        except Exception as e:
            logging.error(f"Failed to send message: {e}")

    async def process_message(self, event):
        if self._should_ignore_message(event):
            return

        urls = self._collect_urls(event)
        keyword_urls = list(set(url for url in urls if Config.KEYWORD in url))

        if keyword_urls and self.message_cache.add_message(event.message.message):
            await self._handle_message(event, keyword_urls)

    def _should_ignore_message(self, event):
        sender = event.sender
        if isinstance(sender, User) and sender.bot:
            return True

        if str(event.chat_id) in Config.EXCLUDED_GROUP_IDS:
            return True

        if any(keyword in event.message.message for keyword in Config.EXCLUDE_KEYWORDS):
            return True

        return False

    def _collect_urls(self, event):
        urls = self.extract_urls(event.message.message)
        urls.extend(self.extract_hyperlink_urls(event.message))
        
        if event.message.media and hasattr(event.message.media, 'webpage'):
            if hasattr(event.message.media.webpage, 'url'):
                urls.append(event.message.media.webpage.url)
        
        return urls

    async def _handle_message(self, event, keyword_urls):
        message_to_send = f"Keyword detected message:\n{event.message.message}\n\nLinks:\n"
        message_to_send += "\n".join(keyword_urls)

        try:
            if event.message.media and isinstance(event.message.media, MessageMediaPhoto):
                if not os.path.exists(Config.IMAGE_DIR):
                    os.makedirs(Config.IMAGE_DIR)
                
                photo_path = await event.download_media(file=Config.IMAGE_DIR)
                await self.send_message_via_bot(message_to_send, media=photo_path)
            else:
                await self.send_message_via_bot(message_to_send)

            for url in keyword_urls:
                await self._process_url(url)

        except Exception as e:
            logging.error(f"Error handling message: {e}")

    async def _process_url(self, url):
        try:
            self.web_driver.navigate(url)
            self.web_driver.click_button()
            self.web_driver.perform_clicks()
        except Exception as e:
            logging.error(f"Error processing URL {url}: {e}")

async def main():
    user_client = TelegramClient('user_session', Config.API_ID, Config.API_HASH)
    bot_client = TelegramClient('bot_session', Config.API_ID, Config.API_HASH)
    
    try:
        web_driver = WebDriver()
        message_cache = MessageCache()
        handler = MessageHandler(user_client, bot_client, web_driver, message_cache)

        await bot_client.start(bot_token=Config.BOT_TOKEN)
        await user_client.start()
        
        logging.info(f"Bot started on {Config.SYSTEM} platform")
        
        @user_client.on(events.NewMessage)
        async def message_handler(event):
            await handler.process_message(event)

        await user_client.run_until_disconnected()
    except Exception as e:
        logging.error(f"Error in main process: {e}")
    finally:
        if 'web_driver' in locals():
            web_driver.quit()
        await bot_client.disconnect()
        await user_client.disconnect()

if __name__ == '__main__':
    try:
        import asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Program terminated by user")
    except Exception as e:
        logging.error(f"Program terminated with error: {e}") 