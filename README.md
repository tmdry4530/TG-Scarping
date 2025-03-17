# TG-Scraping

텔레그램 메시지를 스크래핑하고 카카오톡 오픈채팅방 링크를 자동으로 처리하는 봇입니다.

## 주요 기능

- 텔레그램 채팅에서 카카오톡 오픈채팅방 링크 자동 감지
- 감지된 링크를 특정 텔레그램 그룹에 전달
- 웹 브라우저 자동화를 통한 카카오톡 링크 처리
- 맥OS, 윈도우 크로스 플랫폼 지원

## 주요 파일

- `tg.py`: 윈도우 환경용 메인 스크립트
- `tg_mac.py`: 맥OS 환경용 메인 스크립트
- `TG_kakao.py`: 카카오톡 링크 처리 관련 확장 기능
- `monitor_channels.py`: 채널 모니터링 기능
- `create_session.py`: 텔레그램 세션 생성 유틸리티

## 설치 방법

1. 저장소 클론

   ```
   git clone https://github.com/tmdry4530/TG-Scarping.git
   ```

2. 의존성 설치

   ```
   pip install -r requirements.txt
   ```

3. `.env` 파일 설정 (다음 형식으로 생성)
   ```
   API_ID=your_telegram_api_id
   API_HASH=your_telegram_api_hash
   BOT_TOKEN=your_bot_token
   TARGET_GROUP=target_group_id
   EXCLUDED_GROUP_IDS=id1,id2
   EXCLUDE_KEYWORDS=keyword1,keyword2
   ```

## 사용 방법

1. 세션 생성

   ```
   python create_session.py
   ```

2. 봇 실행 (운영체제에 맞는 스크립트 선택)
   ```
   python tg.py    # 윈도우용
   python tg_mac.py    # 맥OS용
   ```
