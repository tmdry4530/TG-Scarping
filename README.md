# 텔레그램 카카오 링크 자동 참여 봇

텔레그램에서 오픈카카오톡 초대 링크를 자동으로 감지하고 참여하는 봇입니다. CLOVA OCR을 사용해 이미지에서 비밀번호를 추출할 수 있습니다.

## 주요 기능

- 텔레그램 그룹에서 오픈카카오톡 링크 감지
- 자동으로 링크에 접속 및 참여
- 이미지에서 OCR을 통한 비밀번호 추출
- 중복 메시지 필터링
- 메모리 최적화 및 리소스 관리

## 설치 방법

1. 저장소 클론:

   ```bash
   git clone https://github.com/yourusername/tg_coffee_bot.git
   cd tg_coffee_bot
   ```

2. 필요한 패키지 설치:

   ```bash
   pip install -r requirements.txt
   ```

3. 환경 변수 설정:
   `.env.example` 파일을 `.env`로 복사하고 필요한 값들을 설정하세요.

   ```bash
   cp .env.example .env
   ```

4. Chrome 드라이버 설치:
   Chrome 브라우저와 같은 버전의 Chrome 드라이버를 설치하세요.

## 환경 변수 설정

`.env` 파일에 다음 값들을 설정해야 합니다:

```
# 텔레그램 API 정보
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
TARGET_GROUP=your_target_group_id

# CLOVA OCR 설정
CLOVA_OCR_API_URL=your_clova_ocr_api_url
CLOVA_OCR_SECRET_KEY=your_clova_ocr_secret_key

# 기타 설정
DEBUG_MODE=False
ADMIN_CHAT_ID=your_admin_chat_id
```

## 사용 방법

봇 실행:

```bash
python tg.py
```

## 명령어

- `/ping` - 봇 상태 확인
- `/status` - 상태 정보 표시
- `/debug` - 자가 진단 실행
- `/shutdown` - 봇 종료 (관리자만 가능)

## 주의사항

- 텔레그램 API와 CLOVA OCR API 사용을 위한 인증 정보가 필요합니다.
- Chrome 브라우저가 설치되어 있어야 합니다.
- 자동화된 작업이 서비스 약관에 위배될 수 있으니 사용에 주의하세요.

## 라이선스

MIT License
