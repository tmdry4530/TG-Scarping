# CLOVA OCR 테스트 안내

이 디렉토리에는 네이버 클라우드의 CLOVA OCR API를 테스트하기 위한 스크립트가 포함되어 있습니다.

## 사전 준비

1. 네이버 클라우드 계정 생성 및 CLOVA OCR 서비스 활성화
2. API Gateway 및 Secret Key 발급
3. 필요한 Python 패키지 설치

```bash
pip install opencv-python requests python-dotenv
```

## 환경 설정

`.env` 파일에 다음 내용을 추가하세요:

```
CLOVA_OCR_API_URL=https://your-api-gateway-url.apigw.ntruss.com/custom/v1/your-key/your-id
CLOVA_OCR_SECRET_KEY=your-secret-key
```

## 테스트 방법

1. 테스트할 이미지를 `test_images` 디렉토리에 넣으세요.
2. 다음 명령어로 테스트를 실행하세요:

```bash
python test_clova_ocr.py test_images/your_image.jpg
```

## 결과 확인

테스트 결과는 다음 위치에 저장됩니다:

- `test_images/debug/{이미지파일명}_resized.png`: 전처리된 이미지
- `test_images/debug/{이미지파일명}_ocr_result.json`: OCR API 응답 원본 데이터
- `test_images/debug/{이미지파일명}_extracted_text.txt`: 추출된 텍스트 및 상세 정보

## 결과 해석

- `combined_text`: 전체 추출된 텍스트를 하나의 문자열로 결합한 결과
- `details`: 각 텍스트 블록의 상세 정보 (텍스트, 신뢰도, 위치)
