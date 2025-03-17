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
    # 클라이언트 시작
    await client.start(phone_number)

    # 계정 정보 가져오기
    me = await client.get_me()
    
    # 계정 정보 출력
    print(f"ID: {me.id}")
    print(f"Access Hash: {me.access_hash}")

with client:
    client.loop.run_until_complete(main())
