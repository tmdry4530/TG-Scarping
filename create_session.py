from telethon import TelegramClient
from dotenv import load_dotenv
import os

# .env 파일에서 환경 변수 로드
load_dotenv()

# API ID와 해시 설정
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
phone_number = os.getenv('PHONE_NUMBER')

# 클라이언트 초기화
client = TelegramClient('session_name', api_id, api_hash)

async def main():
    await client.start(phone_number)
    print("Session file created")

with client:
    client.loop.run_until_complete(main())
