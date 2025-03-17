from telethon import TelegramClient, functions
from dotenv import load_dotenv
import os

# .env 파일에서 환경 변수 로드
load_dotenv()

# API 설정
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
bot_token = os.getenv('BOT_TOKEN')

# 기존 세션 파일을 사용하여 클라이언트 초기화
client = TelegramClient('user_session', api_id, api_hash)

async def main():
    await client.start(bot_token=bot_token)
    
    # 모든 대화 가져오기
    dialogs = await client(functions.messages.GetDialogsRequest(
        offset_date=None,
        offset_id=0,
        offset_peer='me',
        limit=100,
        hash=0
    ))

    for dialog in dialogs.chats:
        print(f'Name: {dialog.title}, ID: {dialog.id}, Type: {type(dialog).__name__}')

with client:
    client.loop.run_until_complete(main())
