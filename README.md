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
- `setup_coordinates.py`: 맥OS용 클릭 좌표 설정 도구
- `.env.sample`: 환경 설정 파일 샘플

## 설치 방법

1. 저장소 클론

   ```
   git clone https://github.com/tmdry4530/TG-Scarping.git
   ```

2. 의존성 설치

   ```
   pip install -r requirements.txt
   ```

3. `.env` 파일 설정
   ```
   # .env.sample 파일을 .env로 복사하고 수정
   cp .env.sample .env
   # 파일을 열어 실제 값으로 수정
   ```

## 초기 설정

1. 텔레그램 세션 생성

   ```
   python create_session.py
   ```

2. 맥OS에서 클릭 좌표 설정 (맥OS 사용자만)
   ```
   python setup_coordinates.py
   ```
   화면의 지시에 따라 카카오톡 오픈채팅 링크를 열고 필요한 버튼 위치에 마우스를 올려놓고 Enter를 눌러 좌표를 설정합니다.

## 사용 방법

1. 봇 실행 (운영체제에 맞는 스크립트 선택)

   ```
   python tg.py    # 윈도우용
   python tg_mac.py    # 맥OS용
   ```

2. 텔레그램 채팅에서 카카오톡 오픈채팅 링크가 감지되면 봇이 자동으로 처리합니다.

## 문제 해결

- **맥OS에서 클릭이 제대로 동작하지 않는 경우**: `setup_coordinates.py`를 실행하여 좌표를 다시 설정합니다.
- **ChromeDriver 오류**: 크롬 브라우저가 최신 버전으로 업데이트되어 있는지 확인합니다.
- **텔레그램 API 오류**: `.env` 파일의 API 키와 토큰이 올바르게 설정되어 있는지 확인합니다.
