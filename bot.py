from telethon import TelegramClient, events
from dotenv import load_dotenv
import os

# .env 파일에서 환경 변수 로드
load_dotenv()

# API 설정
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
bot_token = os.getenv('BOT_TOKEN')

# 클라이언트 초기화
client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

async def main():
    # 봇이 작동 중인지 확인
    me = await client.get_me()
    print(f"Bot is working: {me.username}")

    # 예시: 채팅에서 메시지를 수신하고 응답
    @client.on(events.NewMessage)
    async def handler(event):
        await event.respond('Hello! I am your bot.')

    # 봇이 계속 실행되도록 유지
    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())
