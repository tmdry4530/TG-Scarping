from telethon.sync import TelegramClient, events
from telethon.tl.types import PeerChannel
from dotenv import load_dotenv
import asyncio
import json
import os
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# .env 파일에서 환경 변수 로드
load_dotenv()

# API 인증 정보
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
phone_number = os.getenv('PHONE_NUMBER')

# 모니터링할 채널 ID 목록 (channels.json 파일에서 로드)
def load_channel_ids():
    try:
        with open('channels.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('channel_ids', [])
    except FileNotFoundError:
        logger.error("channels.json 파일을 찾을 수 없습니다.")
        return []
    except json.JSONDecodeError:
        logger.error("channels.json 파일 형식이 잘못되었습니다.")
        return []

async def monitor_channels():
    # 클라이언트 초기화
    client = TelegramClient('monitor_session', api_id, api_hash)
    
    try:
        await client.start(phone_number)
        logger.info("텔레그램 클라이언트에 연결되었습니다.")

        channel_ids = load_channel_ids()
        if not channel_ids:
            logger.error("모니터링할 채널이 없습니다.")
            return

        # 각 채널 구독
        for channel_id in channel_ids:
            try:
                channel = await client.get_entity(PeerChannel(channel_id))
                logger.info(f"채널 '{channel.title}' ({channel_id}) 모니터링 시작")
            except Exception as e:
                logger.error(f"채널 ID {channel_id} 연결 실패: {str(e)}")
                continue

        @client.on(events.NewMessage(chats=channel_ids))
        async def handler(event):
            try:
                # 메시지 발신 채널 정보 가져오기
                channel = await event.get_chat()
                
                # 메시지 정보 구성
                message_info = {
                    'channel_id': channel.id,
                    'channel_name': channel.title,
                    'message_id': event.message.id,
                    'message': event.message.text,
                    'timestamp': datetime.now().isoformat()
                }
                
                # 메시지 처리 (예: 콘솔에 출력, 파일에 저장, DB에 저장 등)
                logger.info(f"새 메시지 감지: {message_info}")
                
                # 여기에 메시지 저장 로직 추가
                save_message(message_info)
                
            except Exception as e:
                logger.error(f"메시지 처리 중 오류 발생: {str(e)}")

        # 클라이언트 실행 유지
        await client.run_until_disconnected()
        
    except Exception as e:
        logger.error(f"모니터링 중 오류 발생: {str(e)}")
    finally:
        await client.disconnect()

def save_message(message_info):
    """
    메시지를 파일이나 데이터베이스에 저장하는 함수
    여기서는 간단히 JSON 파일에 저장하는 예시를 보여줍니다.
    """
    filename = f"messages_{datetime.now().strftime('%Y%m%d')}.json"
    
    try:
        # 기존 메시지 로드
        messages = []
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                messages = json.load(f)
        
        # 새 메시지 추가
        messages.append(message_info)
        
        # 파일에 저장
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        logger.error(f"메시지 저장 중 오류 발생: {str(e)}")

if __name__ == "__main__":
    # 이벤트 루프 실행
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(monitor_channels())
    except KeyboardInterrupt:
        logger.info("모니터링이 중단되었습니다.")
    finally:
        loop.close() 